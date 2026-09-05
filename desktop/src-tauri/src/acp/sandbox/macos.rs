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
/// sockets and writes, then re-allow DNS plus the app-derived writable roots.
fn profile(project: &Path, engine_root: &Path, agent_home: Option<&Path>) -> String {
    let agent_home = agent_home.map(Path::to_path_buf);
    let config = ensure_nurb_config_dir();
    let mut rules = String::new();
    for root in writable_roots(
        project,
        engine_root,
        agent_home.as_deref(),
        config.as_deref(),
    ) {
        rules.push_str(&format!("  (subpath {})\n", quoted(&root)));
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
         {rules})\n"
    )
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
