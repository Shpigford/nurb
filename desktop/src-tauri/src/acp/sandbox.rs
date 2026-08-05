//! The OS sandbox every agent adapter runs under. Enforcement used to live
//! in policy.rs as a shell-command parser deciding which permission requests
//! to auto-allow, and it lost by construction: bash's lexer is the spec, any
//! approximation misses shapes, and every miss was a dialog. Now the adapter
//! process (and so every command the agent runs) is spawned under a Seatbelt
//! profile: read anything, network allowed, write only where the app says.
//! Dialogs are gone because the kernel is the guard; a forbidden write fails
//! in the agent's own transcript instead of interrupting the user.
//!
//! No entry in the profile is user-managed. Every writable root is computed
//! at spawn time from facts the app already owns: the project the user
//! opened, the app's own data directory (or the dev checkout), the per-user
//! temp and cache trees macOS assigns, and the state directories of the
//! agents the app ships. If a future change wants a user-typed path or a
//! setting here, it is the wrong change.

use std::path::{Path, PathBuf};

/// Wrap an adapter invocation in `sandbox-exec`. sandbox-exec applies the
/// profile and execs the target in place, so the child pid, process group,
/// and kill semantics the caller relies on are unchanged.
pub(super) fn wrap(
    program: String,
    args: Vec<String>,
    project: &Path,
    engine_root: &Path,
) -> (String, Vec<String>) {
    let mut wrapped = vec!["-p".into(), profile(project, engine_root), program];
    wrapped.extend(args);
    ("/usr/bin/sandbox-exec".into(), wrapped)
}

/// The Seatbelt profile. Later rules win, so: allow everything, deny all
/// writes, then re-allow the app-derived writable roots.
fn profile(project: &Path, engine_root: &Path) -> String {
    let mut rules = String::new();
    for root in writable_roots(project, engine_root) {
        rules.push_str(&format!("  (subpath {})\n", quoted(&root)));
    }
    if let Some(home) = home() {
        // The agents' own state (`~/.claude` and the `~/.claude.json` family,
        // `~/.codex`): one prefix rule per agent home, so session files,
        // config, and their temp-file variants are all covered without
        // enumerating filenames.
        for dot in [".claude", ".codex"] {
            rules.push_str(&format!(
                "  (regex #\"^{}/\\{dot}\")\n",
                regex_escaped(&home.display().to_string())
            ));
        }
    }
    format!(
        "(version 1)\n\
         (allow default)\n\
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

/// Directory roots the adapter may write, symlink-resolved because Seatbelt
/// matches syscall paths after resolution (/tmp is really /private/tmp).
/// Roots that do not exist are skipped: a rule for a missing path is dead
/// weight, and everything here is created by macOS or the app before an
/// adapter ever spawns.
fn writable_roots(project: &Path, engine_root: &Path) -> Vec<PathBuf> {
    let mut roots = Vec::new();
    let mut push = |path: PathBuf| {
        if let Ok(real) = path.canonicalize() {
            if !roots.contains(&real) {
                roots.push(real);
            }
        }
    };
    // The project the user opened, and the engine's home: the provisioned
    // app-data dir on user machines, the repo checkout in dev builds (where
    // `uv run --project` and `npx -y` write build state).
    push(project.to_path_buf());
    push(engine_root.to_path_buf());
    // The per-user temp tree macOS hands the app (TMPDIR under
    // /var/folders/...) and its sibling cache tree; child shells inherit the
    // same confstr answers.
    let temp = std::env::temp_dir();
    if let Some(user_dir) = temp.parent() {
        push(user_dir.join("C"));
    }
    push(temp);
    if let Some(home) = home() {
        // Tool caches (uv resolves to ~/Library/Caches, npm to ~/.npm,
        // XDG-style tools to ~/.cache) and nurb's own config.
        push(home.join("Library/Caches"));
        push(home.join(".cache"));
        push(home.join(".npm"));
        push(home.join(".config/nurb"));
    }
    roots
}

fn home() -> Option<PathBuf> {
    std::env::var_os("HOME").map(PathBuf::from)
}

/// A Seatbelt string literal: double-quoted, with quotes and backslashes
/// escaped ("Banana Holder" is a normal project name; quotes would be
/// pathological but must not break out of the string).
fn quoted(path: &Path) -> String {
    let escaped = path
        .display()
        .to_string()
        .replace('\\', "\\\\")
        .replace('"', "\\\"");
    format!("\"{escaped}\"")
}

/// A path made safe for use inside a Seatbelt regex literal.
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
mod tests {
    use super::*;
    use std::process::Command;

    fn sh(profile: &str, script: &str) -> bool {
        Command::new("/usr/bin/sandbox-exec")
            .args(["-p", profile, "/bin/sh", "-c", script])
            .output()
            .expect("sandbox-exec runs")
            .status
            .success()
    }

    #[test]
    fn the_kernel_enforces_the_write_boundary() {
        // The test IS the security property: writes inside the project
        // succeed, writes beside it fail, reads work everywhere.
        let project = std::env::temp_dir().join(format!("nurb-sbx-{}", std::process::id()));
        let outside = std::env::temp_dir().join(format!("nurb-sbx-out-{}", std::process::id()));
        std::fs::create_dir_all(&project).unwrap();
        std::fs::create_dir_all(&outside).unwrap();
        // A profile whose only writable root is the project: temp trees are
        // excluded here on purpose, because the test's "outside" lives there.
        let profile = format!(
            "(version 1)\n(allow default)\n(deny file-write*)\n(allow file-write* (subpath {}) (literal \"/dev/null\"))\n",
            quoted(&project.canonicalize().unwrap())
        );
        assert!(sh(&profile, &format!("echo hi > '{}/inside.txt'", project.display())));
        assert!(!sh(&profile, &format!("echo hi > '{}/escape.txt'", outside.display())));
        assert!(sh(&profile, "cat /etc/hosts > /dev/null"));
        std::fs::remove_dir_all(&project).ok();
        std::fs::remove_dir_all(&outside).ok();
    }

    #[test]
    fn the_real_profile_admits_the_project_and_agent_state() {
        let project = std::env::temp_dir().join(format!("nurb-sbx-real-{}", std::process::id()));
        std::fs::create_dir_all(&project).unwrap();
        let profile = profile(&project, &project);
        // Inside the project: allowed. The user's own dotfiles: refused.
        assert!(sh(&profile, &format!("echo hi > '{}/part.py'", project.display())));
        assert!(!sh(&profile, "echo hacked >> \"$HOME/nurb-sbx-canary\" && rm \"$HOME/nurb-sbx-canary\""));
        // Agent state under ~/.claude writes fine (created and removed).
        assert!(sh(
            &profile,
            "mkdir -p \"$HOME/.claude/nurb-sbx-test\" && rmdir \"$HOME/.claude/nurb-sbx-test\""
        ));
        std::fs::remove_dir_all(&project).ok();
    }

    #[test]
    fn quoting_survives_hostile_paths() {
        let path = PathBuf::from("/Users/me/Documents/nurb/Banana Holder");
        assert_eq!(quoted(&path), "\"/Users/me/Documents/nurb/Banana Holder\"");
        let tricky = PathBuf::from("/Users/me/a\"b");
        assert_eq!(quoted(&tricky), "\"/Users/me/a\\\"b\"");
        assert_eq!(regex_escaped("/Users/j.p"), "/Users/j\\.p");
    }
}
