//! Kernel sandbox orchestration shared by every ACP adapter process.
//!
//! Both platforms enforce the same write boundary: read anything, keep network
//! access, and write only the open project, engine state, tool caches, agent
//! state, temp space, and nurb config. macOS renders those roots into Seatbelt;
//! Linux overlays them on a read-only mount namespace and separately denies
//! Unix sockets with seccomp.

use std::path::{Path, PathBuf};

#[cfg(any(target_os = "linux", test))]
mod linux;
#[cfg(target_os = "macos")]
mod macos;

#[cfg(target_os = "linux")]
pub(super) use linux::wrap;
#[cfg(target_os = "macos")]
pub(super) use macos::wrap;

/// One prefix per shipped agent home. Seatbelt uses all of them; Linux exposes
/// only the currently spawned agent through its HOME relayout.
pub(super) const AGENT_DOTS: [&str; 5] = [".claude", ".codex", ".gemini", ".cursor", ".grok"];

/// Writable roots shared by both renderers. Every returned path is resolved so
/// Seatbelt sees the syscall path and bwrap receives a real bind source.
pub(super) fn writable_roots(
    project: &Path,
    engine_root: &Path,
    agent_home: Option<&Path>,
    config: Option<&Path>,
) -> Vec<PathBuf> {
    let mut roots = Vec::new();
    let mut push = |path: PathBuf| {
        if let Ok(real) = path.canonicalize() {
            if !roots.contains(&real) {
                roots.push(real);
            }
        }
    };
    push(project.to_path_buf());
    push(engine_root.to_path_buf());
    if let Some(agent_home) = agent_home {
        push(agent_home.to_path_buf());
    }
    let temp = std::env::temp_dir();
    #[cfg(target_os = "macos")]
    if let Some(user_dir) = temp.parent() {
        push(user_dir.join("C"));
    }
    push(temp);
    #[cfg(target_os = "linux")]
    push(PathBuf::from("/tmp"));
    if let Some(home) = home() {
        #[cfg(target_os = "macos")]
        push(home.join("Library/Caches"));
        push(home.join(".cache"));
        push(home.join(".npm"));
    }
    if let Some(config) = config {
        push(config.to_path_buf());
    }
    roots
}

pub(super) fn ensure_nurb_config_dir() -> Option<PathBuf> {
    let path = match crate::agents::nurb_config_dir() {
        Ok(path) => path,
        Err(error) => {
            eprintln!("[acp:sandbox] {error}");
            return None;
        }
    };
    ensure_directory(path, "nurb config")
}

/// Return the writable custom state root and the CODEX_HOME value the child
/// must see. An invalid inherited override explicitly falls back to ~/.codex;
/// otherwise Codex would keep targeting an intentionally read-only path.
pub(super) fn agent_home_policy(
    agent_dot: &str,
    requested: Option<&Path>,
    project: &Path,
    engine_root: &Path,
    override_present: bool,
) -> Result<(Option<PathBuf>, Option<String>), String> {
    let safe = safe_agent_home(requested, project, engine_root)?;
    if agent_dot != ".codex" || !override_present {
        return Ok((safe, None));
    }
    let effective = safe
        .as_ref()
        .cloned()
        .or_else(|| home().map(|home| home.join(".codex")));
    let environment = effective.and_then(|path| path.to_str().map(str::to_string));
    Ok((safe, environment))
}

/// Resolve symlinks before granting a custom agent root. It may not be HOME,
/// an ancestor of HOME, or an ancestor that widens project/engine access.
fn safe_agent_home(
    path: Option<&Path>,
    project: &Path,
    engine_root: &Path,
) -> Result<Option<PathBuf>, String> {
    let Some(path) = path else {
        return Ok(None);
    };
    let candidate = match prospective_real_path(path) {
        Ok(path) => path,
        Err(error) => {
            eprintln!(
                "[acp:sandbox] ignoring unsafe CODEX_HOME {}: {error}",
                path.display()
            );
            return Ok(None);
        }
    };
    if let Some(home) = home() {
        if home.starts_with(&candidate) {
            eprintln!(
                "[acp:sandbox] ignoring unsafe CODEX_HOME {} because it would make protected data writable",
                path.display()
            );
            return Ok(None);
        }
    }
    for root in [project, engine_root] {
        if let Ok(root) = root.canonicalize() {
            if root != candidate && root.starts_with(&candidate) {
                return Err(format!(
                    "CODEX_HOME {} contains the open project or nurb engine. Choose a separate CODEX_HOME folder, then reopen the project.",
                    path.display()
                ));
            }
        }
    }
    std::fs::create_dir_all(&candidate).map_err(|error| {
        format!(
            "Could not create CODEX_HOME {}: {error}. Choose a writable CODEX_HOME folder, then reopen the project.",
            candidate.display()
        )
    })?;
    Ok(Some(candidate))
}

fn prospective_real_path(path: &Path) -> Result<PathBuf, String> {
    use std::path::Component;

    if !path.is_absolute() {
        return Err("the path is not absolute".into());
    }
    if path.to_str().is_none() {
        return Err("the path is not valid UTF-8".into());
    }
    if path
        .components()
        .any(|component| matches!(component, Component::ParentDir))
    {
        return Err("the path contains '..'".into());
    }
    let mut existing = path.to_path_buf();
    let mut suffix = Vec::new();
    while !existing.exists() {
        let Some(name) = existing.file_name() else {
            return Err("the path has no existing ancestor".into());
        };
        suffix.push(name.to_os_string());
        if !existing.pop() {
            return Err("the path has no existing ancestor".into());
        }
    }
    let mut real = existing
        .canonicalize()
        .map_err(|error| format!("its existing ancestor cannot be resolved: {error}"))?;
    for component in suffix.into_iter().rev() {
        real.push(component);
    }
    Ok(real)
}

fn ensure_directory(path: PathBuf, label: &str) -> Option<PathBuf> {
    if let Err(error) = std::fs::create_dir_all(&path) {
        eprintln!(
            "[acp:sandbox] could not create the {label} directory at {}: {error}",
            path.display()
        );
        return None;
    }
    Some(path)
}

pub(super) fn home() -> Option<PathBuf> {
    canonical_existing_dir(PathBuf::from(std::env::var_os("HOME")?))
}

pub(super) fn canonical_existing_dir(path: PathBuf) -> Option<PathBuf> {
    path.canonicalize().ok().filter(|path| path.is_dir())
}

#[cfg(test)]
#[path = "sandbox/common_tests.rs"]
mod common_tests;
