use std::path::{Path, PathBuf};
use std::process::Command;

use super::super::AGENT_DOTS;
use super::*;

fn scratch(label: &str) -> PathBuf {
    std::env::temp_dir().join(format!("nurb-{label}-{}", std::process::id()))
}

fn bwrapped(project: &Path, engine_root: &Path, script: &str) -> bool {
    bwrapped_as(".claude", None, project, engine_root, script)
}

fn bwrapped_as(
    agent_dot: &str,
    agent_home: Option<&Path>,
    project: &Path,
    engine_root: &Path,
    script: &str,
) -> bool {
    let program = which_bwrap().expect("bubblewrap is required for this test");
    assert!(
        probe_bwrap(&program),
        "bubblewrap must load the real filter"
    );
    let filter = UnixSocketFilter::new().unwrap();
    let agent_home = safe_agent_home(agent_home, project, engine_root).unwrap();
    let mut args = vec!["--seccomp".into(), filter.fd().to_string()];
    args.extend(bwrap_args(
        project,
        engine_root,
        agent_dot,
        agent_home.as_deref(),
    ));
    args.extend(["/bin/sh".into(), "-c".into(), script.into()]);
    Command::new(program)
        .args(args)
        .output()
        .expect("bwrap runs")
        .status
        .success()
}

#[test]
fn production_wrap_uses_a_fixed_bwrap_and_holds_the_filter_fd() {
    let project = scratch("production-wrap");
    std::fs::create_dir_all(&project).unwrap();
    let (program, args, confined, guard) = super::wrap(
        "/bin/true".into(),
        Vec::new(),
        &project,
        &project,
        ".codex",
        None,
    )
    .unwrap();
    assert!(confined);
    assert!(fixed_bwrap_paths()
        .iter()
        .any(|candidate| *candidate == Path::new(&program)));
    let guard = guard.expect("a confined spawn owns the filter read fd");
    let fd = guard._fd.as_raw_fd().to_string();
    assert!(args
        .windows(2)
        .any(|pair| pair[0] == "--seccomp" && pair[1] == fd));
    std::fs::remove_dir_all(project).ok();
}

#[test]
fn the_seccomp_filter_blocks_unix_sockets_but_keeps_tcp() {
    let instructions = unix_socket_filter_instructions();
    let child = unsafe { libc::fork() };
    assert!(child >= 0, "fork succeeds");
    if child == 0 {
        let mut raw: Vec<libc::sock_filter> = instructions
            .iter()
            .map(|(code, jt, jf, constant)| libc::sock_filter {
                code: *code,
                jt: *jt,
                jf: *jf,
                k: *constant,
            })
            .collect();
        let mut program = libc::sock_fprog {
            len: raw.len() as u16,
            filter: raw.as_mut_ptr(),
        };
        let no_privs = unsafe { libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) };
        let installed = unsafe {
            libc::syscall(
                libc::SYS_seccomp,
                libc::SECCOMP_SET_MODE_FILTER,
                0,
                &mut program,
            )
        };
        let unix = unsafe { libc::socket(libc::AF_UNIX, libc::SOCK_STREAM, 0) };
        let unix_error = std::io::Error::last_os_error().raw_os_error();
        let mut pair = [-1; 2];
        let socketpair =
            unsafe { libc::socketpair(libc::AF_UNIX, libc::SOCK_STREAM, 0, pair.as_mut_ptr()) };
        let socketpair_error = std::io::Error::last_os_error().raw_os_error();
        let ring = unsafe {
            libc::syscall(
                libc::SYS_io_uring_setup,
                1,
                std::ptr::null::<libc::c_void>(),
            )
        };
        let ring_error = std::io::Error::last_os_error().raw_os_error();
        let tcp = unsafe { libc::socket(libc::AF_INET, libc::SOCK_STREAM, 0) };
        let passed = no_privs == 0
            && installed == 0
            && unix == -1
            && unix_error == Some(libc::EAFNOSUPPORT)
            && socketpair == -1
            && socketpair_error == Some(libc::EAFNOSUPPORT)
            && ring == -1
            && ring_error == Some(libc::EPERM)
            && tcp >= 0;
        unsafe { libc::_exit(i32::from(!passed)) };
    }
    let mut status = 0;
    assert_eq!(unsafe { libc::waitpid(child, &mut status, 0) }, child);
    assert!(libc::WIFEXITED(status));
    assert_eq!(libc::WEXITSTATUS(status), 0);
}

#[test]
fn the_kernel_enforces_the_write_boundary() {
    let project = scratch("bwrap");
    std::fs::create_dir_all(&project).unwrap();
    let project = project.canonicalize().unwrap();
    let outside = home()
        .unwrap()
        .join(format!("nurb-bwrap-out-{}", std::process::id()));
    std::fs::create_dir_all(&outside).unwrap();
    let existing = outside.join("notes.txt");
    std::fs::write(&existing, "mine").unwrap();

    assert!(bwrapped(
        &project,
        &project,
        &format!("echo hi > '{}/inside.txt'", project.display())
    ));
    assert!(!bwrapped(
        &project,
        &project,
        &format!("echo hi > '{}/escape.txt'", outside.display())
    ));
    assert!(!outside.join("escape.txt").exists());
    assert!(bwrapped(&project, &project, "cat /etc/hosts > /dev/null"));
    assert!(bwrapped(&project, &project, "echo discard > /dev/null"));
    assert!(!bwrapped(
        &project,
        &project,
        &format!("echo hacked > '{}'", existing.display())
    ));
    assert!(!bwrapped(
        &project,
        &project,
        &format!("rm -rf '{}'", outside.display())
    ));
    assert_eq!(std::fs::read_to_string(&existing).unwrap(), "mine");
    // Counted by glob rather than a pipeline. `$(ls -d /proc/[0-9]* | wc -l)`
    // forks a subshell, an ls and a wc, and all three appear in the listing
    // they are counting: that reads 5 under dash on Debian and failed here
    // while the namespace was working perfectly. Expanding the glob in the
    // shell itself spawns nothing, so this counts only what the sandbox holds.
    assert!(bwrapped(
        &project,
        &project,
        "set -- /proc/[0-9]*; test \"$#\" -le 3"
    ));
    std::fs::remove_dir_all(project).ok();
    std::fs::remove_dir_all(outside).ok();
}

#[test]
fn the_real_wrapping_admits_the_project_and_agent_state() {
    let project = scratch("bwrap-real");
    std::fs::create_dir_all(&project).unwrap();
    let project = project.canonicalize().unwrap();
    assert!(bwrapped(
        &project,
        &project,
        &format!("echo hi > '{}/part.py'", project.display())
    ));
    let home = home().unwrap();
    for dot in AGENT_DOTS {
        let state = home.join(dot);
        let existed = state.exists();
        std::fs::create_dir_all(&state).unwrap();
        let script = format!(
            "mkdir -p \"$HOME/{dot}/nurb-bwrap-test\" && rmdir \"$HOME/{dot}/nurb-bwrap-test\""
        );
        assert!(bwrapped_as(dot, None, &project, &project, &script));
        let other = if dot == ".claude" {
            ".codex"
        } else {
            ".claude"
        };
        assert!(!bwrapped_as(other, None, &project, &project, &script));
        if !existed {
            std::fs::remove_dir(&state).ok();
        }
    }
    std::fs::remove_dir_all(project).ok();
}

#[test]
fn the_real_wrapping_honors_a_custom_codex_home() {
    let project = scratch("bwrap-custom-project");
    let custom = home()
        .unwrap()
        .join(format!("nurb-codex-home-test-{}", std::process::id()));
    std::fs::create_dir_all(&project).unwrap();
    std::fs::create_dir_all(&custom).unwrap();
    let project = project.canonicalize().unwrap();
    assert!(bwrapped_as(
        ".codex",
        Some(&custom),
        &project,
        &project,
        &format!("echo state > '{}/session.json'", custom.display())
    ));
    assert_eq!(
        std::fs::read_to_string(custom.join("session.json")).unwrap(),
        "state\n"
    );
    std::fs::remove_dir_all(project).ok();
    std::fs::remove_dir_all(custom).ok();
}

#[test]
fn agent_state_beside_the_directory_is_writable_too() {
    let home = home().unwrap();
    let probe = home.join(format!(".claude-nurbprobe-{}", std::process::id()));
    std::fs::write(&probe, "probe").unwrap();
    let fresh = home.join(format!(".claude-nurbfresh-{}", std::process::id()));
    let project = scratch("bwrap-dot");
    std::fs::create_dir_all(&project).unwrap();
    let project = project.canonicalize().unwrap();

    assert!(bwrapped(
        &project,
        &project,
        &format!("printf x >> '{}'", probe.display())
    ));
    assert!(bwrapped(
        &project,
        &project,
        &format!(
            "printf y > '{0}.tmp' && mv '{0}.tmp' '{0}'",
            fresh.display()
        )
    ));
    assert_eq!(std::fs::read_to_string(&fresh).unwrap(), "y");
    assert!(bwrapped(
        &project,
        &project,
        &format!(
            "printf z > '{0}.tmp' && mv '{0}.tmp' '{0}'",
            probe.display()
        )
    ));
    let unrelated = home.join(format!("nurb-unrelated-{}", std::process::id()));
    std::fs::write(&unrelated, "probe").unwrap();
    assert!(!bwrapped(
        &project,
        &project,
        &format!("printf x >> '{}'", unrelated.display())
    ));

    std::fs::remove_dir_all(project).ok();
    std::fs::remove_file(probe).ok();
    std::fs::remove_file(fresh).ok();
    std::fs::remove_file(unrelated).ok();
}

#[test]
fn the_wrapping_keeps_the_process_group_and_dies_with_its_parent() {
    let project = std::env::temp_dir();
    let (_, args, _, _guard) = super::wrap(
        "/bin/sh".into(),
        Vec::new(),
        &project,
        &project,
        ".claude",
        None,
    )
    .unwrap();
    assert!(args.contains(&"--die-with-parent".to_string()));
    assert!(args.contains(&"--unshare-pid".to_string()));
    assert!(!args.contains(&"--new-session".to_string()));
}

#[test]
fn paths_with_spaces_need_no_quoting_because_they_are_argv() {
    let project = scratch("bwrap spaces");
    std::fs::create_dir_all(&project).unwrap();
    let project = project.canonicalize().unwrap();
    let (_, args, _, _guard) = super::wrap(
        "/bin/sh".into(),
        Vec::new(),
        &project,
        &project,
        ".claude",
        None,
    )
    .unwrap();
    let want = project.to_string_lossy().into_owned();
    assert!(args.iter().filter(|arg| **arg == want).count() >= 2);
    assert!(bwrapped(
        &project,
        &project,
        &format!("echo hi > '{}/x.txt'", project.display())
    ));
    std::fs::remove_dir_all(project).ok();
}
