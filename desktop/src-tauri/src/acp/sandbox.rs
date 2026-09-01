//! The OS sandbox every agent adapter runs under. Enforcement used to live
//! in policy.rs as a shell-command parser deciding which permission requests
//! to auto-allow, and it lost by construction: bash's lexer is the spec, any
//! approximation misses shapes, and every miss was a dialog. Now the adapter
//! process (and so every command the agent runs) is spawned under a Seatbelt
//! profile: read anything, network allowed, write only where the app says.
//! Where the kernel is the guard, dialogs are gone: a forbidden write fails
//! in the agent's own transcript instead of interrupting the user.
//!
//! No entry in the profile is user-managed. Every writable root is computed
//! at spawn time from facts the app already owns: the project the user
//! opened, the app's own data directory (or the dev checkout), the per-user
//! temp and cache trees macOS assigns, and the state directories of the
//! agents the app ships. If a future change wants a user-typed path or a
//! setting here, it is the wrong change.
//!
//! Seatbelt is macOS-only. On Windows the adapter runs unconfined: there is
//! no OS primitive with sandbox-exec's shape (a restricted token or
//! AppContainer would break node, npm, and the venv wholesale). Nothing here
//! substitutes for that, so the app asks instead: CONFINED is false, and
//! policy.rs sends every request this profile would have constrained to a
//! dialog until the user says otherwise for that project. That is not the
//! same as running the agent CLI in a terminal, because that CLI prompts and
//! this app answers for it, so suppressing the prompt without the kernel
//! behind it is the one combination worse than either alone. Confinement and
//! consent are one decision, which is why the flag ships beside `wrap` rather
//! than being restated elsewhere: a platform that gains real confinement
//! flips CONFINED and the dialogs go away on their own.

#[cfg(target_os = "macos")]
use std::path::{Path, PathBuf};
#[cfg(not(target_os = "macos"))]
use std::path::Path;

/// Whether `wrap` actually confines the adapter. approvals.rs reads it to
/// pick the default for a project nobody has answered for yet: where the
/// kernel is the guard the app can answer permission requests itself, and
/// where it is not it has to ask. Set by the same cfg that selects `wrap`,
/// and asserted against what `wrap` observably does by the test below, so a
/// new platform cannot end up with an identity `wrap` and a stale true here.
#[cfg(target_os = "macos")]
pub(super) const CONFINED: bool = true;

#[cfg(not(target_os = "macos"))]
pub(super) const CONFINED: bool = false;

/// Wrap an adapter invocation in `sandbox-exec`. sandbox-exec applies the
/// profile and execs the target in place, so the child pid, process group,
/// and kill semantics the caller relies on are unchanged. Outside macOS this
/// is the identity function; see the module note.
#[cfg(target_os = "macos")]
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

#[cfg(not(target_os = "macos"))]
pub(super) fn wrap(
    program: String,
    args: Vec<String>,
    _project: &Path,
    _engine_root: &Path,
) -> (String, Vec<String>) {
    (program, args)
}

/// The Seatbelt profile. Later rules win, so: allow everything, deny all
/// writes, then re-allow the app-derived writable roots.
#[cfg(target_os = "macos")]
fn profile(project: &Path, engine_root: &Path) -> String {
    let mut rules = String::new();
    for root in writable_roots(project, engine_root) {
        rules.push_str(&format!("  (subpath {})\n", quoted(&root)));
    }
    if let Some(home) = home() {
        // The agents' own state (`~/.claude` and the `~/.claude.json` family,
        // `~/.codex`, `~/.gemini`, `~/.cursor`, `~/.grok`): one prefix rule per agent
        // home, so session files, config, and their temp-file variants are
        // all covered without enumerating filenames.
        for dot in [".claude", ".codex", ".gemini", ".cursor", ".grok"] {
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
#[cfg(target_os = "macos")]
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

#[cfg(target_os = "macos")]
fn home() -> Option<PathBuf> {
    crate::env::home_dir()
}

/// A Seatbelt string literal: double-quoted, with quotes and backslashes
/// escaped ("Banana Holder" is a normal project name; quotes would be
/// pathological but must not break out of the string).
#[cfg(target_os = "macos")]
fn quoted(path: &Path) -> String {
    let escaped = path
        .display()
        .to_string()
        .replace('\\', "\\\\")
        .replace('"', "\\\"");
    format!("\"{escaped}\"")
}

/// A path made safe for use inside a Seatbelt regex literal.
#[cfg(target_os = "macos")]
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

/// Kept separate from the Seatbelt tests below, which only run on macOS,
/// because the drift this catches happens on the platforms those never see.
#[cfg(test)]
mod confinement {
    use super::*;

    #[test]
    fn the_constant_tracks_what_wrap_actually_does() {
        // The bug this file shipped once: `wrap` became the identity function
        // on a new platform while everything downstream still believed the
        // kernel was the guard. Derive the claim from the behavior so the two
        // cannot separate again.
        let root = std::env::temp_dir();
        let (program, args) = wrap("agent".into(), vec!["--acp".into()], &root, &root);
        let rewrote = program != "agent" || args != ["--acp"];
        assert_eq!(CONFINED, rewrote);
    }
}

#[cfg(all(test, target_os = "macos"))]
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
        // Agent state under each agent home writes fine (created and removed).
        for dot in [".claude", ".codex", ".gemini", ".cursor", ".grok"] {
            let existed = home().map(|h| h.join(dot).exists()).unwrap_or(false);
            assert!(sh(
                &profile,
                &format!("mkdir -p \"$HOME/{dot}/nurb-sbx-test\" && rmdir \"$HOME/{dot}/nurb-sbx-test\"")
            ));
            // Do not leave dotdirs behind for agents this machine lacks.
            if !existed {
                if let Some(h) = home() {
                    std::fs::remove_dir(h.join(dot)).ok();
                }
            }
        }
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
