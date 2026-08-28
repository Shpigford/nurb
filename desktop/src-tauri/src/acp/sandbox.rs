//! The OS sandbox every agent adapter runs under. Enforcement used to live
//! in policy.rs as a shell-command parser deciding which permission requests
//! to auto-allow, and it lost by construction: bash's lexer is the spec, any
//! approximation misses shapes, and every miss was a dialog. Now the adapter
//! process (and so every command the agent runs) is spawned under a kernel
//! sandbox: read anything, network allowed, write only where the app says.
//! Dialogs are gone because the kernel is the guard; a forbidden write fails
//! in the agent's own transcript instead of interrupting the user.
//!
//! Two backends, one property. macOS states it as a Seatbelt profile handed
//! to `sandbox-exec`: allow all, deny writes, re-allow the roots. Linux states
//! the same shape as a bubblewrap mount namespace: bind the filesystem in
//! read-only, then bind the writable roots back over it. Neither is a policy
//! language the other can express exactly, so `writable_roots` is the shared
//! part and each backend renders it its own way.
//!
//! No entry is user-managed. Every writable root is computed at spawn time
//! from facts the app already owns: the project the user opened, the app's own
//! data directory (or the dev checkout), the per-user temp and cache trees,
//! and the state directories of the agents the app ships. If a future change
//! wants a user-typed path or a setting here, it is the wrong change.

use std::path::{Path, PathBuf};

/// The agents whose state directories stay writable. One name per agent home,
/// so config, sessions, and their temp-file variants are all covered without
/// enumerating filenames.
const AGENT_DOTS: [&str; 5] = [".claude", ".codex", ".gemini", ".cursor", ".grok"];

/// Wrap an adapter invocation in `sandbox-exec`. sandbox-exec applies the
/// profile and execs the target in place, so the child pid, process group,
/// and kill semantics the caller relies on are unchanged.
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

/// Wrap an adapter invocation in `bwrap`. Unlike sandbox-exec this forks
/// rather than execing in place, so two flags carry the semantics the caller
/// depends on: `--die-with-parent` ties the sandbox's life to the app's, and
/// the absence of `--new-session` keeps the child in the process group the
/// spawn established, which is what `killpg` in acp.rs reaps. `--new-session`
/// would harden against TIOCSTI injection, but adapters get pipes rather than
/// a tty, and losing the process group would leak adapter processes on quit.
///
/// bubblewrap is a hard dependency of the .deb for this reason. If it is
/// somehow missing, the adapter still runs: chat that refuses to start is a
/// dead end for the user, where an unsandboxed adapter is the behaviour every
/// agent CLI has on its own. The warning names what was lost.
#[cfg(target_os = "linux")]
pub(super) fn wrap(
    program: String,
    args: Vec<String>,
    project: &Path,
    engine_root: &Path,
) -> (String, Vec<String>) {
    let Some(bwrap) = which_bwrap() else {
        eprintln!(
            "[acp:sandbox] bubblewrap not found, so this agent runs unsandboxed \
             and may write outside {}. Install the bubblewrap package.",
            project.display()
        );
        return (program, args);
    };
    let mut wrapped = bwrap_args(project, engine_root);
    wrapped.push(program);
    wrapped.extend(args);
    (bwrap.to_string_lossy().into_owned(), wrapped)
}

/// The bwrap invocation, without the command it wraps. Order is the policy:
/// the whole filesystem arrives read-only, then /dev and /proc are replaced
/// with fresh minimal instances, then each writable root is bound back over
/// the read-only view. Network is deliberately left shared.
#[cfg(target_os = "linux")]
fn bwrap_args(project: &Path, engine_root: &Path) -> Vec<String> {
    let mut args: Vec<String> = ["--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc"]
        .iter()
        .map(|s| (*s).to_string())
        .collect();
    // --bind-try, not --bind: the roots are enumerated a moment before bwrap
    // execs, and a plain --bind aborts the whole sandbox if any source has
    // gone by then. An agent's own temp file in $HOME is enough to lose that
    // race, and the adapter failing to start is far worse than one fewer
    // writable root. It cannot widen the boundary, only narrow it.
    for root in writable_roots(project, engine_root) {
        let path = root.to_string_lossy().into_owned();
        args.push("--bind-try".into());
        args.push(path.clone());
        args.push(path);
    }
    args.push("--die-with-parent".into());
    args
}

/// bubblewrap's absolute path. Distributions disagree (/usr/bin on Debian,
/// /usr/bin or /bin elsewhere), so the known locations are tried before PATH,
/// which a user profile controls.
#[cfg(target_os = "linux")]
fn which_bwrap() -> Option<PathBuf> {
    for candidate in ["/usr/bin/bwrap", "/bin/bwrap", "/usr/local/bin/bwrap"] {
        let path = PathBuf::from(candidate);
        if path.is_file() {
            return Some(path);
        }
    }
    let path = std::env::var_os("PATH")?;
    std::env::split_paths(&path)
        .map(|dir| dir.join("bwrap"))
        .find(|candidate| candidate.is_file())
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
/// matches syscall paths after resolution (/tmp is really /private/tmp) and
/// because a bwrap bind source has to be a real path. Roots that do not exist
/// are skipped: a Seatbelt rule for a missing path is dead weight, and a bwrap
/// bind of one is a hard error.
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
    let temp = std::env::temp_dir();
    // The per-user temp tree macOS hands the app (TMPDIR under
    // /var/folders/...) and its sibling cache tree; child shells inherit the
    // same confstr answers. Linux TMPDIR has no such sibling.
    #[cfg(target_os = "macos")]
    if let Some(user_dir) = temp.parent() {
        push(user_dir.join("C"));
    }
    push(temp);
    // A Linux TMPDIR may point elsewhere, but tools still reach for /tmp.
    #[cfg(target_os = "linux")]
    push(PathBuf::from("/tmp"));
    if let Some(home) = home() {
        // Tool caches (uv resolves to ~/Library/Caches on macOS and ~/.cache
        // on Linux, npm to ~/.npm) and nurb's own config.
        #[cfg(target_os = "macos")]
        push(home.join("Library/Caches"));
        push(home.join(".cache"));
        push(home.join(".npm"));
        push(home.join(".config/nurb"));
        // Seatbelt takes the agent state as a prefix regex in `profile`, so one
        // rule covers both ~/.claude and the ~/.claude.json family beside it. A
        // bind mount cannot glob, so the same prefixes are enumerated: the
        // directory itself, created when absent so a first run has somewhere to
        // write, plus every existing $HOME entry whose name starts with one.
        // Without the second half ~/.claude.json is read-only and the agent
        // cannot persist its own config. All five agents, not just the one
        // being spawned, because `wrap` is not told which it is and the macOS
        // rule is equally unconditional.
        #[cfg(target_os = "linux")]
        {
            for dot in AGENT_DOTS {
                let state = home.join(dot);
                let _ = std::fs::create_dir_all(&state);
                push(state);
            }
            if let Ok(entries) = std::fs::read_dir(&home) {
                for entry in entries.flatten() {
                    if let Some(name) = entry.file_name().to_str() {
                        if AGENT_DOTS.iter().any(|dot| name.starts_with(dot)) {
                            push(home.join(name));
                        }
                    }
                }
            }
        }
    }
    roots
}

fn home() -> Option<PathBuf> {
    std::env::var_os("HOME").map(PathBuf::from)
}

/// A Seatbelt string literal: double-quoted, with quotes and backslashes
/// escaped ("Banana Holder" is a normal project name; quotes would be
/// pathological but must not break out of the string). bwrap needs no
/// equivalent: its paths are argv entries, never parsed from a string.
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

#[cfg(test)]
mod tests {
    use super::*;
    #[allow(unused_imports)]
    use std::process::Command;

    #[cfg(target_os = "macos")]
    fn sh(profile: &str, script: &str) -> bool {
        Command::new("/usr/bin/sandbox-exec")
            .args(["-p", profile, "/bin/sh", "-c", script])
            .output()
            .expect("sandbox-exec runs")
            .status
            .success()
    }

    #[test]
    #[cfg(target_os = "macos")]
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
    #[cfg(target_os = "macos")]
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
    #[cfg(target_os = "macos")]
    fn quoting_survives_hostile_paths() {
        let path = PathBuf::from("/Users/me/Documents/nurb/Banana Holder");
        assert_eq!(quoted(&path), "\"/Users/me/Documents/nurb/Banana Holder\"");
        let tricky = PathBuf::from("/Users/me/a\"b");
        assert_eq!(quoted(&tricky), "\"/Users/me/a\\\"b\"");
        assert_eq!(regex_escaped("/Users/j.p"), "/Users/j\\.p");
    }

    /// Run a script through the exact bwrap invocation `wrap` would build, so
    /// the test exercises the shipped policy rather than a copy of it.
    #[cfg(target_os = "linux")]
    fn bwrapped(project: &Path, engine_root: &Path, script: &str) -> bool {
        let (program, args) = super::wrap(
            "/bin/sh".into(),
            vec!["-c".into(), script.into()],
            project,
            engine_root,
        );
        assert!(
            program.ends_with("bwrap"),
            "bubblewrap is required for this test"
        );
        Command::new(program)
            .args(args)
            .output()
            .expect("bwrap runs")
            .status
            .success()
    }

    #[test]
    #[cfg(target_os = "linux")]
    fn the_kernel_enforces_the_write_boundary() {
        // The test IS the security property, same as the Seatbelt one above:
        // writes inside the project succeed, writes outside the policy fail,
        // reads work everywhere, and the network the agent needs is still there.
        //
        // The escape target lives under $HOME rather than beside the project,
        // because the temp tree is a writable root on purpose (tools need it),
        // so a sibling in /tmp is allowed by design and would prove nothing.
        // $HOME is the real threat: the user's files outside what they opened.
        let project = std::env::temp_dir().join(format!("nurb-bwrap-{}", std::process::id()));
        std::fs::create_dir_all(&project).unwrap();
        let project = project.canonicalize().unwrap();
        let outside = home().unwrap().join(format!("nurb-bwrap-out-{}", std::process::id()));
        std::fs::create_dir_all(&outside).unwrap();

        assert!(bwrapped(&project, &project, &format!("echo hi > '{}/inside.txt'", project.display())));
        assert!(!bwrapped(&project, &project, &format!("echo hi > '{}/escape.txt'", outside.display())));
        assert!(!outside.join("escape.txt").exists());
        assert!(bwrapped(&project, &project, "cat /etc/hosts > /dev/null"));
        assert!(bwrapped(&project, &project, "echo discard > /dev/null"));
        // $HOME itself stays read-only; only the agent state dirs inside it move.
        assert!(!bwrapped(&project, &project, "echo hacked > \"$HOME/nurb-bwrap-canary\""));
        assert!(!home().unwrap().join("nurb-bwrap-canary").exists());

        std::fs::remove_dir_all(&project).ok();
        std::fs::remove_dir_all(&outside).ok();
    }

    #[test]
    #[cfg(target_os = "linux")]
    fn the_real_wrapping_admits_the_project_and_agent_state() {
        let project = std::env::temp_dir().join(format!("nurb-bwrap-real-{}", std::process::id()));
        std::fs::create_dir_all(&project).unwrap();
        let project = project.canonicalize().unwrap();
        assert!(bwrapped(&project, &project, &format!("echo hi > '{}/part.py'", project.display())));
        for dot in AGENT_DOTS {
            assert!(
                bwrapped(
                    &project,
                    &project,
                    &format!("mkdir -p \"$HOME/{dot}/nurb-bwrap-test\" && rmdir \"$HOME/{dot}/nurb-bwrap-test\"")
                ),
                "{dot} state should be writable"
            );
        }
        std::fs::remove_dir_all(&project).ok();
    }

    #[test]
    #[cfg(target_os = "linux")]
    fn agent_state_beside_the_directory_is_writable_too() {
        // Seatbelt's prefix regex covers ~/.claude.json as well as ~/.claude,
        // and Claude keeps real config in that file. A bind of the directory
        // alone leaves it read-only, which is silent until an agent cannot save.
        // A throwaway file sharing the .claude prefix, never the real
        // ~/.claude.json: this asserts the rule, and a test that appended to a
        // user's live agent config to prove a point would be a bad trade.
        let home = home().unwrap();
        let probe = home.join(format!(".claude-nurbprobe-{}", std::process::id()));
        std::fs::write(&probe, "probe").unwrap();
        let project = std::env::temp_dir().join(format!("nurb-bwrap-dot-{}", std::process::id()));
        std::fs::create_dir_all(&project).unwrap();
        let project = project.canonicalize().unwrap();

        assert!(
            bwrapped(
                &project,
                &project,
                &format!("printf x >> '{}'", probe.display())
            ),
            "agent state beside the directory should be writable, as under Seatbelt"
        );
        // And the rule really is the prefix, not a blanket $HOME: a neighbour
        // that does not belong to an agent stays read-only.
        let unrelated = home.join(format!("nurb-unrelated-{}", std::process::id()));
        std::fs::write(&unrelated, "probe").unwrap();
        assert!(!bwrapped(
            &project,
            &project,
            &format!("printf x >> '{}'", unrelated.display())
        ));

        std::fs::remove_dir_all(&project).ok();
        std::fs::remove_file(&probe).ok();
        std::fs::remove_file(&unrelated).ok();
    }

    #[test]
    #[cfg(target_os = "linux")]
    fn the_wrapping_keeps_the_process_group_and_dies_with_its_parent() {
        // acp.rs reaps adapters with killpg(child.id()), which only reaches
        // inside the sandbox while bwrap stays in the spawn's process group.
        // --new-session would break that; --die-with-parent stops an orphaned
        // adapter outliving the app.
        let project = std::env::temp_dir();
        let (_, args) = super::wrap("/bin/sh".into(), vec![], &project, &project);
        assert!(args.contains(&"--die-with-parent".to_string()));
        assert!(!args.contains(&"--new-session".to_string()));
    }

    #[test]
    #[cfg(target_os = "linux")]
    fn paths_with_spaces_need_no_quoting_because_they_are_argv() {
        let project = std::env::temp_dir().join(format!("nurb bwrap spaces {}", std::process::id()));
        std::fs::create_dir_all(&project).unwrap();
        let project = project.canonicalize().unwrap();
        let (_, args) = super::wrap("/bin/sh".into(), vec![], &project, &project);
        let want = project.to_string_lossy().into_owned();
        assert!(args.iter().filter(|a| **a == want).count() >= 2, "bound as its own argv entries");
        assert!(bwrapped(&project, &project, &format!("echo hi > '{}/x.txt'", project.display())));
        std::fs::remove_dir_all(&project).ok();
    }
}
