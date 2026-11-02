//! The Claude driver: the user's own `claude` binary, run as one long-lived
//! child per chat session in print mode with stream-json on both pipes.
//!
//! No adapter sits in the middle, so the app owns the whole contract: the
//! nurb tools are handed to the CLI as an http MCP server pointed at the
//! serve, everything else is switched off, and the CLI's event lines map onto
//! the same ChatEvent channel the ACP agents use.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

use serde_json::Value;
use tauri::ipc::Channel;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin};
use tokio::sync::oneshot;

use crate::acp::events::{capped, mirror, ChatEvent};
use crate::acp::sandbox;
use crate::agents::AgentKind;
use crate::prefs::{ConfigChoice, ConfigRow, PrefStore};

/// The oldest CLI whose print mode waits for its MCP servers before the first
/// turn. Older ones can start turn 1 with no nurb tools at all.
const MINIMUM: (u32, u32, u32) = (2, 1, 221);

/// The models the picker offers. The CLI resolves an alias against the user's
/// plan, which is why there is no hardcoded model id here. Fable is the
/// suggestion: on nurb's own parts it holds one coherent form where Opus
/// builds a plinth and a cradle.
const MODELS: [(&str, &str); 4] = [
    ("default", "Default"),
    ("fable", "Fable"),
    ("opus", "Opus"),
    ("sonnet", "Sonnet"),
];

/// How hard the model thinks, the CLI's `--effort` levels. Default leaves the
/// flag off and lets the CLI decide.
const EFFORTS: [(&str, &str); 6] = [
    ("default", "Default"),
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("xhigh", "Extra high"),
    ("max", "Max"),
];

pub struct Drivers {
    sessions: Mutex<HashMap<String, Arc<Session>>>,
}

pub(crate) struct Session {
    pub(crate) project: PathBuf,
    pgid: i32,
    stdin: tokio::sync::Mutex<ChildStdin>,
    turn: Mutex<Option<oneshot::Sender<Result<String, String>>>>,
    /// Set by cancel, so the exit that follows reads as a stop, not a crash.
    stopped: AtomicBool,
}

impl Drivers {
    pub fn new() -> Self {
        Self {
            sessions: Mutex::new(HashMap::new()),
        }
    }

    pub(crate) fn get(&self, session_id: &str) -> Option<Arc<Session>> {
        self.sessions.lock().unwrap().get(session_id).cloned()
    }

    pub(crate) fn remove(&self, session_id: &str) {
        if let Some(session) = self.sessions.lock().unwrap().remove(session_id) {
            session.signal(libc::SIGTERM);
        }
    }

    /// Synchronous kill of every driver, for app exit where the async
    /// teardown may never run.
    pub fn shutdown(&self) {
        for session in std::mem::take(&mut *self.sessions.lock().unwrap()).values() {
            session.signal(libc::SIGTERM);
        }
    }
}

impl Session {
    fn signal(&self, signal: i32) {
        // A pgid of 0 would be the app's own group.
        if self.pgid > 0 {
            unsafe {
                libc::killpg(self.pgid, signal);
            }
        }
    }

    /// One user turn: the prompt goes in as a single stream-json line, and the
    /// turn ends when the CLI's `result` line arrives.
    pub(crate) async fn prompt(&self, content: Value) -> Result<String, String> {
        let (done, wait) = oneshot::channel();
        {
            let mut turn = self.turn.lock().unwrap();
            if turn.is_some() {
                return Err("Claude is still answering; wait for that to finish".into());
            }
            *turn = Some(done);
        }
        let line = serde_json::json!({
            "type": "user",
            "message": { "role": "user", "content": content },
        });
        self.write_line(line).await?;
        wait.await
            .map_err(|_| "Claude stopped unexpectedly".to_string())?
    }

    /// Switches the running child, so the picker never names a model this
    /// chat is not on. The CLI takes it between turns or mid-turn alike.
    pub(crate) async fn set_model(&self, model: &str) -> Result<(), String> {
        self.write_line(set_model_line(model)).await
    }

    async fn write_line(&self, line: Value) -> Result<(), String> {
        let mut stdin = self.stdin.lock().await;
        stdin
            .write_all(format!("{line}\n").as_bytes())
            .await
            .map_err(|e| format!("Claude stopped listening: {e}"))?;
        stdin
            .flush()
            .await
            .map_err(|e| format!("Claude stopped listening: {e}"))
    }

    /// SIGINT: measured on 2.1.272, the CLI answers with an
    /// `error_during_execution` result and exits, so a stop ends the child.
    /// The session itself survives on disk and the next message resumes it.
    pub(crate) fn cancel(&self) {
        self.stopped.store(true, Ordering::SeqCst);
        self.signal(libc::SIGINT);
    }
}

/// The CLI's own control request. "default" is an alias it understands, and
/// resets the child to the plan's default model.
pub(crate) fn set_model_line(model: &str) -> Value {
    serde_json::json!({
        "type": "control_request",
        "request_id": uuid::Uuid::new_v4().to_string(),
        "request": { "subtype": "set_model", "model": model },
    })
}

/// More text than this would crowd out the conversation it was attached to.
const TEXT_LIMIT: usize = 100 * 1024;

/// What one turn says: the user's words, then each file as a block the model
/// reads itself. Every built-in tool is off, so a link to a path would be a
/// file the CLI has no way to open.
pub(crate) fn user_content(text: String, attachments: &[String]) -> Result<Value, String> {
    if attachments.is_empty() {
        return Ok(Value::String(text));
    }
    let mut blocks = Vec::new();
    if !text.trim().is_empty() {
        blocks.push(serde_json::json!({ "type": "text", "text": text }));
    }
    for path in attachments {
        blocks.push(attachment_block(Path::new(path))?);
    }
    Ok(Value::Array(blocks))
}

fn attachment_block(path: &Path) -> Result<Value, String> {
    use base64::Engine;
    let encode = |data: Vec<u8>| base64::engine::general_purpose::STANDARD.encode(data);
    let name = crate::acp::attachment_name(path)?;
    if let Some((mime, data)) = crate::acp::attached_image(path, &name)? {
        return Ok(serde_json::json!({
            "type": "image",
            "source": { "type": "base64", "media_type": mime, "data": encode(data) },
        }));
    }
    let data = crate::acp::read_attachment(path, &name)?;
    if crate::acp::attachment_extension(path).as_deref() == Some("pdf") {
        return Ok(serde_json::json!({
            "type": "document",
            "title": name,
            "source": { "type": "base64", "media_type": "application/pdf", "data": encode(data) },
        }));
    }
    let text = String::from_utf8(data)
        .ok()
        .filter(|text| !text.contains('\0'))
        .ok_or_else(|| format!("Claude can't open {name}. It reads photos, PDFs and text files, so attach a screenshot of it instead."))?;
    if text.len() > TEXT_LIMIT {
        return Err(format!("{name} is too long to attach (over 100KB of text)"));
    }
    Ok(serde_json::json!({
        "type": "text",
        "text": format!("Attached file \"{name}\":\n\n{text}"),
    }))
}

/// What one stdout line means. Events go straight to the webview; the other
/// two drive the session's own state.
pub(crate) enum Signal {
    Event(ChatEvent),
    Init {
        session_id: String,
        tools_ready: bool,
        detail: String,
    },
    Result {
        stop: String,
        is_error: bool,
        text: String,
    },
}

/// The whole mapping from the CLI's stream-json to what the chat column
/// renders. Pure, so the shapes are testable against recorded lines.
pub(crate) fn map_line(line: &Value) -> Vec<Signal> {
    match line.get("type").and_then(Value::as_str) {
        Some("stream_event") => delta_signal(line.get("event")).into_iter().collect(),
        Some("assistant") => content_of(line)
            .iter()
            .filter_map(assistant_block)
            .map(Signal::Event)
            .collect(),
        Some("user") => content_of(line)
            .iter()
            .filter_map(tool_result)
            .map(Signal::Event)
            .collect(),
        Some("result") => vec![Signal::Result {
            stop: string_of(line, "stop_reason")
                .or_else(|| string_of(line, "subtype"))
                .unwrap_or_else(|| "end_turn".into()),
            is_error: line
                .get("is_error")
                .and_then(Value::as_bool)
                .unwrap_or(false),
            text: string_of(line, "result").unwrap_or_default(),
        }],
        Some("system") if line.get("subtype").and_then(Value::as_str) == Some("init") => {
            let servers = line
                .get("mcp_servers")
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default();
            let nurb = servers
                .iter()
                .find(|server| server.get("name").and_then(Value::as_str) == Some("nurb"));
            let status = nurb
                .and_then(|server| string_of(server, "status"))
                .unwrap_or_else(|| "missing".into());
            vec![Signal::Init {
                session_id: string_of(line, "session_id").unwrap_or_default(),
                tools_ready: matches!(status.as_str(), "connected" | "pending"),
                detail: status,
            }]
        }
        _ => Vec::new(),
    }
}

fn content_of(line: &Value) -> Vec<Value> {
    line.get("message")
        .and_then(|message| message.get("content"))
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default()
}

fn string_of(value: &Value, key: &str) -> Option<String> {
    value
        .get(key)
        .and_then(Value::as_str)
        .map(str::to_string)
        .filter(|text| !text.is_empty())
}

fn delta_signal(event: Option<&Value>) -> Option<Signal> {
    let event = event?;
    if event.get("type").and_then(Value::as_str) != Some("content_block_delta") {
        return None;
    }
    let delta = event.get("delta")?;
    match delta.get("type").and_then(Value::as_str) {
        Some("text_delta") => Some(Signal::Event(ChatEvent::AgentText {
            text: string_of(delta, "text")?,
        })),
        Some("thinking_delta") => Some(Signal::Event(ChatEvent::AgentThought {
            text: string_of(delta, "thinking")?,
        })),
        // input_json_delta: the tool_use block arrives complete later.
        _ => None,
    }
}

/// A finished assistant block. Text arrives twice (as deltas and then whole),
/// so the complete copy is sent as prose for the webview to swap in.
fn assistant_block(block: &Value) -> Option<ChatEvent> {
    match block.get("type").and_then(Value::as_str) {
        Some("text") => Some(ChatEvent::Prose {
            text: string_of(block, "text")?,
        }),
        Some("tool_use") => Some(ChatEvent::ToolCall {
            id: string_of(block, "id")?,
            title: string_of(block, "name")?
                .trim_start_matches("mcp__nurb__")
                .to_string(),
            kind: "nurb".into(),
            status: "in_progress".into(),
            input: block.get("input").and_then(|input| capped(input.to_string())),
            output: None,
            locations: Vec::new(),
        }),
        _ => None,
    }
}

fn tool_result(block: &Value) -> Option<ChatEvent> {
    if block.get("type").and_then(Value::as_str) != Some("tool_result") {
        return None;
    }
    let failed = block
        .get("is_error")
        .and_then(Value::as_bool)
        .unwrap_or(false);
    Some(ChatEvent::ToolCallUpdate {
        id: string_of(block, "tool_use_id")?,
        title: None,
        status: Some(if failed { "failed" } else { "completed" }.into()),
        input: None,
        output: capped(result_text(block.get("content"))),
        locations: Vec::new(),
    })
}

/// The text of a tool result. Renders are pictures the chat column does not
/// show, so they become a word rather than a wall of base64.
fn result_text(content: Option<&Value>) -> String {
    match content {
        Some(Value::String(text)) => text.clone(),
        Some(Value::Array(blocks)) => blocks
            .iter()
            .map(|block| match block.get("type").and_then(Value::as_str) {
                Some("image") => "[image]".to_string(),
                _ => string_of(block, "text").unwrap_or_default(),
            })
            .filter(|text| !text.is_empty())
            .collect::<Vec<_>>()
            .join("\n"),
        _ => String::new(),
    }
}

/// The argv after the binary. The tool switches are the whole security story:
/// every built-in tool off, only the nurb MCP server allowed.
pub(crate) fn spawn_args(
    mcp_url: &str,
    token: &str,
    project_id: &str,
    part: Option<&str>,
    model: Option<&str>,
    effort: Option<&str>,
    session: &str,
    resume: bool,
) -> Vec<String> {
    let mcp = serde_json::json!({
        "mcpServers": {
            "nurb": {
                "type": "http",
                "url": format!("{}/mcp", mcp_url.trim_end_matches('/')),
                "headers": { "Authorization": format!("Bearer {token}") },
            }
        }
    });
    let mut args: Vec<String> = [
        "-p",
        "--output-format",
        "stream-json",
        "--input-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--strict-mcp-config",
        "--mcp-config",
    ]
    .iter()
    .map(|arg| (*arg).to_string())
    .collect();
    args.push(mcp.to_string());
    args.extend(
        ["--tools", "", "--allowedTools", "mcp__nurb__*"]
            .iter()
            .map(|arg| (*arg).to_string()),
    );
    if let Some(model) = model.filter(|model| *model != "default") {
        args.push("--model".into());
        args.push(model.to_string());
    }
    if let Some(effort) = effort.filter(|effort| *effort != "default") {
        args.push("--effort".into());
        args.push(effort.to_string());
    }
    // The CLI says nothing, not even init, until the first prompt arrives on
    // stdin, so the session id is minted here and handed to it rather than
    // read back. A resume carries the id it was born with.
    args.push(if resume { "--resume" } else { "--session-id" }.into());
    args.push(session.to_string());
    // Each chat column belongs to one part, and the session is started per
    // column, so the part it is about rides in the prompt the session is born
    // with. The project-wide conversation names no part.
    let selected = match part.filter(|name| *name != crate::acp::PROJECT_CHAT) {
        Some(crate::acp::NEW_PART) => crate::acp::NEW_PART_CONTEXT.to_string(),
        Some(name) => format!(" This conversation is about the part \"{name}\", which is on screen beside the chat."),
        None => String::new(),
    };
    args.push("--append-system-prompt".into());
    args.push(format!(
        "You are inside the nurb desktop app, working on nurb project_id \"{project_id}\".{selected} \
         Everything goes through the nurb tools; there are no files to edit. \
         Call read_guide once before writing a part. \
         The user is a hobbyist with a 3D printer: plain words, no code and no file names unless asked."
    ));
    args
}

/// The child, under the same Seatbelt profile every agent runs in.
pub(crate) fn spawn(
    bin: &Path,
    args: Vec<String>,
    project: &Path,
    engine_root: &Path,
) -> Result<Child, String> {
    let (program, args) = sandbox::wrap(
        bin.to_string_lossy().into_owned(),
        args,
        project,
        engine_root,
    );
    tokio::process::Command::new(program)
        .args(args)
        .current_dir(project)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .process_group(0)
        .spawn()
        .map_err(|e| format!("could not start Claude: {e}"))
}

/// Installed, current enough, and signed in. All three are cheap, and each
/// error string is one the chat column knows how to explain.
fn ready_binary() -> Result<PathBuf, String> {
    let bin = AgentKind::Claude.native_bin().ok_or("claude_missing")?;
    let version = std::process::Command::new(&bin)
        .arg("--version")
        .output()
        .ok()
        .and_then(|out| String::from_utf8(out.stdout).ok())
        .ok_or("claude_missing")?;
    let version = version.split_whitespace().next().unwrap_or("").to_string();
    if !is_current(&version) {
        return Err(format!("claude_outdated: {version}"));
    }
    let signed_in = std::process::Command::new(&bin)
        .args(["auth", "status"])
        .output()
        .map(|out| out.status.success())
        .unwrap_or(false);
    if !signed_in {
        return Err("auth_required".into());
    }
    Ok(bin)
}

fn is_current(version: &str) -> bool {
    let mut parts = version.split('.').map(|part| part.parse::<u32>().ok());
    let found = (
        parts.next().flatten().unwrap_or(0),
        parts.next().flatten().unwrap_or(0),
        parts.next().flatten().unwrap_or(0),
    );
    found >= MINIMUM
}

pub(crate) async fn start(
    app: tauri::AppHandle,
    project: PathBuf,
    part: Option<String>,
    channel: Channel<ChatEvent>,
    resume: Option<String>,
) -> Result<String, String> {
    use tauri::Manager;
    let bin = ready_binary()?;
    let serve = {
        let app = app.clone();
        tauri::async_runtime::spawn_blocking(move || {
            app.state::<crate::supervisor::Supervisor>().ensure()
        })
        .await
        .map_err(|e| e.to_string())??
    };
    let chosen = app.state::<PrefStore>().chosen(AgentKind::Claude.id());
    let pick = |category: &str| {
        chosen
            .iter()
            .find(|(key, _)| key == category)
            .map(|(_, value)| value.clone())
    };
    let model = pick("model");
    let effort = pick("thought_level");
    let project_id = crate::acp::project_key(&project);
    let session_id = resume
        .clone()
        .unwrap_or_else(|| uuid::Uuid::new_v4().to_string());
    let args = spawn_args(
        &serve.url,
        &serve.token,
        &project_id,
        part.as_deref(),
        model.as_deref(),
        effort.as_deref(),
        &session_id,
        resume.is_some(),
    );
    let engine_root = app.state::<crate::env::Launcher>().engine_root();
    let mut child = spawn(&bin, args, &project, &engine_root)?;
    let pgid = child.id().unwrap_or_default() as i32;
    let stdin = child.stdin.take().ok_or("Claude has no input pipe")?;
    let stdout = child.stdout.take().ok_or("Claude has no output pipe")?;
    drain_stderr(child.stderr.take());

    let session = Arc::new(Session {
        project,
        pgid,
        stdin: tokio::sync::Mutex::new(stdin),
        turn: Mutex::new(None),
        stopped: AtomicBool::new(false),
    });
    app.state::<Drivers>()
        .sessions
        .lock()
        .unwrap()
        .insert(session_id.clone(), session.clone());
    tauri::async_runtime::spawn(read_stream(
        app.clone(),
        child,
        stdout,
        channel,
        session,
        session_id.clone(),
    ));
    Ok(session_id)
}

/// One session's stdout, start to grave: events to the webview, and every
/// turn resolved even when the process dies.
async fn read_stream(
    app: tauri::AppHandle,
    mut child: Child,
    stdout: tokio::process::ChildStdout,
    channel: Channel<ChatEvent>,
    session: Arc<Session>,
    session_id: String,
) {
    use tauri::Manager;
    // One session error per session: the column forgets the session on it.
    let mut reported = false;
    let mut lines = BufReader::new(stdout).lines();
    while let Ok(Some(line)) = lines.next_line().await {
        let Ok(value) = serde_json::from_str::<Value>(&line) else {
            continue;
        };
        for signal in map_line(&value) {
            match signal {
                Signal::Event(event) => send(&channel, event),
                Signal::Init {
                    session_id: id,
                    tools_ready,
                    detail,
                } => {
                    // The child is alive either way; a note says what it lacks.
                    if !tools_ready {
                        send(
                            &channel,
                            ChatEvent::Note {
                                text: format!("The nurb tools did not connect ({detail}). Claude can talk, but it cannot touch the project until they do."),
                            },
                        );
                    }
                    if id != session_id {
                        eprintln!("[claude] session {id} answered for {session_id}");
                    }
                }
                Signal::Result {
                    stop,
                    is_error,
                    text,
                } => {
                    // A failed turn leaves the child alive and waiting, so it
                    // is a note, not the end of the session. Being signed out
                    // is the exception: nothing more can happen in this child.
                    if is_error && looks_signed_out(&text) {
                        reported = true;
                        send(&channel, ChatEvent::SessionError { message: "auth_required".into() });
                        session.signal(libc::SIGTERM);
                    } else if is_error && !session.stopped.load(Ordering::SeqCst) {
                        let text = if text.is_empty() {
                            "Claude hit an error and stopped this turn.".to_string()
                        } else {
                            text
                        };
                        send(&channel, ChatEvent::Note { text });
                    }
                    finish(&session, Ok(stop));
                }
            }
        }
    }
    let code = child
        .wait()
        .await
        .ok()
        .and_then(|status| status.code())
        .unwrap_or(-1);
    // Every exit reaches the column, or a child that died before its first
    // turn leaves the column holding an id that answers nothing.
    let message = if session.stopped.load(Ordering::SeqCst) {
        "Stopped. The next message picks the conversation back up.".to_string()
    } else {
        format!("Claude stopped unexpectedly (exit {code})")
    };
    if !reported {
        send(&channel, ChatEvent::SessionError {
            message: message.clone(),
        });
    }
    finish(&session, Err(message));
    app.state::<Drivers>()
        .sessions
        .lock()
        .unwrap()
        .remove(&session_id);
}

fn send(channel: &Channel<ChatEvent>, event: ChatEvent) {
    mirror(&event);
    let _ = channel.send(event);
}

fn finish(session: &Session, outcome: Result<String, String>) {
    if let Some(turn) = session.turn.lock().unwrap().take() {
        let _ = turn.send(outcome);
    }
}

fn looks_signed_out(text: &str) -> bool {
    let text = text.to_ascii_lowercase();
    text.contains("invalid api key")
        || text.contains("/login")
        || text.contains("authentication method")
}

fn drain_stderr(stderr: Option<tokio::process::ChildStderr>) {
    let Some(stderr) = stderr else { return };
    tauri::async_runtime::spawn(async move {
        use std::io::Write;
        let mut lines = BufReader::new(stderr).lines();
        while let Ok(Some(line)) = lines.next_line().await {
            let _ = writeln!(std::io::stderr(), "[claude] {line}");
        }
    });
}

/// The driver's picker: the model and how hard it thinks, both passed at
/// spawn. A model pick also switches the running child; thinking waits for
/// the next session.
pub(crate) fn config_rows(prefs: &PrefStore) -> Vec<ConfigRow> {
    let chosen = prefs.chosen(AgentKind::Claude.id());
    let pick = |category: &str| {
        chosen
            .iter()
            .find(|(key, _)| key == category)
            .map(|(_, value)| value.clone())
            .unwrap_or_else(|| "default".into())
    };
    let row = |category: &str, name: &str, options: &[(&str, &str)], suggested: &str| ConfigRow {
        id: category.into(),
        category: category.into(),
        name: name.into(),
        value: pick(category),
        options: options
            .iter()
            .map(|(value, label)| ConfigChoice {
                value: (*value).into(),
                name: (*label).into(),
                description: (*value == suggested).then(|| "recommended".into()),
            })
            .collect(),
    };
    vec![
        row("model", "Model", &MODELS, "fable"),
        row("thought_level", "Thinking", &EFFORTS, "default"),
    ]
}

#[cfg(test)]
mod tests {
    use super::{is_current, map_line, set_model_line, spawn, spawn_args, user_content, Signal};
    use serde_json::Value;

    const STREAM: &str = include_str!("../tests/fixtures/claude-stream.jsonl");

    fn events(stream: &str) -> Vec<Value> {
        stream
            .lines()
            .filter(|line| !line.trim().is_empty())
            .flat_map(|line| map_line(&serde_json::from_str::<Value>(line).unwrap()))
            .map(|signal| match signal {
                Signal::Event(event) => serde_json::to_value(event).unwrap(),
                Signal::Init {
                    session_id,
                    tools_ready,
                    detail,
                } => serde_json::json!({ "type": "init", "id": session_id, "ready": tools_ready, "detail": detail }),
                Signal::Result { stop, is_error, .. } => {
                    serde_json::json!({ "type": "result", "stop": stop, "error": is_error })
                }
            })
            .collect()
    }

    #[test]
    fn the_stream_maps_onto_chat_events_in_order() {
        let mapped = events(STREAM);
        assert_eq!(mapped.len(), 6, "{mapped:#?}");
        assert_eq!(mapped[0]["type"], "init");
        assert_eq!(mapped[0]["ready"], true);
        assert_eq!(mapped[0]["id"], "01998e7a-1111-2222-3333-444455556666");
        assert_eq!(mapped[1]["type"], "agent_text");
        assert_eq!(mapped[1]["text"], "Making the shelf");
        // The complete block arrives as prose, not as a second agent_text.
        assert_eq!(mapped[2]["type"], "prose");
        assert_eq!(mapped[2]["text"], "Making the shelf taller.");
        assert_eq!(mapped[3]["type"], "tool_call");
        assert_eq!(mapped[3]["id"], "toolu_01");
        assert_eq!(mapped[3]["title"], "write_part_source");
        assert_eq!(mapped[3]["status"], "in_progress");
        assert_eq!(mapped[4]["type"], "tool_call_update");
        assert_eq!(mapped[4]["id"], "toolu_01");
        assert_eq!(mapped[4]["status"], "completed");
        assert_eq!(mapped[4]["output"], "built shelf in 1.2s\n[image]");
        assert_eq!(mapped[5]["type"], "result");
        assert_eq!(mapped[5]["stop"], "end_turn");
    }

    #[test]
    fn a_turn_carries_its_files_as_blocks_the_model_reads() {
        let dir = std::env::temp_dir().join(format!("nurb-claude-files-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let file = |name: &str, bytes: &[u8]| {
            let path = dir.join(name);
            std::fs::write(&path, bytes).unwrap();
            path.to_string_lossy().into_owned()
        };

        // No files is the plain turn it has always been.
        assert_eq!(user_content("taller".into(), &[]).unwrap(), Value::String("taller".into()));

        let sent = user_content(
            "fit this".into(),
            &[file("photo.PNG", b"pixels"), file("manual.pdf", b"%PDF-1.4"), file("notes.txt", b"lip is 3mm")],
        )
        .unwrap();
        let blocks = sent.as_array().unwrap();
        assert_eq!(blocks[0]["text"], "fit this");
        assert_eq!(blocks[1]["type"], "image");
        assert_eq!(blocks[1]["source"]["media_type"], "image/png");
        assert_eq!(blocks[1]["source"]["data"], "cGl4ZWxz");
        assert_eq!(blocks[2]["type"], "document");
        assert_eq!(blocks[2]["title"], "manual.pdf");
        assert_eq!(blocks[2]["source"]["media_type"], "application/pdf");
        assert_eq!(blocks[3]["type"], "text");
        assert!(blocks[3]["text"].as_str().unwrap().contains("notes.txt"));
        assert!(blocks[3]["text"].as_str().unwrap().contains("lip is 3mm"));

        // A photo alone is a message, and it stays a photo with no empty words.
        let alone = user_content("  ".into(), &[file("hook.jpg", b"pixels")]).unwrap();
        assert_eq!(alone.as_array().unwrap().len(), 1);
        assert_eq!(alone[0]["type"], "image");

        // What Claude has no way to read is refused by name, never dropped.
        let mesh = file("bracket.3mf", b"PK\x03\x04\xff\xfe");
        assert!(user_content("hi".into(), &[mesh]).unwrap_err().contains("bracket.3mf"));
        let long = file("huge.txt", &vec![b'a'; super::TEXT_LIMIT + 1]);
        assert!(user_content("hi".into(), &[long]).unwrap_err().contains("too long"));

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn the_cli_has_to_be_new_enough_to_wait_for_its_tools() {
        assert!(!is_current("2.1.220"));
        assert!(is_current("2.1.221"));
        assert!(is_current("2.2.0"));
        assert!(is_current("2.1.272"));
        assert!(!is_current("2.0.9"));
    }

    /// The shape 2.1.316 answers with a success and the new model on the
    /// next turn: issue #303, where the menu moved and the chat did not.
    #[test]
    fn a_model_pick_is_a_control_request_to_the_running_child() {
        let line = set_model_line("haiku");
        assert_eq!(line["type"], "control_request");
        assert_eq!(line["request"]["subtype"], "set_model");
        assert_eq!(line["request"]["model"], "haiku");
        assert!(line["request_id"].as_str().is_some_and(|id| !id.is_empty()));
        assert_ne!(line["request_id"], set_model_line("haiku")["request_id"]);
    }

    #[test]
    fn the_tools_are_the_nurb_server_and_nothing_else() {
        let args = spawn_args("http://127.0.0.1:7373", "secret", "box", Some("lip"), Some("opus"), Some("high"), "sid", false);
        let joined = args.join(" ");
        assert!(joined.contains("--strict-mcp-config"));
        assert!(joined.contains("http://127.0.0.1:7373/mcp"));
        assert!(joined.contains("Bearer secret"));
        assert!(joined.contains("--allowedTools mcp__nurb__*"));
        assert!(joined.contains("--model opus"));
        assert!(joined.contains("project_id \"box\""));
        assert!(joined.contains("the part \"lip\""));
        assert!(joined.contains("--session-id sid"));
        // The default alias is the CLI's own choice, so it is never passed.
        let default = spawn_args("http://x", "t", "box", None, Some("default"), Some("default"), "sid", true);
        assert!(!default.join(" ").contains("--model"));
        assert!(default.join(" ").contains("--resume sid"));
    }

    /// The spawn path end to end against a fake CLI: the sandbox wrapper, the
    /// stdin line, and the recorded stream back out as events.
    #[tokio::test]
    async fn a_turn_runs_against_a_fake_cli() {
        use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
        let dir = std::env::temp_dir().join(format!("nurb-claude-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let fixture = dir.join("stream.jsonl");
        std::fs::write(&fixture, STREAM).unwrap();
        let script = dir.join("claude");
        std::fs::write(
            &script,
            format!(
                "#!/bin/sh\ncase \"$1\" in\n--version) echo '2.1.272 (Claude Code)';;\nauth) exit 0;;\n*) read line; cat {};;\nesac\n",
                fixture.display()
            ),
        )
        .unwrap();
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            std::fs::set_permissions(&script, std::fs::Permissions::from_mode(0o755)).unwrap();
        }
        let args = spawn_args("http://127.0.0.1:7373", "t", "box", None, None, None, "sid", false);
        let mut child = spawn(&script, args, &dir, &dir).unwrap();
        let mut stdin = child.stdin.take().unwrap();
        stdin.write_all(b"{\"type\":\"user\"}\n").await.unwrap();
        stdin.flush().await.unwrap();
        let mut lines = BufReader::new(child.stdout.take().unwrap()).lines();
        let mut stream = String::new();
        while let Some(line) = lines.next_line().await.unwrap() {
            stream.push_str(&line);
            stream.push('\n');
        }
        let mapped = events(&stream);
        assert_eq!(mapped.len(), 6, "{mapped:#?}");
        assert_eq!(mapped[5]["stop"], "end_turn");
        std::fs::remove_dir_all(&dir).unwrap();
    }
}
