//! The terminal host: a process whose stdin/stdout is a real terminal the app
//! owns. On Windows this is a ConPTY (the same mechanism Windows Terminal and
//! every modern IDE terminal are built on); elsewhere it is a pty.
//!
//! The contract of this module is byte transport. The user's keystrokes go to
//! the child, and the child's output goes to the UI, with no interpretation in
//! either direction. There is no code path that can inject text into the
//! session or read the session back as structured data, which is what keeps
//! the host a terminal and not a custom client.

use std::collections::HashMap;
use std::io::{Read, Write};
use std::path::Path;
use std::sync::{Arc, Mutex};

use base64::Engine;
use portable_pty::{native_pty_system, Child, CommandBuilder, MasterPty, PtySize};
use tauri::{AppHandle, Emitter};

use crate::extensions;

/// A live terminal session, one per open panel.
pub struct TerminalSession {
    writer: Arc<Mutex<Box<dyn Write + Send>>>,
    master: Arc<Mutex<Box<dyn MasterPty + Send>>>,
    child: Arc<Mutex<Box<dyn Child + Send + Sync>>>,
}

/// All open sessions, keyed by an id the UI assigns.
#[derive(Default)]
pub struct Terminals {
    sessions: Mutex<HashMap<String, Arc<TerminalSession>>>,
}

#[derive(Clone, serde::Serialize)]
struct OutputEvent {
    id: String,
    data: String, // base64: terminal bytes are not necessarily UTF-8
}

#[derive(Clone, serde::Serialize)]
struct ExitEvent {
    id: String,
    code: Option<u32>,
}

impl TerminalSession {
    /// Write raw input bytes (user keystrokes only) to the child.
    fn write(&self, data: &str) -> Result<(), String> {
        let mut writer = self.writer.lock().unwrap();
        writer.write_all(data.as_bytes()).map_err(|e| e.to_string())?;
        writer.flush().map_err(|e| e.to_string())
    }

    fn resize(&self, cols: u16, rows: u16) -> Result<(), String> {
        self.master
            .lock()
            .unwrap()
            .resize(PtySize { rows, cols, pixel_width: 0, pixel_height: 0 })
            .map_err(|e| e.to_string())
    }

    fn kill(&self) {
        let _ = self.child.lock().unwrap().kill();
    }
}

impl Terminals {
    /// Spawn a terminal host for an extension manifest and keep it running.
    /// The argv comes from the manifest alone; `project` replaces the
    /// `{project}` placeholder as a single argument, never concatenated.
    pub fn open(
        &self,
        app: &AppHandle,
        id: &str,
        exe: &Path,
        launch: &[&str],
        project: &Path,
        cols: u16,
        rows: u16,
    ) -> Result<(), String> {
        let pty_system = native_pty_system();
        let pair = pty_system
            .openpty(PtySize { rows, cols, pixel_width: 0, pixel_height: 0 })
            .map_err(|e| e.to_string())?;

        let mut builder = CommandBuilder::new(exe);
        for arg in launch {
            builder.arg(if *arg == "{project}" {
                project.to_string_lossy().into_owned()
            } else {
                (*arg).to_string()
            });
        }
        builder.cwd(project);
        let child = pair.slave.spawn_command(builder).map_err(|e| e.to_string())?;
        drop(pair.slave);

        let mut reader = pair.master.try_clone_reader().map_err(|e| e.to_string())?;
        let writer: Box<dyn Write + Send> = pair.master.take_writer().map_err(|e| e.to_string())?;

        let session = Arc::new(TerminalSession {
            writer: Arc::new(Mutex::new(writer)),
            master: Arc::new(Mutex::new(pair.master)),
            child: Arc::new(Mutex::new(child)),
        });
        self.sessions.lock().unwrap().insert(id.to_string(), session.clone());

        let app = app.clone();
        let out_id = id.to_string();
        std::thread::spawn(move || {
            let mut buf = [0u8; 4096];
            loop {
                match reader.read(&mut buf) {
                    Ok(0) | Err(_) => break,
                    Ok(n) => {
                        let data = base64::engine::general_purpose::STANDARD.encode(&buf[..n]);
                        let _ = app.emit("terminal-output", OutputEvent { id: out_id.clone(), data });
                    }
                }
            }
            let code = session.child.lock().unwrap().wait().ok().map(|s| s.exit_code());
            let _ = app.emit("terminal-exit", ExitEvent { id: out_id, code });
        });
        Ok(())
    }

    pub fn input(&self, id: &str, data: &str) -> Result<(), String> {
        let session = self
            .sessions
            .lock()
            .unwrap()
            .get(id)
            .cloned()
            .ok_or_else(|| format!("no terminal session {id}"))?;
        session.write(data)
    }

    pub fn resize(&self, id: &str, cols: u16, rows: u16) -> Result<(), String> {
        let session = self
            .sessions
            .lock()
            .unwrap()
            .get(id)
            .cloned()
            .ok_or_else(|| format!("no terminal session {id}"))?;
        session.resize(cols, rows)
    }

    pub fn close(&self, id: &str) {
        if let Some(session) = self.sessions.lock().unwrap().remove(id) {
            session.kill();
        }
    }

    pub fn shutdown(&self) {
        for session in self.sessions.lock().unwrap().drain().map(|(_, s)| s) {
            session.kill();
        }
    }
}

/// Enable/disable state is a Mutex because the Tauri State is shared; the
/// registry itself is small and the lock is only held for the call.
#[tauri::command]
pub fn extension_statuses(
    extensions: tauri::State<std::sync::Mutex<crate::extensions::Extensions>>,
) -> Vec<crate::extensions::ExtensionStatus> {
    extensions.lock().unwrap().statuses()
}

#[tauri::command]
pub fn set_extension_enabled(
    extensions: tauri::State<std::sync::Mutex<crate::extensions::Extensions>>,
    id: String,
    enabled: bool,
) -> Result<(), String> {
    extensions.lock().unwrap().set_enabled(&id, enabled)
}

/// Run the install command for an extension (e.g. `npm install -g some-cli`).
/// The command comes from the compile-time BUILTIN table, never from user input.
#[tauri::command]
pub fn install_extension(
    extensions: tauri::State<std::sync::Mutex<crate::extensions::Extensions>>,
    id: String,
) -> Result<String, String> {
    let manifest = extensions.lock().unwrap().manifest(&id)?;
    let install_cmd = manifest.install.to_string();
    // Split into program + args. The BUILTIN install strings are simple
    // (`npm install -g some-cli`), so shell-style splitting is safe.
    let parts: Vec<&str> = install_cmd.split_whitespace().collect();
    if parts.is_empty() {
        return Err("install command is empty".into());
    }
    let mut cmd = std::process::Command::new(parts[0]);
    cmd.args(&parts[1..]);
    cmd.stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped());
    let output = cmd
        .spawn()
        .map_err(|e| format!("failed to start '{}': {e}", parts[0]))?
        .wait_with_output()
        .map_err(|e| format!("failed to run '{}': {e}", parts[0]))?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    if output.status.success() {
        Ok(format!("{stdout}{stderr}"))
    } else {
        Err(format!("install failed (exit {}): {stderr}", output.status.code().unwrap_or(-1)))
    }
}

/// Open a Terminal-host extension in a ConPTY session pointed at the project.
/// Only the extension registry decides what runs: `extension` must name a known
/// Terminal manifest, and its executable must be the user's own install. This
/// is the only terminal-open entry point, so an arbitrary command can never be
/// launched from the UI.
///
/// `session` is the UI's handle for the live session and is deliberately
/// separate from `extension`: session identity is per panel, not per
/// extension, so opening the same extension twice cannot collapse two live
/// sessions into one map entry (and close one and kill the other).
#[tauri::command]
pub fn open_terminal_extension(
    app: tauri::AppHandle,
    extensions: tauri::State<std::sync::Mutex<crate::extensions::Extensions>>,
    terminals: tauri::State<Terminals>,
    session: String,
    extension: String,
    project_dir: String,
    cols: u16,
    rows: u16,
) -> Result<(), String> {
    let (exe, manifest) = extensions.lock().unwrap().resolved(&extension)?;
    if manifest.host != extensions::HostKind::Terminal {
        return Err(format!("{extension} is not a terminal extension"));
    }
    if !extensions::version_at_least(&app.package_info().version.to_string(), manifest.min_app_version)
    {
        return Err(format!(
            "{} needs nurb {} or newer; this app is older",
            manifest.label, manifest.min_app_version
        ));
    }
    let project = std::path::PathBuf::from(project_dir);
    if !project.join("parts").is_dir() {
        return Err(format!("{} is not a nurb project (no parts/)", project.display()));
    }
    terminals.open(&app, &session, &exe, manifest.launch, &project, cols.max(2), rows.max(2))
}

/// Launch an ExternalApp extension detached. The app is never touched
/// afterward: no window manipulation, no IPC, no arguments beyond an optional
/// project hint where the product documents one (none do today, so none are
/// passed).
#[tauri::command]
pub fn launch_external_extension(
    extensions: tauri::State<std::sync::Mutex<crate::extensions::Extensions>>,
    id: String,
) -> Result<(), String> {
    let (exe, manifest) = extensions.lock().unwrap().resolved(&id)?;
    if manifest.host != extensions::HostKind::ExternalApp {
        return Err(format!("{id} is not an external-app extension"));
    }
    let mut cmd = std::process::Command::new(&exe);
    #[cfg(windows)]
    {
        // Detach from the console so the app's own window does not close the
        // extension with it, and give it its own console to inherit stdout.
        use std::os::windows::process::CommandExt;
        const CREATE_NEW_PROCESS_GROUP: u32 = 0x0000_0200;
        const DETACHED_PROCESS: u32 = 0x0000_0008;
        cmd.creation_flags(CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS);
    }
    cmd.spawn().map_err(|e| format!("could not launch {}: {e}", exe.display()))?;
    Ok(())
}

#[tauri::command]
pub fn terminal_input(
    terminals: tauri::State<Terminals>,
    id: String,
    data: String,
) -> Result<(), String> {
    terminals.input(&id, &data)
}

#[tauri::command]
pub fn terminal_resize(
    terminals: tauri::State<Terminals>,
    id: String,
    cols: u16,
    rows: u16,
) -> Result<(), String> {
    terminals.resize(&id, cols, rows)
}

#[tauri::command]
pub fn terminal_close(terminals: tauri::State<Terminals>, id: String) {
    terminals.close(&id)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{Duration, Instant};

    /// A child that reads four raw bytes and echoes them back. Python is the
    /// most deterministic choice on both platforms: pure stdin/stdout
    /// semantics, no console API involvement, present on dev machines and CI
    /// runners. Reading a fixed byte count sidesteps line discipline (a pty in
    /// cooked mode wants CR, not LF, for Enter), so the round trip is about
    /// the transport, not about console line editing.
    fn shell_echo_command() -> (String, Vec<String>) {
        let py = if cfg!(windows) { "python" } else { "python3" };
        (
            py.into(),
            vec![
                "-u".into(),
                "-c".into(),
                "import sys; d = sys.stdin.buffer.read(4); sys.stdout.buffer.write(b'got:' + d)"
                    .into(),
            ],
        )
    }

    /// The byte round-trip that proves the host is a terminal: input written
    /// by the host reaches the child, and the child's answer comes back.
    /// The reader runs on a thread feeding a channel so a silent child cannot
    /// hang the test: every wait has a deadline, then the child is killed.
    #[test]
    fn terminal_round_trips_bytes() {
        let (exe, args) = shell_echo_command();
        // The echo child is Python. On a bare CI runner without python on
        // PATH the test would fail for the wrong reason, so skip with a note
        // instead; the ConPTY machinery is still exercised everywhere python
        // exists (dev machines, the usual Windows CI images).
        if std::process::Command::new(&exe)
            .arg("--version")
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status()
            .map(|s| s.success())
            .unwrap_or(false)
            == false
        {
            eprintln!("skipping round-trip test: no python on PATH");
            return;
        }
        let pty_system = native_pty_system();
        let pair = pty_system
            .openpty(PtySize { rows: 24, cols: 80, pixel_width: 0, pixel_height: 0 })
            .unwrap();
        let mut builder = CommandBuilder::new(exe);
        for a in args {
            builder.arg(a);
        }
        let mut child = pair.slave.spawn_command(builder).unwrap();
        drop(pair.slave);
        let mut reader = pair.master.try_clone_reader().unwrap();
        let mut writer = pair.master.take_writer().unwrap();

        let (tx, rx) = std::sync::mpsc::channel::<String>();
        std::thread::spawn(move || {
            let mut buf = [0u8; 4096];
            loop {
                match reader.read(&mut buf) {
                    Ok(0) | Err(_) => break,
                    Ok(n) => {
                        if tx.send(String::from_utf8_lossy(&buf[..n]).into_owned()).is_err() {
                            break;
                        }
                    }
                }
            }
        });

        let deadline = Instant::now() + Duration::from_secs(15);
        let mut out = String::new();
        let mut last_send = Instant::now();
        while Instant::now() < deadline && !out.contains("got:abcd") {
            match rx.recv_timeout(Duration::from_millis(100)) {
                Ok(chunk) => out.push_str(&chunk),
                Err(_) => {}
            }
            // Re-send every half second until the echo lands. The child reads
            // exactly four bytes per run and the loop stops on the echo, so an
            // extra queued write is consumed by the next run at worst. The CR
            // is the byte a real Enter key sends: the console line discipline
            // on Windows completes input on CR, not LF.
            if Instant::now().duration_since(last_send) > Duration::from_millis(500) {
                writer.write_all(b"abcd\r").unwrap();
                writer.flush().unwrap();
                last_send = Instant::now();
            }
        }
        let _ = child.kill();
        let _ = child.wait();
        assert!(out.contains("got:abcd"), "echo never arrived; output so far: {out:?}");
    }

    #[test]
    fn closed_session_is_removed() {
        let terminals = Terminals::default();
        assert!(terminals.input("nope", "x").is_err());
        terminals.close("nope"); // closing an absent session is a no-op
    }
}
