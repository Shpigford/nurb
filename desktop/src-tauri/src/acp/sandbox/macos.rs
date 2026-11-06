use std::path::Path;

use super::{agent_home_policy, ensure_nurb_config_dir, home, writable_roots, AGENT_DOTS};

pub(crate) struct SandboxGuard;

impl Drop for SandboxGuard {
    fn drop(&mut self) {}
}

/// sandbox-exec applies the profile and execs the target in place, preserving
/// the child pid, process group, and kill semantics the ACP caller relies on.
pub(crate) fn wrap(
    program: String,
    args: Vec<String>,
    project: &Path,
    engine_root: &Path,
    agent_dot: &str,
    agent_home: Option<&Path>,
) -> Result<(String, Vec<String>, bool, Option<SandboxGuard>), String> {
    let override_present = std::env::var_os("CODEX_HOME").is_some_and(|value| !value.is_empty());
    let (agent_home, codex_home) = agent_home_policy(
        agent_dot,
        agent_home,
        project,
        engine_root,
        override_present,
    )?;
    let mut wrapped = vec![
        "-p".into(),
        profile(project, engine_root, agent_home.as_deref()),
    ];
    if let Some(home) = codex_home {
        wrapped.extend(["/usr/bin/env".into(), format!("CODEX_HOME={home}")]);
    }
    wrapped.push(program);
    wrapped.extend(args);
    Ok(("/usr/bin/sandbox-exec".into(), wrapped, true, None))
}

/// Later Seatbelt rules win: allow normal reads and IP networking, deny Unix
/// sockets and writes, re-allow DNS plus the app-derived writable roots, then
/// shut the folders macOS guards with a permission prompt and re-open the
/// roots the agent works in.
fn profile(project: &Path, engine_root: &Path, agent_home: Option<&Path>) -> String {
    let agent_home = agent_home.map(Path::to_path_buf);
    let config = ensure_nurb_config_dir();
    let mut rules = String::new();
    let mut readable = String::new();
    for root in writable_roots(
        project,
        engine_root,
        agent_home.as_deref(),
        config.as_deref(),
    ) {
        rules.push_str(&format!("  (subpath {})\n", quoted(&root)));
        readable.push_str(&format!("  (subpath {})\n", quoted(&root)));
    }
    if let Some(bundle) = app_bundle() {
        readable.push_str(&format!("  (subpath {})\n", quoted(&bundle)));
    }
    let mut private = String::new();
    for folder in private_folders() {
        private.push_str(&format!("  (subpath {})\n", quoted(&folder)));
    }
    if let Some(home) = home() {
        for dot in AGENT_DOTS {
            rules.push_str(&format!(
                "  (regex #\"^{}/\\{dot}\")\n",
                regex_escaped(&home.display().to_string())
            ));
        }
    }
    format!(
        "(version 1)\n\
         (allow default)\n\
         (deny network-outbound (remote unix-socket))\n\
         (allow network-outbound (literal \"/private/var/run/mDNSResponder\"))\n\
         (deny file-write*)\n\
         (allow file-write*\n\
         \x20 (literal \"/dev/null\")\n\
         \x20 (literal \"/dev/tty\")\n\
         \x20 (literal \"/dev/dtracehelper\")\n\
         \x20 (regex #\"^/dev/ttys[0-9]\")\n\
         \x20 (subpath \"/private/tmp\")\n\
         {rules})\n\
         (deny file-read*\n\
         {private})\n\
         (allow file-read*\n\
         {readable})\n"
    )
}

/// The folders macOS asks the user about before any app reads them. An agent
/// left to look around (`ls ~/Documents`, a search across the home folder) set
/// off one prompt per folder in nurb's name. Its project and attachments come
/// from the app, so it never needs these, and a refused read lands in its own
/// transcript instead of a dialog.
fn private_folders() -> Vec<std::path::PathBuf> {
    let mut folders = vec![std::path::PathBuf::from("/Volumes")];
    if let Some(home) = home() {
        for name in ["Desktop", "Documents", "Downloads", "Library/CloudStorage", "Library/Mobile Documents"] {
            folders.push(home.join(name));
        }
    }
    folders
}

/// The .app the running binary lives in. Opened straight from the mounted DMG it
/// sits under /Volumes, and the adapters it bundles still have to be readable.
fn app_bundle() -> Option<std::path::PathBuf> {
    let exe = std::env::current_exe().ok()?.canonicalize().ok()?;
    exe.ancestors()
        .find(|dir| dir.extension().is_some_and(|ext| ext == "app"))
        .map(Path::to_path_buf)
}

fn quoted(path: &Path) -> String {
    let escaped = path
        .display()
        .to_string()
        .replace('\\', "\\\\")
        .replace('"', "\\\"");
    format!("\"{escaped}\"")
}

fn regex_escaped(path: &str) -> String {
    let mut out = String::new();
    for c in path.chars() {
        if "\\^$.|?*+()[]{}\"".contains(c) {
            out.push('\\');
        }
        out.push(c);
    }
    out
}

#[cfg(test)]
#[path = "macos_tests.rs"]
mod tests;
