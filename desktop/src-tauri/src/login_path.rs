//! The PATH a terminal would have. Opened from Finder or the Dock, the app
//! inherits launchd's bare `/usr/bin:/bin:/usr/sbin:/sbin`, so a CLI the user
//! installed with Homebrew (`/opt/homebrew/bin/claude`) or npm is invisible to
//! `find_bin` and every agent reads as not installed. The login shell is the
//! only thing that knows the real PATH, so ask it once at startup.

use std::io::Read;
use std::os::fd::AsRawFd;
use std::os::unix::process::CommandExt;
use std::path::Path;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

const START: &str = "_NURB_PATH_START_";
const END: &str = "_NURB_PATH_END_";

/// Long enough for a heavy oh-my-zsh or nvm setup, short enough that a
/// broken shell config only costs a slow launch rather than a hung one.
const TIMEOUT: Duration = Duration::from_secs(3);

/// Replaces this process's PATH with the login shell's, and keeps the
/// inherited one when the shell fails, hangs or prints nothing usable. Must
/// run before any other thread starts, because set_var is not thread-safe.
pub fn adopt() {
    let shell = std::env::var_os("SHELL").unwrap_or_else(|| "/bin/zsh".into());
    if let Some(path) = read(Path::new(&shell), TIMEOUT) {
        std::env::set_var("PATH", path);
    }
}

/// Runs `shell` as both a login shell (`.zprofile`, where Homebrew's
/// shellenv lives) and an interactive one (`.zshrc`, where nvm and friends
/// live), and returns the PATH it ends up with.
fn read(shell: &Path, timeout: Duration) -> Option<String> {
    let script = format!("printf '%s%s%s' '{START}' \"$PATH\" '{END}'");
    let mut child = Command::new(shell)
        .args(["-l", "-i", "-c", &script])
        // oh-my-zsh's update prompt would otherwise sit waiting for an answer.
        .env("DISABLE_AUTO_UPDATE", "true")
        .current_dir(std::env::var_os("HOME").unwrap_or_else(|| "/".into()))
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .process_group(0)
        .spawn()
        .ok()?;
    let mut stdout = child.stdout.take()?;
    let path = read_until_end(&mut stdout, Instant::now() + timeout);
    // Takes the shell and anything its config left running (a prompt's git
    // daemon, say) with it. Waiting for EOF instead would block on any of
    // those still holding the pipe.
    unsafe {
        libc::killpg(child.id() as i32, libc::SIGKILL);
    }
    let _ = child.wait();
    path
}

/// Reads until the END marker or the deadline, polling so a shell that never
/// answers cannot block past it.
fn read_until_end(stdout: &mut std::process::ChildStdout, deadline: Instant) -> Option<String> {
    let mut output = Vec::new();
    let mut chunk = [0u8; 4096];
    loop {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            return None;
        }
        let mut fd = libc::pollfd {
            fd: stdout.as_raw_fd(),
            events: libc::POLLIN,
            revents: 0,
        };
        let millis = remaining.as_millis().clamp(1, i32::MAX as u128) as i32;
        match unsafe { libc::poll(&mut fd, 1, millis) } {
            0 => return None,
            n if n < 0 => {
                if std::io::Error::last_os_error().kind() == std::io::ErrorKind::Interrupted {
                    continue;
                }
                return None;
            }
            _ => {}
        }
        // Readable (or hung up), so this read returns at once; 0 is EOF.
        let n = stdout.read(&mut chunk).ok().filter(|n| *n > 0)?;
        output.extend_from_slice(&chunk[..n]);
        if let Some(path) = between_markers(&String::from_utf8_lossy(&output)) {
            return Some(path);
        }
    }
}

/// The PATH between the markers. Anything an interactive shell prints first
/// (a motd, a prompt's escape codes) lands before START and is ignored.
fn between_markers(output: &str) -> Option<String> {
    let after = &output[output.rfind(START)? + START.len()..];
    let path = &after[..after.find(END)?];
    (!path.is_empty()).then(|| path.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::os::unix::fs::PermissionsExt;

    /// A stand-in for zsh: runs `body`, then hands the `-c` script (its
    /// fourth argument) to /bin/sh with a known PATH.
    fn fake_shell(name: &str, body: &str) -> std::path::PathBuf {
        let dir = std::env::temp_dir().join(format!("nurb-login-path-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let shell = dir.join(name);
        std::fs::write(
            &shell,
            format!(
                "#!/bin/sh\n{body}\nPATH=/opt/homebrew/bin:/usr/bin:/bin exec /bin/sh -c \"$4\"\n"
            ),
        )
        .unwrap();
        std::fs::set_permissions(&shell, std::fs::Permissions::from_mode(0o755)).unwrap();
        shell
    }

    #[test]
    fn reads_the_path_past_whatever_the_shell_prints_first() {
        let shell = fake_shell("chatty", "printf 'Last login: today\\n\\033[1m> \\033[0m'");
        assert_eq!(
            read(&shell, Duration::from_secs(5)).as_deref(),
            Some("/opt/homebrew/bin:/usr/bin:/bin")
        );
    }

    /// A prompt daemon that inherits stdout keeps the pipe open after the
    /// shell exits, so waiting for EOF would always run into the timeout.
    #[test]
    fn does_not_wait_on_a_background_process_holding_the_pipe() {
        let shell = fake_shell("daemon", "sleep 30 &");
        let started = Instant::now();
        assert!(read(&shell, Duration::from_secs(10)).is_some());
        assert!(started.elapsed() < Duration::from_secs(5));
    }

    #[test]
    fn a_hung_shell_gives_up_at_the_timeout() {
        let shell = fake_shell("hung", "sleep 30");
        let started = Instant::now();
        assert_eq!(read(&shell, Duration::from_millis(300)), None);
        assert!(started.elapsed() < Duration::from_secs(2));
    }

    #[test]
    fn a_missing_shell_or_no_output_keeps_the_inherited_path() {
        assert_eq!(
            read(Path::new("/nonexistent/zsh"), Duration::from_secs(1)),
            None
        );
        assert_eq!(
            read(&fake_shell("silent", "exit 1"), Duration::from_secs(5)),
            None
        );
        assert_eq!(between_markers(&format!("{START}{END}")), None);
        assert_eq!(between_markers(&format!("{START}/usr/bin")), None);
    }
}
