//! Cross-platform child-process handling, in one place.
//!
//! Upstream assumes Unix throughout: every child runs in its own process
//! group, and killing the group with killpg takes the child plus whatever it
//! spawned (uv -> python -> the dev server, or a login browser flow). Windows
//! has no process groups, so the equivalent is two pieces: children are
//! spawned with CREATE_NEW_PROCESS_GROUP so console signals meant for the app
//! never reach them, and a tree is killed with `taskkill /T`, which is the one
//! reliable way to take a child and its descendants together.
//!
//! All other process code in this crate goes through these two functions so
//! the platform difference has exactly one home.

use std::process::Command;

/// Put the child in its own process group (Unix) or a new process group
/// without a console window (Windows). Call before `spawn`.
pub(crate) fn own_group(command: &mut Command) {
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        command.process_group(0);
    }
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        // CREATE_NEW_PROCESS_GROUP: Ctrl+C/Ctrl+Break sent to the app's
        // console must not reach the child. CREATE_NO_WINDOW: a console-less
        // app must not flash a terminal for each child it spawns.
        const CREATE_NEW_PROCESS_GROUP: u32 = 0x0000_0200;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        command.creation_flags(CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW);
    }
}

/// Take the process and everything it spawned. On Unix this is the process
/// group; on Windows, `taskkill /T`, spawned detached so it never blocks on
/// the very process it is killing.
pub(crate) fn kill_tree(pid: u32) {
    #[cfg(unix)]
    unsafe {
        libc::killpg(pid as i32, libc::SIGTERM);
    }
    #[cfg(windows)]
    {
        let _ = Command::new("taskkill")
            .args(["/PID", &pid.to_string(), "/T", "/F"])
            .stdin(std::process::Stdio::null())
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status();
    }
}

/// Force-kill the process and its tree, for a child that outlived its grace
/// period. Unix: SIGKILL to the group. Windows: taskkill /F again (it is
/// already force, but a second call covers a tree that was still spawning).
pub(crate) fn kill_tree_force(pid: u32) {
    #[cfg(unix)]
    unsafe {
        libc::killpg(pid as i32, libc::SIGKILL);
    }
    #[cfg(windows)]
    {
        let _ = Command::new("taskkill")
            .args(["/PID", &pid.to_string(), "/T", "/F"])
            .stdin(std::process::Stdio::null())
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status();
    }
}
