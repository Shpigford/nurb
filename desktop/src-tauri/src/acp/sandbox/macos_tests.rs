use std::path::PathBuf;
use std::process::Command;

use super::*;

fn scratch(label: &str) -> PathBuf {
    std::env::temp_dir().join(format!("nurb-{label}-{}", std::process::id()))
}

fn sh(profile: &str, script: &str) -> bool {
    Command::new("/usr/bin/sandbox-exec")
        .args(["-p", profile, "/bin/sh", "-c", script])
        .output()
        .expect("sandbox-exec runs")
        .status
        .success()
}

fn sandboxed_command(profile: &str, program: &str, args: &[String]) -> bool {
    Command::new("/usr/bin/sandbox-exec")
        .args(["-p", profile, program])
        .args(args)
        .output()
        .expect("sandbox-exec runs")
        .status
        .success()
}

#[test]
fn the_kernel_enforces_the_write_boundary() {
    let project = scratch("sbx");
    let outside = scratch("sbx-out");
    std::fs::create_dir_all(&project).unwrap();
    std::fs::create_dir_all(&outside).unwrap();
    let profile = format!(
        "(version 1)\n(allow default)\n(deny file-write*)\n(allow file-write* (subpath {}) (literal \"/dev/null\"))\n",
        quoted(&project.canonicalize().unwrap())
    );
    assert!(sh(
        &profile,
        &format!("echo hi > '{}/inside.txt'", project.display())
    ));
    assert!(!sh(
        &profile,
        &format!("echo hi > '{}/escape.txt'", outside.display())
    ));
    assert!(sh(&profile, "cat /etc/hosts > /dev/null"));
    std::fs::remove_dir_all(project).ok();
    std::fs::remove_dir_all(outside).ok();
}

#[test]
fn the_real_profile_admits_the_project_and_agent_state() {
    let project = scratch("sbx-real");
    std::fs::create_dir_all(&project).unwrap();
    let profile = profile(&project, &project, None);
    assert!(sh(
        &profile,
        &format!("echo hi > '{}/part.py'", project.display())
    ));
    assert!(!sh(
        &profile,
        "echo hacked >> \"$HOME/nurb-sbx-canary\" && rm \"$HOME/nurb-sbx-canary\""
    ));
    for dot in AGENT_DOTS {
        let existed = home().map(|h| h.join(dot).exists()).unwrap_or(false);
        assert!(sh(
            &profile,
            &format!(
                "mkdir -p \"$HOME/{dot}/nurb-sbx-test\" && rmdir \"$HOME/{dot}/nurb-sbx-test\""
            )
        ));
        if !existed {
            if let Some(home) = home() {
                std::fs::remove_dir(home.join(dot)).ok();
            }
        }
    }
    std::fs::remove_dir_all(project).ok();
}

#[test]
fn the_real_profile_honors_a_custom_codex_home() {
    let project = scratch("sbx-custom-project");
    let custom = home()
        .unwrap()
        .join(format!("nurb-codex-home-test-{}", std::process::id()));
    std::fs::create_dir_all(&project).unwrap();
    std::fs::create_dir_all(&custom).unwrap();
    let profile = profile(&project, &project, Some(&custom));
    assert!(sh(
        &profile,
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
fn the_real_profile_blocks_unix_sockets_but_keeps_tcp() {
    use std::os::unix::net::UnixListener;

    let project = scratch("socket-policy");
    std::fs::create_dir_all(&project).unwrap();
    let socket = project.join("control.sock");
    let unix = UnixListener::bind(&socket).unwrap();
    let tcp = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    let port = tcp.local_addr().unwrap().port().to_string();
    let profile = profile(&project, &project, None);
    assert!(!sandboxed_command(
        &profile,
        "/usr/bin/nc",
        &[
            "-z".into(),
            "-n".into(),
            "-U".into(),
            "-w".into(),
            "1".into(),
            socket.display().to_string(),
        ]
    ));
    assert!(sandboxed_command(
        &profile,
        "/usr/bin/nc",
        &[
            "-z".into(),
            "-n".into(),
            "-w".into(),
            "1".into(),
            "127.0.0.1".into(),
            port,
        ]
    ));
    assert!(
        profile.contains("(allow network-outbound (literal \"/private/var/run/mDNSResponder\"))")
    );
    assert!(sandboxed_command(
        &profile,
        "/usr/bin/dscacheutil",
        &[
            "-q".into(),
            "host".into(),
            "-a".into(),
            "name".into(),
            "localhost".into(),
        ]
    ));
    drop(unix);
    std::fs::remove_dir_all(project).ok();
}

#[test]
fn quoting_survives_hostile_paths() {
    let path = PathBuf::from("/Users/me/Documents/nurb/Banana Holder");
    assert_eq!(quoted(&path), "\"/Users/me/Documents/nurb/Banana Holder\"");
    let tricky = PathBuf::from("/Users/me/a\"b");
    assert_eq!(quoted(&tricky), "\"/Users/me/a\\\"b\"");
    assert_eq!(regex_escaped("/Users/j.p"), "/Users/j\\.p");
}
