use std::path::{Path, PathBuf};

use super::linux::{
    bwrap_args, control_ipc_args_for, home_args_for, home_args_from_names, probe_bwrap,
};
use super::*;

fn scratch(label: &str) -> PathBuf {
    std::env::temp_dir().join(format!("nurb-{label}-{}", std::process::id()))
}

#[test]
fn bwrap_probe_requires_a_successful_namespace_command() {
    use std::os::unix::fs::PermissionsExt;

    let dir = scratch("bwrap-probe");
    std::fs::create_dir_all(&dir).unwrap();
    let yes = dir.join("yes");
    let no = dir.join("no");
    std::fs::write(&yes, "#!/bin/sh\nexit 0\n").unwrap();
    std::fs::write(&no, "#!/bin/sh\nexit 1\n").unwrap();
    std::fs::set_permissions(&yes, std::fs::Permissions::from_mode(0o700)).unwrap();
    std::fs::set_permissions(&no, std::fs::Permissions::from_mode(0o700)).unwrap();
    assert!(probe_bwrap(&yes));
    assert!(!probe_bwrap(&no));
    std::fs::remove_dir_all(&dir).ok();
}

#[test]
fn non_utf8_home_entries_keep_the_whole_home_read_only() {
    use std::os::unix::ffi::OsStringExt;

    let home = scratch("non-utf-home");
    let name = std::ffi::OsString::from_vec(vec![b'n', b'o', b't', b'-', 0xff]);
    let error = home_args_from_names(&home, ".claude", vec![name]).unwrap_err();
    assert!(error.contains("not valid UTF-8"));
}

#[test]
fn symlinked_home_entries_keep_the_whole_home_read_only() {
    use std::os::unix::fs::symlink;

    let home = scratch("symlink-home");
    let target = scratch("symlink-target");
    std::fs::create_dir_all(&home).unwrap();
    std::fs::write(&target, "mine").unwrap();
    symlink(&target, home.join("linked-dotfile")).unwrap();
    let error = home_args_for(&home, ".claude").unwrap_err();
    assert!(error.contains("cannot be a bubblewrap mount destination"));
    std::fs::remove_dir_all(home).ok();
    std::fs::remove_file(target).ok();
}

#[test]
fn production_bwrap_args_hide_ipc_without_path_masks_or_network_isolation() {
    let runtime = scratch("runtime");
    std::fs::create_dir_all(&runtime).unwrap();
    let runtime = runtime.canonicalize().unwrap();
    let ipc = control_ipc_args_for(Some(&runtime));
    let runtime = runtime.to_str().unwrap();
    assert!(ipc
        .windows(2)
        .any(|pair| pair[0] == "--tmpfs" && pair[1] == runtime));
    assert!(!ipc.contains(&"--ro-bind-try".to_string()));
    assert!(ipc
        .windows(2)
        .any(|pair| pair[0] == "--unsetenv" && pair[1] == "DBUS_SESSION_BUS_ADDRESS"));
    let project = PathBuf::from(runtime);
    let policy = bwrap_args(&project, &project, ".claude", None);
    assert!(policy.contains(&"--unshare-ipc".to_string()));
    assert!(!policy.contains(&"--unshare-net".to_string()));
    assert!(!policy
        .windows(3)
        .any(|triple| triple[0] == "--ro-bind-try" && triple[1] == "/dev/null"));
    std::fs::remove_dir_all(runtime).ok();
}

#[test]
fn home_and_runtime_mount_destinations_resolve_symlinks() {
    use std::os::unix::fs::symlink;

    let root = scratch("canonical-mount");
    let real = root.join("real");
    let link = root.join("link");
    std::fs::create_dir_all(&real).unwrap();
    symlink(&real, &link).unwrap();
    assert_eq!(canonical_existing_dir(link), real.canonicalize().ok());
    std::fs::remove_dir_all(root).ok();
}

#[test]
fn dangerous_custom_agent_homes_are_rejected() {
    let project = scratch("agent-home-project");
    std::fs::create_dir_all(&project).unwrap();
    let home = home().unwrap();
    assert_eq!(
        safe_agent_home(Some(Path::new("/")), &project, &project),
        Ok(None)
    );
    assert_eq!(safe_agent_home(Some(&home), &project, &project), Ok(None));
    assert_eq!(safe_agent_home(home.parent(), &project, &project), Ok(None));
    assert!(safe_agent_home(project.parent(), &project, &project).is_err());
    let (writable, environment) =
        agent_home_policy(".codex", Some(Path::new("/")), &project, &project, true).unwrap();
    assert_eq!(writable, None);
    assert_eq!(
        environment,
        home.join(".codex").to_str().map(str::to_string)
    );
    std::fs::remove_dir_all(project).ok();
}

#[test]
fn project_ancestor_codex_home_is_an_actionable_spawn_error() {
    let state = scratch("codex-state");
    let project = state.join("project");
    let engine = scratch("codex-engine");
    std::fs::create_dir_all(&project).unwrap();
    std::fs::create_dir_all(&engine).unwrap();
    let state = state.canonicalize().unwrap();

    let error = match super::wrap(
        "codex-acp".into(),
        Vec::new(),
        &project,
        &engine,
        ".codex",
        Some(&state),
    ) {
        Err(error) => error,
        Ok(_) => panic!("a state root containing the project must stop the spawn"),
    };
    assert!(error.contains("CODEX_HOME"));
    assert!(error.contains("Choose a separate CODEX_HOME folder"));

    let valid = scratch("codex-state-valid");
    std::fs::create_dir_all(&valid).unwrap();
    let valid = valid.canonicalize().unwrap();
    let (writable, environment) =
        agent_home_policy(".codex", Some(&valid), &project, &engine, true).unwrap();
    assert_eq!(writable, Some(valid.clone()));
    assert_eq!(environment, valid.to_str().map(str::to_string));

    std::fs::remove_dir_all(state).ok();
    std::fs::remove_dir_all(engine).ok();
    std::fs::remove_dir_all(valid).ok();
}

#[test]
fn missing_config_and_custom_agent_homes_become_writable_roots() {
    let root = scratch("writable-roots");
    let project = root.join("project");
    let agent = root.join("codex-home");
    let config = root.join("config/nurb");
    std::fs::create_dir_all(&project).unwrap();
    std::fs::create_dir_all(&agent).unwrap();
    assert_eq!(
        ensure_directory(config.clone(), "test"),
        Some(config.clone())
    );
    assert!(config.is_dir());
    let roots = writable_roots(&project, &project, Some(&agent), Some(&config));
    assert!(roots.contains(&agent.canonicalize().unwrap()));
    assert!(roots.contains(&config.canonicalize().unwrap()));
    std::fs::remove_dir_all(root).ok();
}
