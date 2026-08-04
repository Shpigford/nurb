use std::collections::{HashMap, HashSet};
use std::io::{BufRead, BufReader, Write};
use std::net::TcpListener;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdout, Stdio};
use std::sync::{mpsc, Arc, Condvar, Mutex};
use std::thread;
use std::time::Duration;

const DEFAULT_PORT: u16 = 7373;
// The first build absorbs the cold OCCT import, which alone takes ~45 seconds.
const READY_TIMEOUT: Duration = Duration::from_secs(180);

pub struct Supervisor {
    state: Mutex<SupervisorState>,
    changed: Condvar,
    launcher: crate::env::Launcher,
}

struct SupervisorState {
    projects: HashMap<PathBuf, ServerEntry>,
    shutting_down: bool,
}

enum ServerEntry {
    Starting(Option<Arc<ProjectServer>>),
    Running(Arc<ProjectServer>),
}

struct ProjectServer {
    child: Mutex<ManagedChild>,
    port: u16,
}

struct ManagedChild {
    process: Child,
    stopped: bool,
}

impl Supervisor {
    pub fn new(launcher: crate::env::Launcher) -> Self {
        Self {
            state: Mutex::new(SupervisorState {
                projects: HashMap::new(),
                shutting_down: false,
            }),
            changed: Condvar::new(),
            launcher,
        }
    }

    /// The running server port for a project, spawning `nurb dev` if needed.
    ///
    /// A starting entry makes concurrent opens of the same project wait for
    /// the first (React StrictMode double-fires this in dev). The state lock is
    /// released during startup so app shutdown can kill a cold build promptly.
    pub fn open(&self, project: &Path) -> Result<u16, String> {
        loop {
            let mut state = self.state.lock().unwrap();
            if state.shutting_down {
                return Err("app is shutting down".into());
            }
            match state.projects.get(project) {
                Some(ServerEntry::Running(server)) if is_running(server) => {
                    return Ok(server.port);
                }
                Some(ServerEntry::Running(server)) => {
                    let server = Arc::clone(server);
                    state.projects.remove(project);
                    drop(state);
                    kill_tree(&server);
                }
                Some(ServerEntry::Starting(_)) => {
                    let state = self.changed.wait(state).unwrap();
                    drop(state);
                }
                None => {
                    state
                        .projects
                        .insert(project.to_path_buf(), ServerEntry::Starting(None));
                    break;
                }
            }
        }

        let result = self.start(project);
        let mut kill = None;
        let response = {
            let mut state = self.state.lock().unwrap();
            state.projects.remove(project);
            let response = match result {
                Ok(server) if !state.shutting_down => {
                    let port = server.port;
                    state
                        .projects
                        .insert(project.to_path_buf(), ServerEntry::Running(server));
                    Ok(port)
                }
                Ok(server) => {
                    kill = Some(server);
                    Err("app is shutting down".into())
                }
                Err(error) => Err(error),
            };
            self.changed.notify_all();
            response
        };
        if let Some(server) = kill {
            kill_tree(&server);
        }
        response
    }

    fn start(&self, project: &Path) -> Result<Arc<ProjectServer>, String> {
        let mut attempt = self.spawn(project)?;
        if let Err(first) = wait_ready(&attempt) {
            // A port grabbed between our probe and the bind is a hard exit
            // (cli.py treats an explicitly asked-for taken port as an error),
            // so one respawn on a fresh port covers the race.
            kill_tree(&attempt);
            if self.is_shutting_down() {
                return Err("app is shutting down".into());
            }
            attempt = self.spawn(project)?;
            if let Err(second) = wait_ready(&attempt) {
                kill_tree(&attempt);
                return Err(format!("{first}; retry: {second}"));
            }
        }
        Ok(attempt)
    }

    /// Claim a port and publish the child while holding the shared state lock.
    /// Starting children have not bound yet, so the OS alone cannot keep two
    /// concurrent opens from choosing the same port.
    fn spawn(&self, project: &Path) -> Result<Arc<ProjectServer>, String> {
        let mut state = self.state.lock().unwrap();
        if state.shutting_down {
            return Err("app is shutting down".into());
        }
        let reserved = state
            .projects
            .values()
            .filter_map(|entry| match entry {
                ServerEntry::Starting(Some(server)) | ServerEntry::Running(server) => {
                    Some(server.port)
                }
                ServerEntry::Starting(None) => None,
            })
            .collect::<HashSet<_>>();
        let server = spawn_server(project, &self.launcher, &reserved)?;
        match state.projects.get_mut(project) {
            Some(ServerEntry::Starting(slot)) => {
                *slot = Some(Arc::clone(&server));
                Ok(server)
            }
            _ => {
                drop(state);
                kill_tree(&server);
                Err("project was closed while starting".into())
            }
        }
    }

    fn is_shutting_down(&self) -> bool {
        self.state.lock().unwrap().shutting_down
    }

    /// The port a project's server is listening on, if it is up.
    pub fn port(&self, project: &Path) -> Option<u16> {
        match self.state.lock().unwrap().projects.get(project) {
            Some(ServerEntry::Running(server)) if is_running(server) => Some(server.port),
            _ => None,
        }
    }

    /// Kill one project's server, waiting out an in-flight startup first so the
    /// child never escapes. Other projects' servers are untouched.
    pub fn close(&self, project: &Path) {
        loop {
            let mut state = self.state.lock().unwrap();
            match state.projects.get(project) {
                Some(ServerEntry::Running(server)) => {
                    let server = Arc::clone(server);
                    state.projects.remove(project);
                    self.changed.notify_all();
                    drop(state);
                    kill_tree(&server);
                    return;
                }
                Some(ServerEntry::Starting(_)) => {
                    let state = self.changed.wait(state).unwrap();
                    drop(state);
                }
                None => return,
            }
        }
    }

    pub fn shutdown(&self) {
        let servers = {
            let mut state = self.state.lock().unwrap();
            state.shutting_down = true;
            let servers = state
                .projects
                .drain()
                .filter_map(|(_, entry)| match entry {
                    ServerEntry::Starting(server) => server,
                    ServerEntry::Running(server) => Some(server),
                })
                .collect::<Vec<_>>();
            self.changed.notify_all();
            servers
        };
        for server in servers {
            kill_tree(&server);
        }
    }
}

fn free_port(reserved: &HashSet<u16>) -> Result<u16, String> {
    for port in DEFAULT_PORT..DEFAULT_PORT + 40 {
        if !reserved.contains(&port) && TcpListener::bind(("127.0.0.1", port)).is_ok() {
            return Ok(port);
        }
    }
    Err("no free port between 7373 and 7412".into())
}

fn spawn_server(
    project: &Path,
    launcher: &crate::env::Launcher,
    reserved: &HashSet<u16>,
) -> Result<Arc<ProjectServer>, String> {
    let port = free_port(reserved)?;
    let mut command = launcher.nurb();
    command
        .args(["dev", "--port", &port.to_string()])
        .current_dir(project)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        // Its own process group, so killing it takes the whole uv -> python
        // tree with it rather than orphaning the server.
        .process_group(0);
    let process = command
        .spawn()
        .map_err(|e| format!("could not start nurb dev: {e}"))?;
    Ok(Arc::new(ProjectServer {
        child: Mutex::new(ManagedChild {
            process,
            stopped: false,
        }),
        port,
    }))
}

fn wait_ready(server: &ProjectServer) -> Result<(), String> {
    let stdout = server
        .child
        .lock()
        .unwrap()
        .process
        .stdout
        .take()
        .ok_or("child stdout missing")?;
    let (tx, rx) = mpsc::channel();
    drain_stdout(stdout, server.port, tx);
    match rx.recv_timeout(READY_TIMEOUT) {
        Ok(Ok(())) => Ok(()),
        Ok(Err(e)) => Err(e),
        Err(_) => Err(format!(
            "nurb dev did not become ready within {}s",
            READY_TIMEOUT.as_secs()
        )),
    }
}

/// Watches for the ready line, then keeps draining so the pipe never fills.
fn drain_stdout(stdout: ChildStdout, port: u16, tx: mpsc::Sender<Result<(), String>>) {
    let ready_line = format!("http://127.0.0.1:{port}");
    thread::spawn(move || {
        let reader = BufReader::new(stdout);
        let mut ready = false;
        for line in reader.lines() {
            let Ok(line) = line else { break };
            // Not eprintln!, which panics when stderr is a broken pipe (as
            // after the tauri dev harness dies) and would kill this thread
            // before the ready signal ever sends.
            let _ = writeln!(std::io::stderr(), "[nurb dev :{port}] {line}");
            if !ready && line.contains(&ready_line) {
                ready = true;
                let _ = tx.send(Ok(()));
            }
        }
        if !ready {
            let _ = tx.send(Err("nurb dev exited before becoming ready".into()));
        }
    });
}

fn is_running(server: &ProjectServer) -> bool {
    let mut child = server.child.lock().unwrap();
    !child.stopped && matches!(child.process.try_wait(), Ok(None))
}

fn kill_tree(server: &ProjectServer) {
    let mut child = server.child.lock().unwrap();
    if child.stopped {
        return;
    }
    let pgid = child.process.id() as i32;
    unsafe {
        libc::killpg(pgid, libc::SIGTERM);
    }
    for _ in 0..20 {
        if matches!(child.process.try_wait(), Ok(Some(_))) {
            child.stopped = true;
            return;
        }
        thread::sleep(Duration::from_millis(100));
    }
    unsafe {
        libc::killpg(pgid, libc::SIGKILL);
    }
    let _ = child.process.wait();
    child.stopped = true;
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Command;
    use std::time::Instant;

    #[test]
    fn port_probe_skips_ports_claimed_by_starting_servers() {
        let first = free_port(&HashSet::new()).unwrap();
        let second = free_port(&HashSet::from([first])).unwrap();

        assert_ne!(first, second);
    }

    #[test]
    fn shutdown_kills_a_server_that_is_still_starting() {
        let process = Command::new("sh")
            .args(["-c", "sleep 60"])
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .process_group(0)
            .spawn()
            .unwrap();
        let server = Arc::new(ProjectServer {
            child: Mutex::new(ManagedChild {
                process,
                stopped: false,
            }),
            port: DEFAULT_PORT,
        });
        let supervisor = Supervisor::new(crate::env::Launcher::Checkout {
            repo: PathBuf::from("."),
        });
        supervisor.state.lock().unwrap().projects.insert(
            PathBuf::from("/test/startup"),
            ServerEntry::Starting(Some(Arc::clone(&server))),
        );

        let started = Instant::now();
        supervisor.shutdown();

        assert!(started.elapsed() < Duration::from_secs(3));
        assert!(matches!(
            server.child.lock().unwrap().process.try_wait(),
            Ok(Some(_))
        ));
    }
}
