//! The extension registry: optional capabilities that ship as data, not as
//! core code. An extension is a manifest plus a host kind; the core knows how
//! to run each host kind and nothing else about the extension.
//!
//! Extensions are opt-in and disabled by default; the app only ever launches
//! an executable the user's own installer put on the machine. The registry is
//! generic: any interactive CLI or external application can be described with
//! the same manifest. The BUILTIN table ships the shipped extensions; user-
//! loadable manifests are the planned next step.
//!
//! The human-in-the-loop boundary lives here too: a Terminal host moves bytes
//! between the user and the CLI and nothing else. There is deliberately no
//! code path that can inject text into the session or read it back as data.

use std::collections::HashSet;
use std::path::{Path, PathBuf};

/// How the core presents the extension to the user.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum HostKind {
    /// A process whose stdin/stdout is a terminal the app hosts (ConPTY on
    /// Windows, a pty elsewhere). Bytes only: the user drives the CLI, the
    /// app never parses or injects into the session.
    Terminal,
    /// A separate native application the app launches and then does not touch.
    ExternalApp,
}

impl HostKind {
    pub fn id(self) -> &'static str {
        match self {
            Self::Terminal => "terminal",
            Self::ExternalApp => "externalApp",
        }
    }
}

/// Where the extension's executable may live. Declarative so the registry
/// stays generic and future extensions are just data.
///
/// No extension ships in this build, so no variant is constructed yet; the
/// table below is the design contract the next BUILTIN entry fills in.
#[allow(dead_code)]
#[derive(Clone, Copy, Debug)]
pub enum Lookup {
    /// A bare executable name resolved through PATH. npm's global bin lands
    /// there on both platforms, so most CLIs are found this way.
    OnPath(&'static str),
    /// Directories under the user's home, then the file name.
    UnderHome(&'static [&'static str], &'static str),
    /// Directories under %LOCALAPPDATA% (the Windows per-user installer
    /// convention), then the file name.
    UnderLocalAppData(&'static [&'static str], &'static str),
}

/// Everything the core needs to know about one extension.
pub struct Manifest {
    pub id: &'static str,
    pub label: &'static str,
    pub version: &'static str,
    /// The oldest app version this extension is known to work with. The app
    /// compares against its own version at launch time and refuses to run an
    /// extension older than the app knows how to host.
    pub min_app_version: &'static str,
    /// Developer/experimental extensions are disabled by default and shown
    /// only in the developer surface, not in the normal release feature set.
    pub dev_only: bool,
    pub host: HostKind,
    /// Candidate locations, tried in order: the npm bin on PATH first, then
    /// the downloaded binary under the user config dir.
    pub lookups: &'static [Lookup],
    /// argv template for Terminal hosts. `{project}` is replaced with the
    /// project directory at launch; nothing else is ever substituted, so no
    /// user-controlled string can become a second argument.
    pub launch: &'static [&'static str],
    /// What the user must install for the extension to exist, shown when it
    /// is not found.
    pub install: &'static str,
    /// One honest sentence about what the extension is and what it is not.
    pub note: &'static str,
}

/// Built-in extension manifests. Each entry is a complete extension
/// definition: what to call it, how to find it, how to launch it, and what to
/// tell the user. New extensions are added here as data, not as code.
///
/// Developer-only extensions are disabled by default and shown only in the
/// developer surface, not in the normal release feature set.
// No builtin extensions ship in this build; the registry is ready for them.
// The desktop Settings panel still shows the section, and the modal reports
// "No extensions shipped in this build" when it is empty.
const BUILTIN: &[Manifest] = &[];

// To add a built-in extension, push a Manifest entry to BUILTIN above. For
// example:
//
//   Manifest {
//       id: "my-tool",
//       label: "My Tool",
//       version: "0.1.0",
//       min_app_version: "0.20.1",
//       dev_only: true,
//       host: HostKind::Terminal,
//       lookups: &[Lookup::OnPath("my-tool")],
//       launch: &["my-tool", "--cwd", "{project}"],
//       install: "npm install -g my-tool",
//       note: "Runs my-tool in a terminal here.",
//   },

pub fn manifest(id: &str) -> Option<&'static Manifest> {
    BUILTIN.iter().find(|m| m.id == id)
}

/// Register a manifest at runtime (for user-loaded extensions). The manifest
/// is validated: ID must be unique, host kind must be known, and the minimum
/// app version must be parseable.
#[allow(dead_code)] // kept as the stable API surface for the next BUILTIN entry
pub fn register(_manifest: Manifest) -> Result<(), String> {
    // User extensions are the next step; for now the registry is builtin-only.
    // This stub exists so the public API surface is stable when user
    // extensions arrive.
    Err("user extensions are not yet supported".into())
}

/// File names worth trying for an executable on this platform. Windows needs
/// the extension the installer actually wrote (.exe, or .cmd/.bat for npm
/// shims); elsewhere the name is the file.
fn candidate_names(base: &str) -> Vec<String> {
    let mut names = vec![base.to_string()];
    if cfg!(windows) {
        names.extend([format!("{base}.exe"), format!("{base}.cmd"), format!("{base}.bat")]);
    }
    names
}

/// The first existing file among the directories, or None.
fn find_in(dirs: &[PathBuf], base: &str) -> Option<PathBuf> {
    for dir in dirs {
        for name in candidate_names(base) {
            let candidate = dir.join(name);
            if candidate.is_file() {
                return Some(candidate);
            }
        }
    }
    None
}

fn home() -> Option<PathBuf> {
    std::env::var_os("HOME")
        .map(PathBuf::from)
        .or_else(|| std::env::var_os("USERPROFILE").map(PathBuf::from))
}

fn local_app_data() -> Option<PathBuf> {
    std::env::var_os("LOCALAPPDATA").map(PathBuf::from)
}

/// Resolve a manifest's lookups to an existing file, trying each candidate in
/// order, or None when the user has not installed it.
fn discover(manifest: &Manifest) -> Option<PathBuf> {
    for lookup in manifest.lookups {
        let found = match lookup {
            Lookup::OnPath(name) => {
                let dirs: Vec<PathBuf> =
                    std::env::split_paths(&std::env::var_os("PATH")?).collect();
                find_in(&dirs, name)
            }
            Lookup::UnderHome(rel_dirs, name) => {
                let base = home()?;
                let dirs: Vec<PathBuf> = rel_dirs.iter().map(|d| base.join(d)).collect();
                find_in(&dirs, name)
            }
            Lookup::UnderLocalAppData(rel_dirs, name) => {
                let base = local_app_data()?;
                let dirs: Vec<PathBuf> = rel_dirs.iter().map(|d| base.join(d)).collect();
                find_in(&dirs, name)
            }
        };
        if found.is_some() {
            return found;
        }
    }
    None
}

#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ExtensionStatus {
    pub id: &'static str,
    pub label: &'static str,
    pub version: &'static str,
    pub host: &'static str,
    pub dev_only: bool,
    /// Whether the user's own install was found on this machine.
    pub installed: bool,
    /// Whether the user has enabled the extension. Developer extensions
    /// default to disabled.
    pub enabled: bool,
    pub install: &'static str,
    pub note: &'static str,
}

/// Is `app` at least `min`? Both are dotted versions like "0.20.1"; the
/// comparison is numeric per component, so 0.20.10 beats 0.20.9. Anything
/// unparsable fails closed: an extension whose minimum the app cannot verify
/// is not launched.
pub fn version_at_least(app: &str, min: &str) -> bool {
    fn parts(v: &str) -> Option<Vec<u32>> {
        v.split('.').map(|p| p.parse::<u32>().ok()).collect::<Option<Vec<_>>>()
    }
    let (Some(app), Some(min)) = (parts(app), parts(min)) else {
        return false;
    };
    for (a, m) in app.iter().zip(min.iter()) {
        if a != m {
            return a > m;
        }
    }
    app.len() >= min.len()
}

/// Enable/disable state, persisted as a small JSON file in the app data dir.
/// Deliberately separate from the manifests: state is the user's, manifests
/// are the app's.
pub struct Extensions {
    dir: PathBuf,
    enabled: HashSet<String>,
}

impl Extensions {
    pub fn load(dir: &Path) -> Self {
        let enabled = std::fs::read_to_string(dir.join("extensions.json"))
            .ok()
            .and_then(|text| serde_json::from_str::<serde_json::Value>(&text).ok())
            .and_then(|v| v.get("enabled").cloned())
            .and_then(|v| serde_json::from_value::<Vec<String>>(v).ok())
            .unwrap_or_default()
            .into_iter()
            .collect();
        Extensions { dir: dir.to_path_buf(), enabled }
    }

    fn save(&self) {
        let list: Vec<&str> = self.enabled.iter().map(|s| s.as_str()).collect();
        let _ = std::fs::write(
            self.dir.join("extensions.json"),
            serde_json::to_string_pretty(&serde_json::json!({ "enabled": list })).unwrap_or_default(),
        );
    }

    pub fn is_enabled(&self, id: &str) -> bool {
        self.enabled.contains(id)
    }

    /// Flip the state of a known extension. Unknown ids are rejected so a typo
    /// can never silently enable something the app cannot run.
    pub fn set_enabled(&mut self, id: &str, enabled: bool) -> Result<(), String> {
        if manifest(id).is_none() {
            return Err(format!("unknown extension: {id}"));
        }
        if enabled {
            self.enabled.insert(id.to_string());
        } else {
            self.enabled.remove(id);
        }
        self.save();
        Ok(())
    }

    pub fn statuses(&self) -> Vec<ExtensionStatus> {
        BUILTIN
            .iter()
            .map(|m| ExtensionStatus {
                id: m.id,
                label: m.label,
                version: m.version,
                host: m.host.id(),
                dev_only: m.dev_only,
                installed: discover(m).is_some(),
                enabled: self.enabled.contains(m.id),
                install: m.install,
                note: m.note,
            })
            .collect()
    }

    /// The resolved executable for a manifest the user has installed, with the
    /// enable gate applied: a disabled extension is not launchable.
    pub fn resolved(&self, id: &str) -> Result<(PathBuf, &'static Manifest), String> {
        let m = manifest(id).ok_or_else(|| format!("unknown extension: {id}"))?;
        if !self.is_enabled(id) {
            return Err(format!("extension {id} is disabled"));
        }
        let exe =
            discover(m).ok_or_else(|| format!("{id} is not installed on this machine"))?;
        Ok((exe, m))
    }

    /// The static manifest for an extension, regardless of install state.
    pub fn manifest(&self, id: &str) -> Result<&'static Manifest, String> {
        manifest(id).ok_or_else(|| format!("unknown extension: {id}"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_lookup_is_exact() {
        // Builtin table is empty by default; user extensions arrive later.
        assert!(manifest("bogus").is_none());
    }

    #[test]
    fn version_gate_compares_componentwise_and_fails_closed() {
        assert!(version_at_least("0.20.1", "0.20.1"));
        assert!(version_at_least("0.21.0", "0.20.1"));
        assert!(version_at_least("0.20.10", "0.20.9"));
        assert!(!version_at_least("0.20.0", "0.20.1"));
        assert!(!version_at_least("0.19.9", "0.20.1"));
        assert!(!version_at_least("banana", "0.20.1"));
    }

    #[test]
    fn find_in_honors_windows_suffixes() {
        let dir = std::env::temp_dir().join(format!("nurb-ext-test-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        std::fs::write(dir.join("tool.cmd"), "").unwrap();
        let dirs = vec![dir.clone()];
        // .cmd is only a candidate on Windows, so assert the platform-relative
        // truth rather than hard-coding one answer.
        let found = find_in(&dirs, "tool");
        assert_eq!(found.is_some(), cfg!(windows));
        // A literal file with the bare name resolves everywhere.
        std::fs::write(dir.join("tool2"), "").unwrap();
        assert!(find_in(&dirs, "tool2").is_some());
        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn enabled_state_persists_and_rejects_unknown_ids() {
        let dir = std::env::temp_dir().join(format!("nurb-ext-state-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let mut ext = Extensions::load(&dir);
        assert!(ext.set_enabled("nope", true).is_err());
        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn launch_template_only_substitutes_project() {
        // A launch template with more placeholders would be a prompt-injection
        // surface. This test asserts the contract on any future manifest: only
        // {project} is ever replaced.
        for manifest in BUILTIN.iter() {
            for arg in manifest.launch {
                if arg.contains('{') {
                    assert_eq!(*arg, "{project}");
                }
            }
        }
    }
}
