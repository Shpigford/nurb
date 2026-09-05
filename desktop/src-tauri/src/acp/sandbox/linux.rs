use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
#[cfg(target_os = "linux")]
use std::sync::OnceLock;
#[cfg(target_os = "linux")]
use std::{io::Write, os::fd::AsRawFd, os::fd::FromRawFd, os::fd::OwnedFd};

#[cfg(target_os = "linux")]
use super::{agent_home_policy, safe_agent_home};
use super::{canonical_existing_dir, ensure_nurb_config_dir, home, writable_roots};

#[cfg(target_os = "linux")]
pub(crate) struct SandboxGuard {
    _fd: OwnedFd,
}

/// Wrap an adapter invocation in `bwrap`. `--die-with-parent` ties the
/// sandbox's life to the app, while keeping the existing process group lets
/// acp.rs reap every descendant. If bubblewrap or its required kernel features
/// are unavailable, run explicitly unsandboxed and tell the caller.
#[cfg(target_os = "linux")]
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
    let bwrap = match usable_bwrap() {
        Ok(path) => path,
        Err(why) => {
            eprintln!(
                "[acp:sandbox] {why}, so this agent runs unsandboxed and may write outside {}. \
                 Install bubblewrap, enable unprivileged user namespaces, then reopen nurb.",
                project.display()
            );
            return Ok((program, args, false, None));
        }
    };
    let filter = match UnixSocketFilter::new() {
        Ok(filter) => filter,
        Err(error) => {
            eprintln!(
                "[acp:sandbox] {error}, so this agent runs unsandboxed and may write outside {}. \
                 Reopen nurb and try again.",
                project.display()
            );
            return Ok((program, args, false, None));
        }
    };
    let mut wrapped = vec!["--seccomp".into(), filter.fd().to_string()];
    wrapped.extend(bwrap_args(
        project,
        engine_root,
        agent_dot,
        agent_home.as_deref(),
    ));
    if let Some(home) = codex_home {
        wrapped.extend(["--setenv".into(), "CODEX_HOME".into(), home]);
    }
    wrapped.push(program);
    wrapped.extend(args);
    Ok((
        bwrap.to_string_lossy().into_owned(),
        wrapped,
        true,
        Some(SandboxGuard {
            _fd: filter.into_fd(),
        }),
    ))
}

/// The bwrap invocation, without the command it wraps. The whole filesystem
/// arrives read-only, HOME is re-laid, and writable roots return last. The PID
/// namespace prevents `/proc/<pid>/root` from escaping the mount namespace.
/// Network stays shared; the seccomp filter independently removes Unix sockets.
pub(super) fn bwrap_args(
    project: &Path,
    engine_root: &Path,
    agent_dot: &str,
    agent_home: Option<&Path>,
) -> Vec<String> {
    let agent_home = agent_home.map(Path::to_path_buf);
    let config = ensure_nurb_config_dir();
    let mut args: Vec<String> = [
        "--ro-bind",
        "/",
        "/",
        "--dev",
        "/dev",
        "--unshare-ipc",
        "--unshare-pid",
        "--proc",
        "/proc",
    ]
    .iter()
    .map(|s| (*s).to_string())
    .collect();
    args.extend(home_args(agent_dot));
    for root in writable_roots(
        project,
        engine_root,
        agent_home.as_deref(),
        config.as_deref(),
    ) {
        let Some(path) = root.to_str().map(str::to_string) else {
            eprintln!(
                "[acp:sandbox] refusing a non-UTF-8 writable root: {}",
                root.display()
            );
            continue;
        };
        // Sources may disappear between enumeration and exec. A missing bind
        // narrows the boundary; it must not abort the adapter startup.
        args.extend(["--bind-try".into(), path.clone(), path]);
    }
    args.extend(control_ipc_args());
    args.push("--die-with-parent".into());
    args
}

fn control_ipc_args() -> Vec<String> {
    let runtime = runtime_dir();
    control_ipc_args_for(runtime.as_deref())
}

pub(super) fn control_ipc_args_for(runtime: Option<&Path>) -> Vec<String> {
    let mut args = Vec::new();
    if let Some(path) = runtime.and_then(Path::to_str) {
        args.extend(["--tmpfs".into(), path.into()]);
    }
    for name in [
        "DBUS_SESSION_BUS_ADDRESS",
        "DBUS_SYSTEM_BUS_ADDRESS",
        "DOCKER_HOST",
        "CONTAINER_HOST",
    ] {
        args.extend(["--unsetenv".into(), name.into()]);
    }
    args
}

fn runtime_dir() -> Option<PathBuf> {
    std::env::var_os("XDG_RUNTIME_DIR")
        .map(PathBuf::from)
        .filter(|path| path.is_absolute())
        .and_then(canonical_existing_dir)
        .or_else(|| {
            let path = PathBuf::from(format!("/run/user/{}", unsafe { libc::geteuid() }));
            canonical_existing_dir(path)
        })
}

/// Bind HOME writable, then bind every existing non-agent entry back read-only.
/// Validation completes first: one unreadable or non-UTF-8 entry keeps all of
/// HOME read-only instead of leaving that entry exposed on a writable mount.
fn home_args(agent_dot: &str) -> Vec<String> {
    let Some(home) = home() else {
        return Vec::new();
    };
    match home_args_for(&home, agent_dot) {
        Ok(args) => args,
        Err(why) => {
            eprintln!("[acp:sandbox] {why}; keeping all of HOME read-only");
            Vec::new()
        }
    }
}

pub(super) fn home_args_for(home: &Path, agent_dot: &str) -> Result<Vec<String>, String> {
    let entries = std::fs::read_dir(home)
        .map_err(|error| format!("could not inspect HOME for sandboxing: {error}"))?;
    let mut names = Vec::new();
    for entry in entries {
        let entry = entry
            .map_err(|error| format!("could not inspect a HOME entry for sandboxing: {error}"))?;
        let file_type = entry.file_type().map_err(|error| {
            format!("could not inspect a HOME entry type for sandboxing: {error}")
        })?;
        if file_type.is_symlink() {
            return Err(format!(
                "HOME contains the symlink {}, which cannot be a bubblewrap mount destination",
                entry.path().display()
            ));
        }
        names.push(entry.file_name());
    }
    home_args_from_names(home, agent_dot, names)
}

pub(super) fn home_args_from_names(
    home: &Path,
    agent_dot: &str,
    names: Vec<std::ffi::OsString>,
) -> Result<Vec<String>, String> {
    let path = home
        .to_str()
        .ok_or_else(|| "HOME is not valid UTF-8".to_string())?
        .to_string();
    let mut args = vec!["--bind".into(), path.clone(), path];
    for name in names {
        let name = name
            .into_string()
            .map_err(|_| "HOME contains a filename that is not valid UTF-8".to_string())?;
        if name.starts_with(agent_dot) {
            continue;
        }
        let path = home
            .join(name)
            .to_str()
            .expect("validated HOME and entry are UTF-8")
            .to_string();
        args.extend(["--ro-bind-try".into(), path.clone(), path]);
    }
    Ok(args)
}

#[cfg(target_os = "linux")]
static BWRAP: OnceLock<Result<PathBuf, String>> = OnceLock::new();

#[cfg(target_os = "linux")]
fn usable_bwrap() -> Result<PathBuf, String> {
    BWRAP
        .get_or_init(|| {
            let path = which_bwrap().ok_or_else(|| "bubblewrap was not found".to_string())?;
            if probe_bwrap(&path) {
                Ok(path)
            } else {
                Err(format!(
                    "bubblewrap at {} cannot create the required namespaces and socket filter",
                    path.display()
                ))
            }
        })
        .clone()
}

#[cfg(target_os = "linux")]
pub(super) fn probe_bwrap(path: &Path) -> bool {
    let Ok(filter) = UnixSocketFilter::new() else {
        return false;
    };
    Command::new(path)
        .args(["--seccomp", &filter.fd().to_string()])
        .args([
            "--ro-bind",
            "/",
            "/",
            "--dev",
            "/dev",
            "--unshare-ipc",
            "--unshare-pid",
            "--proc",
            "/proc",
            "--die-with-parent",
            "/bin/true",
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .is_ok_and(|status| status.success())
}

#[cfg(all(test, not(target_os = "linux")))]
pub(super) fn probe_bwrap(path: &Path) -> bool {
    Command::new(path)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .is_ok_and(|status| status.success())
}

/// cBPF supplied through an inherited pipe. AF_UNIX socket/socketpair and
/// io_uring are denied; TCP, UDP, and DNS remain available.
#[cfg(target_os = "linux")]
struct UnixSocketFilter(OwnedFd);

#[cfg(target_os = "linux")]
impl UnixSocketFilter {
    fn new() -> Result<Self, String> {
        let mut fds = [-1; 2];
        if unsafe { libc::pipe2(fds.as_mut_ptr(), libc::O_CLOEXEC) } < 0 {
            return Err(format!(
                "could not create the Unix-socket filter: {}",
                std::io::Error::last_os_error()
            ));
        }
        let read = unsafe { OwnedFd::from_raw_fd(fds[0]) };
        let mut write = unsafe { std::fs::File::from_raw_fd(fds[1]) };
        write
            .write_all(&unix_socket_filter_bytes())
            .map_err(|error| format!("could not write the Unix-socket filter: {error}"))?;
        drop(write);
        if unsafe { libc::fcntl(read.as_raw_fd(), libc::F_SETFD, 0) } < 0 {
            return Err(format!(
                "could not pass the Unix-socket filter to bubblewrap: {}",
                std::io::Error::last_os_error()
            ));
        }
        Ok(Self(read))
    }

    fn fd(&self) -> i32 {
        self.0.as_raw_fd()
    }

    fn into_fd(self) -> OwnedFd {
        self.0
    }
}

#[cfg(target_os = "linux")]
fn unix_socket_filter_bytes() -> Vec<u8> {
    let instructions = unix_socket_filter_instructions();
    let mut bytes = Vec::with_capacity(instructions.len() * 8);
    for (code, jt, jf, constant) in instructions {
        bytes.extend(code.to_ne_bytes());
        bytes.push(jt);
        bytes.push(jf);
        bytes.extend(constant.to_ne_bytes());
    }
    bytes
}

#[cfg(target_os = "linux")]
fn unix_socket_filter_instructions() -> [(u16, u8, u8, u32); 15] {
    let arch = match std::env::consts::ARCH {
        "x86_64" => 0xc000_003e,
        "aarch64" => 0xc000_00b7,
        _ => 0,
    };
    let permission_denied = 0x0005_0000 | libc::EPERM as u32;
    let unix_unsupported = 0x0005_0000 | libc::EAFNOSUPPORT as u32;
    let allow = 0x7fff_0000;
    [
        (0x20, 0, 0, 4),
        (0x15, 1, 0, arch),
        (0x06, 0, 0, permission_denied),
        (0x20, 0, 0, 0),
        (0x35, 0, 1, 0x4000_0000),
        (0x06, 0, 0, permission_denied),
        (0x15, 0, 1, libc::SYS_io_uring_setup as u32),
        (0x06, 0, 0, permission_denied),
        (0x15, 2, 0, libc::SYS_socket as u32),
        (0x15, 1, 0, libc::SYS_socketpair as u32),
        (0x06, 0, 0, allow),
        (0x20, 0, 0, 16),
        (0x15, 0, 1, libc::AF_UNIX as u32),
        (0x06, 0, 0, unix_unsupported),
        (0x06, 0, 0, allow),
    ]
}

#[cfg(target_os = "linux")]
fn which_bwrap() -> Option<PathBuf> {
    fixed_bwrap_paths()
        .into_iter()
        .find(|path| path.is_file())
        .map(Path::to_path_buf)
}

#[cfg(target_os = "linux")]
fn fixed_bwrap_paths() -> [&'static Path; 2] {
    [Path::new("/usr/bin/bwrap"), Path::new("/bin/bwrap")]
}

#[cfg(all(test, target_os = "linux"))]
#[path = "linux_tests.rs"]
mod tests;
