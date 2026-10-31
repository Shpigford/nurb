//! The one serve the app talks to: a Starlette process with the database
//! behind it, on loopback, shared by every project in the window.

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::os::unix::process::CommandExt;
use std::path::PathBuf;
use std::process::{Child, ExitStatus, Stdio};
use std::sync::{Arc, Condvar, Mutex};
use std::thread;
use std::time::{Duration, Instant};

const DEFAULT_PORT: u16 = 7373;
// The first request absorbs the cold OCCT import, which alone takes ~45 seconds
// on an idle machine and stretched past two minutes on a loaded one (issue
// #202), so the deadline leaves room for a busy machine rather than killing a
// nearly-ready server.
const READY_TIMEOUT: Duration = Duration::from_secs(300);
// A health probe talks to a process on this machine, so anything slower than
// this is a wedged or dead serve, not a slow one.
const HEALTH_TIMEOUT: Duration = Duration::from_millis(500);

/// What the webview needs to reach the serve: it fetches and opens its
/// websocket against this URL directly.
/// Deserialized straight from the serve's own serve.json, so the file and the
/// shape the webview receives cannot drift.
#[derive(Clone, serde::Serialize, serde::Deserialize)]
pub struct ServeInfo {
    pub url: String,
    pub port: u16,
    pub pid: u32,
    pub token: String,
}

pub struct Supervisor {
    state: Mutex<SupervisorState>,
    changed: Condvar,
    launcher: crate::env::Launcher,
    /// Set only for a debug test run, which gets its own home so it never
    /// touches the developer's ~/.config/nurb.
    home: Option<PathBuf>,
}

struct SupervisorState {
    phase: Phase,
    shutting_down: bool,
}

enum Phase {
    Idle,
    /// Carries the child as soon as it exists, so shutting the app down during
    /// a cold start still takes the serve with it.
    Starting(Option<Arc<ManagedChild>>),
    Running(Running),
}

struct Running {
    info: ServeInfo,
    /// `None` for a serve we adopted. Another process owns that one, so it is
    /// never killed.
    child: Option<Arc<ManagedChild>>,
}

struct ManagedChild {
    state: Mutex<ChildState>,
}

struct ChildState {
    process: Child,
    stopped: bool,
}

impl Supervisor {
    pub fn new(launcher: crate::env::Launcher, data: PathBuf) -> Self {
        Self {
            state: Mutex::new(SupervisorState {
                phase: Phase::Idle,
                shutting_down: false,
            }),
            changed: Condvar::new(),
            launcher,
            home: home_override(data),
        }
    }

    /// The serve's address, starting one if nothing is listening.
    ///
    /// Idempotent: a `Starting` phase makes concurrent callers wait for the
    /// first rather than spawn a second serve. A remembered serve that no
    /// longer answers is dropped and replaced, which is how the page recovers
    /// after a crash: its websocket drops and it asks again.
    pub fn ensure(&self) -> Result<ServeInfo, String> {
        loop {
            let mut state = self.state.lock().unwrap();
            if state.shutting_down {
                return Err("app is shutting down".into());
            }
            match &state.phase {
                Phase::Running(running) if alive(&running.info) => {
                    return Ok(running.info.clone());
                }
                Phase::Running(_) => {
                    let Phase::Running(dead) =
                        std::mem::replace(&mut state.phase, Phase::Idle)
                    else {
                        unreachable!()
                    };
                    drop(state);
                    if let Some(child) = dead.child {
                        kill_tree(&child);
                    }
                }
                Phase::Starting(_) => {
                    let state = self.changed.wait(state).unwrap();
                    drop(state);
                }
                Phase::Idle => {
                    state.phase = Phase::Starting(None);
                    break;
                }
            }
        }

        let result = self.start();
        let mut kill = None;
        let mut state = self.state.lock().unwrap();
        let response = match result {
            Ok(running) if !state.shutting_down => {
                let info = running.info.clone();
                state.phase = Phase::Running(running);
                Ok(info)
            }
            Ok(running) => {
                kill = running.child;
                state.phase = Phase::Idle;
                Err("app is shutting down".into())
            }
            Err(error) => {
                state.phase = Phase::Idle;
                Err(error)
            }
        };
        self.changed.notify_all();
        drop(state);
        if let Some(child) = kill {
            kill_tree(&child);
        }
        response
    }

    fn start(&self) -> Result<Running, String> {
        // Whatever already holds this home's lock wins, including a serve
        // another process started against the same home.
        if let Some(info) = self.published().filter(alive) {
            return Ok(Running {
                info,
                child: None,
            });
        }
        let first = match self.attempt() {
            Ok(running) => return Ok(running),
            // A timed-out serve is almost always a slow one, not a dead one
            // (issue #202), so starting over just pays the same cost again.
            Err(error @ NotReady::TimedOut) => return Err(error.message()),
            Err(NotReady::Exited(reason)) => reason,
        };
        if self.is_shutting_down() {
            return Err("app is shutting down".into());
        }
        // A port taken between our probe and the serve's bind is a hard exit,
        // so one retry on a fresh port covers the race.
        match self.attempt() {
            Ok(running) => Ok(running),
            Err(second) => Err(format!("{first}; retry: {}", second.message())),
        }
    }

    /// Spawn one serve and wait for it to publish serve.json.
    fn attempt(&self) -> Result<Running, NotReady> {
        let port = self.preferred_port().map_err(NotReady::Exited)?;
        let child = self.spawn(port).map_err(NotReady::Exited)?;
        self.publish_child(&child).map_err(NotReady::Exited)?;
        let deadline = Instant::now() + READY_TIMEOUT;
        loop {
            // Ours only once it names our port; a serve.json naming another
            // port belongs to the process holding the lock, and our child is
            // about to exit 0 for that reason.
            if let Some(info) = self.published().filter(|info| info.port == port) {
                if alive(&info) {
                    return Ok(Running {
                        info,
                        child: Some(child),
                    });
                }
            }
            if let Some(status) = exited(&child) {
                if status.success() {
                    if let Some(info) = self.published().filter(alive) {
                        return Ok(Running {
                            info,
                            child: None,
                        });
                    }
                }
                return Err(NotReady::Exited(format!("the serve exited: {status}")));
            }
            if Instant::now() >= deadline {
                kill_tree(&child);
                return Err(NotReady::TimedOut);
            }
            thread::sleep(Duration::from_millis(100));
        }
    }

    /// The port this home's connect.json remembers, when it is still free, so a
    /// command a user pasted into an agent keeps naming the right port across
    /// launches; otherwise the first free one from the default.
    fn preferred_port(&self) -> Result<u16, String> {
        let remembered = std::fs::read_to_string(self.home().join("connect.json"))
            .ok()
            .and_then(|text| serde_json::from_str::<serde_json::Value>(&text).ok())
            .and_then(|saved| saved.get("port")?.as_u64())
            .and_then(|port| u16::try_from(port).ok())
            .filter(|port| *port > 0 && TcpListener::bind(("127.0.0.1", *port)).is_ok());
        match remembered {
            Some(port) => Ok(port),
            None => free_port(),
        }
    }

    fn spawn(&self, port: u16) -> Result<Arc<ManagedChild>, String> {
        let mut command = self.launcher.serve();
        command
            .args(["--port", &port.to_string()])
            .stdin(Stdio::null())
            // The serve keeps its own <home>/serve.log; letting it share the
            // app's stderr means a `tauri dev` run sees it without tailing.
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            // Its own process group, so killing it takes the whole uv ->
            // python tree rather than orphaning the server.
            .process_group(0);
        if let Some(home) = &self.home {
            std::fs::create_dir_all(home)
                .map_err(|e| format!("could not create {}: {e}", home.display()))?;
            command.env("NURB_HOME", home);
        }
        let process = command
            .spawn()
            .map_err(|e| format!("could not start the serve: {e}"))?;
        Ok(Arc::new(ManagedChild {
            state: Mutex::new(ChildState {
                process,
                stopped: false,
            }),
        }))
    }

    /// Hand the new child to the shared state so shutdown can reach it.
    fn publish_child(&self, child: &Arc<ManagedChild>) -> Result<(), String> {
        let mut state = self.state.lock().unwrap();
        match &mut state.phase {
            Phase::Starting(slot) => {
                *slot = Some(Arc::clone(child));
                Ok(())
            }
            _ => {
                drop(state);
                kill_tree(child);
                Err("app is shutting down".into())
            }
        }
    }

    fn is_shutting_down(&self) -> bool {
        self.state.lock().unwrap().shutting_down
    }

    /// The serve if one is already answering, without starting one. For
    /// callers that want the tools when they are there and must not pay a
    /// cold start when they are not.
    pub fn published_live(&self) -> Option<ServeInfo> {
        let running = match &self.state.lock().unwrap().phase {
            Phase::Running(running) => Some(running.info.clone()),
            _ => None,
        };
        running.or_else(|| self.published()).filter(alive)
    }

    /// The serve.json this home currently advertises, live or stale.
    fn published(&self) -> Option<ServeInfo> {
        let text = std::fs::read_to_string(self.home().join("serve.json")).ok()?;
        serde_json::from_str(&text).ok()
    }

    pub fn home(&self) -> PathBuf {
        if let Some(home) = &self.home {
            return home.clone();
        }
        default_home()
    }

    pub fn shutdown(&self) {
        let child = {
            let mut state = self.state.lock().unwrap();
            state.shutting_down = true;
            let child = match std::mem::replace(&mut state.phase, Phase::Idle) {
                Phase::Starting(child) => child,
                Phase::Running(running) => running.child,
                Phase::Idle => None,
            };
            self.changed.notify_all();
            child
        };
        if let Some(child) = child {
            kill_tree(&child);
        }
    }
}

#[cfg(debug_assertions)]
fn home_override(data: PathBuf) -> Option<PathBuf> {
    // Only a test run redirects the app data dir, and that run must not write
    // into the developer's real nurb home. The shipped app keeps the default
    // home on purpose: one database for the app and for any MCP client
    // connected over HTTP.
    std::env::var_os("NURB_DESKTOP_DATA").map(|_| data.join("home"))
}

#[cfg(not(debug_assertions))]
fn home_override(_data: PathBuf) -> Option<PathBuf> {
    None
}

/// Where the serve keeps serve.json, mirroring the engine's own rule.
fn default_home() -> PathBuf {
    if let Some(home) = std::env::var_os("NURB_HOME") {
        return PathBuf::from(home);
    }
    let config = std::env::var_os("XDG_CONFIG_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            PathBuf::from(std::env::var_os("HOME").unwrap_or_default()).join(".config")
        });
    config.join("nurb")
}

/// A killed serve leaves serve.json behind, and another home's serve can take
/// the same port, so only a matching pid from /health proves this one is up.
fn alive(info: &ServeInfo) -> bool {
    health_pid(info.port) == Some(info.pid)
}

fn health_pid(port: u16) -> Option<u32> {
    let body = loopback_get(port, "/health").ok()?;
    let health: serde_json::Value = serde_json::from_str(&body).ok()?;
    health.get("pid")?.as_u64().map(|pid| pid as u32)
}

/// A minimal loopback GET. The serve always answers with Content-Length and
/// honours Connection: close, so read-to-end is the whole protocol.
fn loopback_get(port: u16, path: &str) -> Result<String, String> {
    let address = SocketAddr::from(([127, 0, 0, 1], port));
    let mut stream = TcpStream::connect_timeout(&address, HEALTH_TIMEOUT)
        .map_err(|e| format!("connect to the serve: {e}"))?;
    stream.set_read_timeout(Some(HEALTH_TIMEOUT)).ok();
    stream.set_write_timeout(Some(HEALTH_TIMEOUT)).ok();
    write!(
        stream,
        "GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\n\r\n"
    )
    .map_err(|e| format!("request: {e}"))?;
    let mut response = String::new();
    stream
        .read_to_string(&mut response)
        .map_err(|e| format!("response: {e}"))?;
    let (head, body) = response
        .split_once("\r\n\r\n")
        .ok_or("malformed response from the serve")?;
    let status = head.lines().next().unwrap_or_default();
    if !status.contains(" 200 ") {
        return Err(format!("the serve answered: {status}"));
    }
    Ok(body.to_string())
}

fn free_port() -> Result<u16, String> {
    for port in DEFAULT_PORT..DEFAULT_PORT + 40 {
        if TcpListener::bind(("127.0.0.1", port)).is_ok() {
            return Ok(port);
        }
    }
    Err("no free port between 7373 and 7412".into())
}

enum NotReady {
    /// The child died before publishing serve.json: a port race or a broken env.
    Exited(String),
    /// Still alive, just not ready yet.
    TimedOut,
}

impl NotReady {
    fn message(&self) -> String {
        match self {
            Self::Exited(reason) => reason.clone(),
            Self::TimedOut => format!(
                "the serve did not become ready within {}s",
                READY_TIMEOUT.as_secs()
            ),
        }
    }
}

fn exited(child: &ManagedChild) -> Option<ExitStatus> {
    child.state.lock().unwrap().process.try_wait().ok().flatten()
}

fn kill_tree(child: &ManagedChild) {
    let mut state = child.state.lock().unwrap();
    if state.stopped {
        return;
    }
    let pgid = state.process.id() as i32;
    unsafe {
        libc::killpg(pgid, libc::SIGTERM);
    }
    for _ in 0..20 {
        if matches!(state.process.try_wait(), Ok(Some(_))) {
            state.stopped = true;
            return;
        }
        thread::sleep(Duration::from_millis(100));
    }
    unsafe {
        libc::killpg(pgid, libc::SIGKILL);
    }
    let _ = state.process.wait();
    state.stopped = true;
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Command;

    fn supervisor() -> Supervisor {
        Supervisor::new(
            crate::env::Launcher::Checkout {
                repo: PathBuf::from("."),
            },
            PathBuf::from("/test/data"),
        )
    }

    #[test]
    fn the_remembered_port_wins_while_it_is_free() {
        let home = std::env::temp_dir().join(format!("nurb-supervisor-{}", std::process::id()));
        std::fs::create_dir_all(&home).unwrap();
        let supervisor = Supervisor {
            home: Some(home.clone()),
            ..supervisor()
        };
        let free = free_port().unwrap() + 5;
        std::fs::write(home.join("connect.json"), format!("{{\"token\": \"t\", \"port\": {free}}}")).unwrap();
        assert_eq!(supervisor.preferred_port().unwrap(), free);

        let held = TcpListener::bind(("127.0.0.1", free)).unwrap();
        assert_ne!(supervisor.preferred_port().unwrap(), free);
        drop(held);

        std::fs::write(home.join("connect.json"), "{\"token\": \"t\", \"port\": 99999}").unwrap();
        assert!(supervisor.preferred_port().is_ok());
        std::fs::remove_dir_all(&home).unwrap();
    }

    #[test]
    fn a_stale_serve_json_is_not_mistaken_for_a_live_serve() {
        let port = free_port().unwrap();
        let info = ServeInfo {
            url: format!("http://127.0.0.1:{port}"),
            port,
            pid: 1,
            token: "t".into(),
        };

        assert!(!alive(&info));
    }

    #[test]
    fn shutdown_kills_a_serve_that_is_still_starting() {
        let process = Command::new("sh")
            .args(["-c", "sleep 60"])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .process_group(0)
            .spawn()
            .unwrap();
        let child = Arc::new(ManagedChild {
            state: Mutex::new(ChildState {
                process,
                stopped: false,
            }),
        });
        let supervisor = supervisor();
        supervisor.state.lock().unwrap().phase = Phase::Starting(Some(Arc::clone(&child)));

        let started = Instant::now();
        supervisor.shutdown();

        assert!(started.elapsed() < Duration::from_secs(3));
        assert!(child.state.lock().unwrap().stopped);
    }
}
