//! Platform process plumbing, the one home for the unix/windows split so it
//! never spreads across the crate. Unix kills a child's whole tree through
//! its process group; Windows has no groups worth trusting, so every child
//! gets a Job Object the moment it spawns and TerminateJobObject takes the
//! tree down.
//!
//! Two ownership flavors on Windows. `attach_owned` sets KILL_ON_JOB_CLOSE,
//! so the OS reaps the tree when the app's last handle vanishes, however the
//! app died: a force-killed app must not leak a uv or npm still writing into
//! app data (seen live: a leaked uv.exe held target\debug locked). `attach`
//! leaves that off for children that legitimately outlive their tree, like a
//! login CLI handing off to the user's browser.

use std::process::{Child, Command};

/// Ready a command for spawning under this module's kill semantics: its own
/// process group on unix, and no flashing console window on Windows (the app
/// is a GUI process, so every console child would otherwise open one).
pub fn configure(command: &mut Command) {
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        command.process_group(0);
    }
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(CREATE_NO_WINDOW);
    }
}

#[cfg(windows)]
pub const CREATE_NO_WINDOW: u32 = 0x0800_0000;

/// A handle that can take down a spawned child and everything it spawned.
/// Cheap to clone; clones address the same tree.
#[derive(Clone)]
pub struct ProcessTree {
    #[cfg(unix)]
    pgid: i32,
    #[cfg(windows)]
    job: std::sync::Arc<windows::Job>,
    /// The direct child, the fallback target when a Windows job could not be
    /// created; on unix it doubles as the identity for `same_child`.
    pid: u32,
}

impl ProcessTree {
    /// Adopt a child that `configure` prepared (or one spawned by a library
    /// on our behalf). Must run promptly after spawn: on Windows the job only
    /// covers descendants forked after assignment. The tree survives this
    /// handle being dropped; use `attach_owned` when it must not.
    pub fn attach(child: &Child) -> Self {
        Self::attach_pid(child.id())
    }

    pub fn attach_pid(pid: u32) -> Self {
        Self::build(pid, false)
    }

    /// Like `attach`, but on Windows the tree dies with the last clone of
    /// this handle, so even a crashed app cannot leak it.
    pub fn attach_owned(child: &Child) -> Self {
        Self::build(child.id(), true)
    }

    pub fn attach_pid_owned(pid: u32) -> Self {
        Self::build(pid, true)
    }

    #[cfg_attr(unix, allow(unused_variables))]
    fn build(pid: u32, kill_on_close: bool) -> Self {
        Self {
            #[cfg(unix)]
            pgid: pid as i32,
            #[cfg(windows)]
            job: std::sync::Arc::new(windows::Job::around(pid, kill_on_close)),
            pid,
        }
    }

    /// Ask the tree to stop. Graceful on unix (SIGTERM); Windows jobs know
    /// only hard termination, so there this is already the kill.
    pub fn terminate(&self) {
        #[cfg(unix)]
        unsafe {
            libc::killpg(self.pgid, libc::SIGTERM);
        }
        #[cfg(windows)]
        self.job.terminate(self.pid);
    }

    /// Stop the tree without appeal.
    pub fn kill(&self) {
        #[cfg(unix)]
        unsafe {
            libc::killpg(self.pgid, libc::SIGKILL);
        }
        #[cfg(windows)]
        self.job.terminate(self.pid);
    }

    /// Whether this tree was attached to the given child, for lists that
    /// remove entries by identity.
    pub fn same_child(&self, pid: u32) -> bool {
        self.pid == pid
    }
}

#[cfg(windows)]
mod windows {
    //! Just enough of the Job Object API, bound by hand: three calls do not
    //! earn a crate dependency.

    use std::ffi::c_void;

    type Handle = isize;
    const PROCESS_SET_QUOTA: u32 = 0x0100;
    const PROCESS_TERMINATE: u32 = 0x0001;
    const JOB_OBJECT_EXTENDED_LIMIT_INFORMATION: u32 = 9;
    const JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE: u32 = 0x2000;

    #[link(name = "kernel32")]
    extern "system" {
        fn CreateJobObjectW(attrs: *const c_void, name: *const u16) -> Handle;
        fn OpenProcess(access: u32, inherit: i32, pid: u32) -> Handle;
        fn AssignProcessToJobObject(job: Handle, process: Handle) -> i32;
        fn SetInformationJobObject(job: Handle, class: u32, info: *const c_void, len: u32) -> i32;
        fn TerminateJobObject(job: Handle, exit_code: u32) -> i32;
        fn TerminateProcess(process: Handle, exit_code: u32) -> i32;
        fn CloseHandle(handle: Handle) -> i32;
    }

    /// JOBOBJECT_EXTENDED_LIMIT_INFORMATION, laid out by hand: only LimitFlags
    /// inside the basic block is read once KILL_ON_JOB_CLOSE is the only flag.
    #[repr(C)]
    #[derive(Default)]
    struct ExtendedLimits {
        // JOBOBJECT_BASIC_LIMIT_INFORMATION
        per_process_user_time_limit: i64,
        per_job_user_time_limit: i64,
        limit_flags: u32,
        minimum_working_set_size: usize,
        maximum_working_set_size: usize,
        active_process_limit: u32,
        affinity: usize,
        priority_class: u32,
        scheduling_class: u32,
        // IO_COUNTERS
        io_counters: [u64; 6],
        process_memory_limit: usize,
        job_memory_limit: usize,
        peak_process_memory_used: usize,
        peak_job_memory_used: usize,
    }

    /// A job wrapped around one child at attach time. When creation or
    /// assignment fails (another tool's job already owns the child without
    /// nesting, say), the handle is zero and termination falls back to the
    /// direct child alone, which matches what killpg does for a child that
    /// never forked.
    pub(super) struct Job(Handle);

    // HANDLEs are process-wide tokens, safe to move and share; all use here
    // is through &self on kernel calls that take their own locks.
    unsafe impl Send for Job {}
    unsafe impl Sync for Job {}

    impl Job {
        pub(super) fn around(pid: u32, kill_on_close: bool) -> Self {
            unsafe {
                let job = CreateJobObjectW(std::ptr::null(), std::ptr::null());
                if job == 0 {
                    return Self(0);
                }
                if kill_on_close {
                    let mut limits = ExtendedLimits::default();
                    limits.limit_flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
                    // A failed set degrades to the plain job rather than
                    // refusing to track the child at all.
                    SetInformationJobObject(
                        job,
                        JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                        &limits as *const ExtendedLimits as *const c_void,
                        std::mem::size_of::<ExtendedLimits>() as u32,
                    );
                }
                let process = OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, 0, pid);
                if process == 0 {
                    CloseHandle(job);
                    return Self(0);
                }
                let assigned = AssignProcessToJobObject(job, process);
                CloseHandle(process);
                if assigned == 0 {
                    CloseHandle(job);
                    return Self(0);
                }
                Self(job)
            }
        }

        pub(super) fn terminate(&self, fallback_pid: u32) {
            unsafe {
                if self.0 != 0 {
                    TerminateJobObject(self.0, 1);
                    return;
                }
                let process = OpenProcess(PROCESS_TERMINATE, 0, fallback_pid);
                if process != 0 {
                    TerminateProcess(process, 1);
                    CloseHandle(process);
                }
            }
        }
    }

    impl Drop for Job {
        fn drop(&mut self) {
            if self.0 != 0 {
                unsafe {
                    CloseHandle(self.0);
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Stdio;
    use std::time::{Duration, Instant};

    fn sleeper() -> Command {
        #[cfg(unix)]
        {
            let mut command = Command::new("sh");
            command.args(["-c", "sleep 60"]);
            command
        }
        #[cfg(windows)]
        {
            let mut command = Command::new("cmd");
            command.args(["/c", "ping -n 60 127.0.0.1 > NUL"]);
            command
        }
    }

    #[test]
    fn a_terminated_tree_is_gone_promptly() {
        let mut command = sleeper();
        command.stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
        configure(&mut command);
        let mut child = command.spawn().unwrap();
        let tree = ProcessTree::attach(&child);

        tree.terminate();
        let deadline = Instant::now() + Duration::from_secs(5);
        loop {
            match child.try_wait() {
                Ok(Some(_)) => break,
                _ if Instant::now() > deadline => {
                    tree.kill();
                    panic!("child survived terminate for 5s");
                }
                _ => std::thread::sleep(Duration::from_millis(50)),
            }
        }
    }

    /// The crash guarantee: on Windows an owned tree dies when its last
    /// handle drops, so a force-killed app cannot leak provisioning children.
    /// Unix has no close-time kill; there the drop is just a drop.
    #[cfg(windows)]
    #[test]
    fn an_owned_tree_dies_with_its_last_handle() {
        let mut command = sleeper();
        command.stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
        configure(&mut command);
        let mut child = command.spawn().unwrap();
        let tree = ProcessTree::attach_owned(&child);

        drop(tree);
        let deadline = Instant::now() + Duration::from_secs(5);
        loop {
            match child.try_wait() {
                Ok(Some(_)) => break,
                _ if Instant::now() > deadline => {
                    let _ = child.kill();
                    panic!("child survived the owned tree's drop for 5s");
                }
                _ => std::thread::sleep(Duration::from_millis(50)),
            }
        }
    }

    #[test]
    fn trees_are_identified_by_their_child() {
        let mut command = sleeper();
        command.stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
        configure(&mut command);
        let mut child = command.spawn().unwrap();
        let tree = ProcessTree::attach(&child);

        assert!(tree.same_child(child.id()));
        assert!(!tree.same_child(child.id().wrapping_add(1)));
        tree.kill();
        let _ = child.wait();
    }
}
