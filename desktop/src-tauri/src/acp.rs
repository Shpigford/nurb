//! The chat column's ACP client: one agent adapter process per chat session
//! (Claude Code or Codex, see agents.rs), spoken to over stdio JSON-RPC,
//! streaming updates to the webview through a Tauri ipc channel.

mod approvals;
mod events;
mod policy;
mod sandbox;

pub use approvals::Approvals;

use std::collections::HashMap;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use agent_client_protocol::schema::v1::ErrorCode;
use agent_client_protocol::schema::v1::{
    AuthenticateRequest, CancelNotification, ContentBlock, ImageContent, InitializeRequest,
    ListSessionsRequest, LoadSessionRequest, Meta, NewSessionRequest, PromptRequest,
    RequestPermissionOutcome, RequestPermissionRequest, RequestPermissionResponse, ResourceLink,
    SelectedPermissionOutcome, SessionConfigKind, SessionConfigOption, SessionConfigSelectOptions,
    SessionId, SessionNotification, SetSessionConfigOptionRequest, TextContent,
};
use agent_client_protocol::schema::ProtocolVersion;
use agent_client_protocol::{
    AcpAgent, AcpAgentConfig, Agent, ByteStreams, Client, ConnectionTo, JsonRpcMessage,
    JsonRpcRequest, UntypedMessage,
};
use serde::{Deserialize, Serialize};
use tauri::ipc::Channel;
use tokio::sync::oneshot;

use crate::agents::AgentKind;
pub async fn authenticate(
    app: tauri::AppHandle,
    kind: AgentKind,
    method: &str,
    api_key: Option<&str>,
) -> Result<(), String> {
    use tauri::Manager;
    let launcher = app.state::<crate::env::Launcher>();
    let (program, args) = launcher.adapter(kind);
    let mut config = AcpAgentConfig::new(program).args(args);
    if kind == AgentKind::Gemini {
        for name in [
            "BROWSER",
            "CI",
            "DEBIAN_FRONTEND",
            "NO_BROWSER",
            "SSH_CONNECTION",
        ] {
            config = config.env(name, "");
        }
    }
    if let Some(path) = launcher.adapter_path() {
        config = config.env("PATH", path);
    }
    if let Some(key) = api_key {
        config = config.env("GEMINI_API_KEY", key);
    }
    let agent = AcpAgent::new(config);
    let (stdin, stdout, stderr, mut child) = agent.spawn_process().map_err(|e| e.to_string())?;
    drain_stderr(kind, stderr);
    let method = method.to_string();
    let login = Client.builder().connect_with(
        ByteStreams::new(stdin, stdout),
        move |cx: ConnectionTo<Agent>| async move {
            cx.send_request(InitializeRequest::new(ProtocolVersion::V1))
                .block_task()
                .await?;
            cx.send_request(AuthenticateRequest::new(method))
                .block_task()
                .await?;
            Ok(())
        },
    );
    let result = match tokio::time::timeout(Duration::from_secs(600), login).await {
        Ok(result) => result.map_err(|e| friendly(kind, e)),
        Err(_) => Err("The sign-in timed out. Try again.".into()),
    };
    let _ = child.kill();
    result
}

use crate::prefs::{ConfigChoice, ConfigRow, PrefStore};
pub(crate) use events::ChatEvent;
use events::{forward, permission_choice, permission_title, wire_string};

/// The whole-project conversation rides the per-part session plumbing under a
/// name no part file can have. The twin constant lives in desktop/src/Chat.tsx.
const PROJECT_CHAT: &str = "//project";

type Pending = Arc<Mutex<HashMap<u32, oneshot::Sender<RequestPermissionOutcome>>>>;

pub struct Chats {
    sessions: Mutex<HashMap<String, ChatSession>>,
}

struct ChatSession {
    conn: ConnectionTo<Agent>,
    session: SessionId,
    project: PathBuf,
    agent: AgentKind,
    pending: Pending,
    channel: Channel<ChatEvent>,
    /// The model and effort this session is actually running on, as the agent
    /// last reported them.
    config: Mutex<Vec<ConfigRow>>,
    /// Per-model effort menus from Grok's initialize `_meta.modelState`. Empty
    /// for agents that speak ACP config options. Needed because switching Grok's
    /// model rebuilds the effort list, and `session/set_model` does not return
    /// the new menus.
    grok_models: Vec<GrokModelMenu>,
    tree: crate::proc::ProcessTree,
    /// Dropped (with the whole entry) to end the connection task, which kills
    /// the adapter's process group.
    _close: oneshot::Sender<()>,
}

impl Chats {
    pub fn new() -> Self {
        Self {
            sessions: Mutex::new(HashMap::new()),
        }
    }

    /// Synchronous kill of every adapter, for app exit where the async
    /// teardown may never get to run.
    pub fn shutdown(&self) {
        let sessions = std::mem::take(&mut *self.sessions.lock().unwrap());
        for session in sessions.values() {
            session.tree.terminate();
        }
    }
}

#[tauri::command]
pub async fn start_chat(
    app: tauri::AppHandle,
    path: String,
    agent: String,
    on_event: Channel<ChatEvent>,
    resume: Option<String>,
) -> Result<String, String> {
    let kind = AgentKind::parse(&agent)?;
    let project = PathBuf::from(&path);
    if !project.is_dir() {
        return Err(format!("project folder missing: {}", project.display()));
    }
    let pending: Pending = Arc::new(Mutex::new(HashMap::new()));
    let (ready_tx, ready_rx) = oneshot::channel();
    let (close_tx, close_rx) = oneshot::channel();
    tauri::async_runtime::spawn(run_chat(
        app.clone(),
        project.clone(),
        kind,
        resume,
        on_event.clone(),
        pending.clone(),
        ready_tx,
        close_tx,
        close_rx,
    ));
    ready_rx
        .await
        .map_err(|_| format!("{} exited before it was ready", kind.label()))?
        .map_err(|error| friendly(kind, error))
}

#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionEntry {
    id: String,
    title: Option<String>,
    updated_at: Option<String>,
    part: Option<String>,
    agent: &'static str,
}

/// The chat history for one project's rail: per agent, a short-lived adapter
/// answers `session/list` and dies. Not polled; the rail refreshes itself
/// from live chat events. One agent failing (Codex errors -32000 here when
/// signed out; Claude's is a local read that works signed out) must not hide
/// the other's history, so failures degrade to an empty list.
#[tauri::command]
pub async fn list_sessions(
    app: tauri::AppHandle,
    path: String,
) -> Result<Vec<SessionEntry>, String> {
    use tauri::Manager;
    let project = PathBuf::from(&path);
    let launcher = app.state::<crate::env::Launcher>().inner().clone();
    // Every agent in parallel, skipping the native CLIs that are not on this
    // machine: spawning those just to watch them fail is noise, where the
    // adapters (always present once provisioned) fail informatively.
    let checks: Vec<_> = crate::agents::ALL
        .into_iter()
        .filter(|kind| kind.native_command().is_none() || launcher.adapter_available(*kind))
        .map(|kind| {
            let launcher = launcher.clone();
            let project = project.clone();
            (
                kind,
                tauri::async_runtime::spawn(async move {
                    agent_sessions(&launcher, kind, project).await
                }),
            )
        })
        .collect();
    let mut sessions = Vec::new();
    let mut configured = false;
    for (kind, check) in checks {
        let listed = check
            .await
            .unwrap_or_else(|error| Err(format!("session list task died: {error}")));
        match listed {
            Ok((list, config, model_rows)) => {
                configured |= !config.is_empty();
                app.state::<PrefStore>().cache(kind.id(), config);
                if kind == AgentKind::Grok {
                    app.state::<PrefStore>()
                        .cache_model_rows(kind.id(), model_rows);
                }
                sessions.extend(list.into_iter().map(|session| (kind, session)))
            }
            Err(error) => {
                let _ = writeln!(
                    std::io::stderr(),
                    "[acp:{}] session list unavailable: {error}",
                    kind.id()
                );
            }
        }
    }
    // Chat columns mount before this returns, so tell the ones already on
    // screen that their picker has lists now.
    if configured {
        use tauri::Emitter;
        let _ = app.emit("agent-config", ());
    }
    // Newest first; ISO 8601 sorts lexicographically, absent timestamps sink.
    sessions.sort_by(|a, b| b.1.updated_at.cmp(&a.1.updated_at));
    let store = app.state::<crate::sessions::SessionStore>();
    Ok(sessions
        .into_iter()
        .map(|(kind, session)| {
            let id = wire_string(&session.session_id);
            let part = store.part_of(&id, &project);
            SessionEntry {
                id,
                title: session.title,
                updated_at: session.updated_at,
                part,
                agent: kind.id(),
            }
        })
        .collect())
}

/// One agent's sessions for one project, plus the lists its model picker
/// draws. Pagination first: codex-acp can answer a cwd-filtered page as empty
/// while `nextCursor` still points at more, so an empty page never means done,
/// only an absent cursor does.
async fn agent_sessions(
    launcher: &crate::env::Launcher,
    kind: AgentKind,
    project: PathBuf,
) -> Result<
    (
        Vec<agent_client_protocol::schema::v1::SessionInfo>,
        Vec<ConfigRow>,
        HashMap<String, Vec<ConfigRow>>,
    ),
    String,
> {
    let (program, args) = launcher.adapter(kind);
    let (program, args) = sandbox::wrap(program, args, &project, &launcher.engine_root());
    let mut config = AcpAgentConfig::new(program).args(args);
    if let Some(path) = launcher.adapter_path() {
        config = config.env("PATH", path);
    }
    if kind == AgentKind::Gemini {
        if let Ok(key) = crate::agents::gemini_api_key() {
            config = config.env("GEMINI_API_KEY", key);
        }
    }
    let agent = AcpAgent::new(config);
    let (stdin, stdout, stderr, child) = agent
        .spawn_process()
        .map_err(|error| friendly(kind, error))?;
    let tree = crate::proc::ProcessTree::attach_pid_owned(child.id());
    drain_stderr(kind, stderr);
    let listed = tokio::time::timeout(
        Duration::from_secs(60),
        Client
            .builder()
            .on_receive_notification(
                async move |_: SessionNotification, _cx| Ok(()),
                agent_client_protocol::on_receive_notification!(),
            )
            .connect_with(
                ByteStreams::new(stdin, stdout),
                move |cx: ConnectionTo<Agent>| async move {
                    let init = cx
                        .send_request(InitializeRequest::new(ProtocolVersion::V1))
                        .block_task()
                        .await?;
                    let menus = grok_model_menus(init.meta.as_ref()).unwrap_or_default();
                    let model_rows = grok_rows_by_model(&menus);
                    // Only a session knows what models the agent offers, and a
                    // part's chat has no session until its first message. This
                    // adapter is already up and paying for its own startup, and
                    // a session that is never prompted writes no transcript, so
                    // asking here is what lets the very first chat of a fresh
                    // install open with a working picker. Failure (a signed-out
                    // Codex answers -32000) just means no picker.
                    let config = cx
                        .send_request(NewSessionRequest::new(project.clone()))
                        .block_task()
                        .await
                        .map(|session| {
                            picker_rows(
                                &session.config_options.unwrap_or_default(),
                                session.meta.as_ref(),
                                init.meta.as_ref(),
                            )
                        })
                        .unwrap_or_else(|_| grok_rows(None, init.meta.as_ref()));
                    if init.agent_capabilities.session_capabilities.list.is_none() {
                        return Ok((Vec::new(), config, model_rows));
                    }
                    let mut sessions = Vec::new();
                    let mut cursor: Option<String> = None;
                    for _ in 0..20 {
                        let mut request = ListSessionsRequest::new().cwd(project.clone());
                        request.cursor = cursor;
                        let response = cx.send_request(request).block_task().await?;
                        sessions.extend(response.sessions);
                        cursor = response.next_cursor;
                        if cursor.is_none() {
                            break;
                        }
                    }
                    Ok((sessions, config, model_rows))
                },
            ),
    )
    .await;
    reap(tree, child).await;
    listed
        .map_err(|_| "timed out listing conversations".to_string())?
        .map_err(|error| friendly(kind, error))
}

#[tauri::command]
pub async fn send_prompt(
    app: tauri::AppHandle,
    session_id: String,
    text: String,
    part: Option<String>,
    attachments: Vec<String>,
) -> Result<String, String> {
    use tauri::Manager;
    let (conn, session, project, kind) = {
        let sessions = app.state::<Chats>();
        let sessions = sessions.sessions.lock().unwrap();
        let chat = sessions.get(&session_id).ok_or("chat is not running")?;
        (
            chat.conn.clone(),
            chat.session.clone(),
            chat.project.clone(),
            chat.agent,
        )
    };
    // Remember which part was on screen for this session, so reopening it
    // later can restore the viewer.
    app.state::<crate::sessions::SessionStore>().record(
        &session_id,
        kind.id(),
        &project,
        part.clone(),
    );
    // Each chat column belongs to one part, and that identity travels with
    // every turn, so "make the lip taller" lands on the right part. The
    // server's real address matters too: without it the agent probes with
    // lsof and can find another project's server (seen live: it told the
    // user the wrong port). The audience line shapes the replies: the app's
    // users are hobbyists, and phrasing like "parts/lid.py:5" in an answer
    // is the file system leaking into a product that promises not to have
    // one.
    let project_name = project
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_else(|| project.display().to_string());
    let server = app
        .state::<crate::supervisor::Supervisor>()
        .port(&project)
        .map(|port| {
            format!(
                " This project's nurb dev server is already running at http://127.0.0.1:{port} and its viewer is on screen beside this chat; never start another one."
            )
        })
        .unwrap_or_default();
    let selected = match part.as_deref() {
        // The rail's project row; the twin constant lives in Chat.tsx.
        Some(PROJECT_CHAT) => " This conversation is about the whole project rather than one part. You can create parts with `nurb new`, edit any part, and lift design the parts share into system.py at the project root; the app notices new and rebuilt parts on its own.".to_string(),
        Some(part) => format!(" This conversation is about the part \"{part}\", which is on screen beside the chat."),
        None => String::new(),
    };
    let context = format!(
        "Context: nurb project \"{project_name}\".{selected}{server} \
        The user is a 3D-printing hobbyist, not a programmer, and the app hides all files and code: \
        in your replies, talk about the part, its features, and its dimensions in plain language, and \
        never mention file names, paths, line numbers, code, or Python. The viewer is built into this \
        app and already shows the part, so never mention server addresses, ports, or URLs, and never \
        tell the user to open one."
    );
    // User text first: the agent's session store titles a conversation from
    // its first user text, and that should be the user's words, not the
    // context block (seen live: the rail titled a chat "Context: nurb…").
    let mut blocks = Vec::new();
    if !text.trim().is_empty() {
        blocks.push(ContentBlock::Text(TextContent::new(text)));
    }
    for path in &attachments {
        blocks.push(attachment_block(std::path::Path::new(path))?);
    }
    blocks.push(ContentBlock::Text(TextContent::new(context)));
    let response = conn
        .send_request(PromptRequest::new(session, blocks))
        .block_task()
        .await;
    // A dialog still open when its turn resolves belongs to no turn now: the
    // UI clears it on its side, so answer it cancelled here too rather than
    // leaving the oneshot pending for the life of the session.
    {
        let sessions = app.state::<Chats>();
        let sessions = sessions.sessions.lock().unwrap();
        if let Some(chat) = sessions.get(&session_id) {
            let pending = std::mem::take(&mut *chat.pending.lock().unwrap());
            for (id, reply) in pending {
                let _ = reply.send(RequestPermissionOutcome::Cancelled);
                let _ = chat.channel.send(ChatEvent::PermissionResolved { id });
            }
        }
    }
    Ok(wire_string(
        &response.map_err(|error| friendly(kind, error))?.stop_reason,
    ))
}

/// Photos and sketches travel embedded, because that is what the prompt's
/// image capability carries; anything else (a mesh, a PDF) becomes a link the
/// agent reads from disk itself.
fn attachment_block(path: &std::path::Path) -> Result<ContentBlock, String> {
    let name = path
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .ok_or_else(|| format!("not a file: {}", path.display()))?;
    let mime = match path
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| e.to_ascii_lowercase())
        .as_deref()
    {
        Some("png") => Some("image/png"),
        Some("jpg") | Some("jpeg") => Some("image/jpeg"),
        Some("gif") => Some("image/gif"),
        Some("webp") => Some("image/webp"),
        _ => None,
    };
    let Some(mime) = mime else {
        return Ok(ContentBlock::ResourceLink(ResourceLink::new(
            name,
            file_uri(path),
        )));
    };
    let data = std::fs::read(path).map_err(|e| format!("cannot read {name}: {e}"))?;
    if data.len() > 10 * 1024 * 1024 {
        return Err(format!("{name} is too large to attach (over 10MB)"));
    }
    use base64::Engine;
    Ok(ContentBlock::Image(ImageContent::new(
        base64::engine::general_purpose::STANDARD.encode(data),
        mime,
    )))
}

/// A file:// URI the agent can read back. Windows paths need their
/// backslashes folded and an extra slash before the drive letter
/// (file:///C:/...); unix paths already start with the slash.
fn file_uri(path: &std::path::Path) -> String {
    let text = path.display().to_string().replace('\\', "/");
    if text.starts_with('/') {
        format!("file://{text}")
    } else {
        format!("file:///{text}")
    }
}

#[tauri::command]
pub fn cancel_turn(app: tauri::AppHandle, session_id: String) -> Result<(), String> {
    use tauri::Manager;
    let sessions = app.state::<Chats>();
    let sessions = sessions.sessions.lock().unwrap();
    let chat = sessions.get(&session_id).ok_or("chat is not running")?;
    // Any permission dialog still open belongs to the cancelled turn: answer
    // it cancelled and tell the UI to drop it.
    let pending = std::mem::take(&mut *chat.pending.lock().unwrap());
    for (id, reply) in pending {
        let _ = reply.send(RequestPermissionOutcome::Cancelled);
        let _ = chat.channel.send(ChatEvent::PermissionResolved { id });
    }
    chat.conn
        .send_notification(CancelNotification::new(chat.session.clone()))
        .map_err(|e| e.message)
}

#[tauri::command]
pub fn respond_permission(
    app: tauri::AppHandle,
    session_id: String,
    request_id: u32,
    option_id: String,
) -> Result<(), String> {
    use tauri::Manager;
    let sessions = app.state::<Chats>();
    let sessions = sessions.sessions.lock().unwrap();
    let chat = sessions.get(&session_id).ok_or("chat is not running")?;
    let reply = chat
        .pending
        .lock()
        .unwrap()
        .remove(&request_id)
        .ok_or("that permission request is no longer open")?;
    let _ = reply.send(RequestPermissionOutcome::Selected(
        SelectedPermissionOutcome::new(option_id),
    ));
    Ok(())
}

/// What the chat column needs to describe its own permission posture.
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ApprovalState {
    /// Whether the OS confines agent commands on this machine, straight from
    /// sandbox.rs. The UI's copy turns on this rather than on a user-agent
    /// sniff, so the shell cannot disagree with the kernel.
    confined: bool,
    /// Whether the app may answer permission requests itself in this project.
    auto: bool,
}

#[tauri::command]
pub fn approval_state(app: tauri::AppHandle, path: String) -> ApprovalState {
    use tauri::Manager;
    let approvals = app.state::<Approvals>();
    ApprovalState {
        confined: approvals.confined(),
        auto: approvals.auto(Path::new(&path)),
    }
}

#[tauri::command]
pub fn set_project_auto(app: tauri::AppHandle, path: String, auto: bool) {
    use tauri::{Emitter, Manager};
    app.state::<Approvals>().set(Path::new(&path), auto);
    // Every chat column open on this project mirrors the flag, the way the
    // picker lists mirror agent-config.
    let _ = app.emit("project-approvals", ());
}

/// Grok's per-model effort menu, taken from initialize `_meta.modelState`.
#[derive(Clone)]
struct GrokModelMenu {
    id: String,
    name: String,
    effort: String,
    efforts: Vec<ConfigChoice>,
}

/// `session/set_model` left ACP, but Grok still uses it to switch models and,
/// via `_meta.reasoningEffort`, thinking level. The typed schema has neither.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct SetSessionModelRequest {
    session_id: SessionId,
    model_id: String,
    #[serde(rename = "_meta", skip_serializing_if = "Option::is_none")]
    meta: Option<Meta>,
}

impl JsonRpcMessage for SetSessionModelRequest {
    fn matches_method(method: &str) -> bool {
        method == "session/set_model"
    }

    fn method(&self) -> &str {
        "session/set_model"
    }

    fn to_untyped_message(&self) -> Result<UntypedMessage, agent_client_protocol::Error> {
        UntypedMessage::new(self.method(), self)
    }

    fn parse_message(
        method: &str,
        params: &impl Serialize,
    ) -> Result<Self, agent_client_protocol::Error> {
        if !Self::matches_method(method) {
            return Err(agent_client_protocol::Error::method_not_found());
        }
        agent_client_protocol::util::json_cast(params)
    }
}

impl JsonRpcRequest for SetSessionModelRequest {
    type Response = serde_json::Value;
}

/// Prefers ACP config options. Grok advertises none, so the picker falls back
/// to its vendor `_meta`: live selection on `x.ai/sessionConfig`, menus on
/// initialize `modelState`.
fn picker_rows(
    options: &[SessionConfigOption],
    session_meta: Option<&Meta>,
    init_meta: Option<&Meta>,
) -> Vec<ConfigRow> {
    let from_acp = rows(options);
    if !from_acp.is_empty() {
        from_acp
    } else {
        grok_rows(session_meta, init_meta)
    }
}

fn grok_open_meta(kind: AgentKind, chosen: &[(String, String)]) -> Option<Meta> {
    if kind != AgentKind::Grok {
        return None;
    }
    let mut meta = Meta::new();
    for (category, value) in chosen {
        match category.as_str() {
            "model" => {
                meta.insert("modelId".into(), serde_json::Value::String(value.clone()));
            }
            "thought_level" => {
                meta.insert(
                    "reasoningEffort".into(),
                    serde_json::Value::String(value.clone()),
                );
            }
            _ => {}
        }
    }
    (!meta.is_empty()).then_some(meta)
}

fn grok_rows(session_meta: Option<&Meta>, init_meta: Option<&Meta>) -> Vec<ConfigRow> {
    let menus = grok_model_menus(init_meta);
    let selected = grok_session_selection(session_meta);
    if let Some(menus) = menus {
        let model_id = selected
            .as_ref()
            .and_then(|(model, _)| model.clone())
            .or_else(|| menus.first().map(|menu| menu.id.clone()));
        let Some(model_id) = model_id else {
            return Vec::new();
        };
        let effort = selected.as_ref().and_then(|(_, effort)| effort.clone());
        return grok_rows_from_menus(&menus, &model_id, effort.as_deref());
    }
    grok_rows_from_session_config(session_meta)
}

fn grok_rows_from_menus(
    menus: &[GrokModelMenu],
    model_id: &str,
    effort: Option<&str>,
) -> Vec<ConfigRow> {
    let Some(current) = menus
        .iter()
        .find(|menu| menu.id == model_id)
        .or_else(|| menus.first())
    else {
        return Vec::new();
    };
    let effort = effort
        .filter(|level| current.efforts.iter().any(|choice| choice.value == *level))
        .unwrap_or(current.effort.as_str());
    let mut rows = vec![ConfigRow {
        id: "model".into(),
        category: "model".into(),
        name: "Model".into(),
        value: current.id.clone(),
        options: menus
            .iter()
            .map(|menu| ConfigChoice {
                value: menu.id.clone(),
                name: menu.name.clone(),
                description: None,
            })
            .collect(),
    }];
    if !current.efforts.is_empty() {
        rows.push(thought_level_row(effort, &current.efforts));
    }
    rows
}

fn grok_rows_by_model(menus: &[GrokModelMenu]) -> HashMap<String, Vec<ConfigRow>> {
    menus
        .iter()
        .map(|menu| {
            (
                menu.id.clone(),
                grok_rows_from_menus(menus, &menu.id, Some(&menu.effort)),
            )
        })
        .collect()
}

fn thought_level_row(value: &str, options: &[ConfigChoice]) -> ConfigRow {
    ConfigRow {
        id: "thought_level".into(),
        category: "thought_level".into(),
        name: "Effort".into(),
        value: value.to_string(),
        options: options.to_vec(),
    }
}

fn grok_rows_from_session_config(meta: Option<&Meta>) -> Vec<ConfigRow> {
    let Some(options) = grok_session_options(meta) else {
        return Vec::new();
    };
    let mut rows = Vec::new();
    for (category, name) in [("model", "Model"), ("mode", "Effort")] {
        let choices: Vec<&GrokSessionOption> = options
            .iter()
            .filter(|option| option.category == category)
            .collect();
        if choices.is_empty() {
            continue;
        }
        let value = choices
            .iter()
            .find(|option| option.selected)
            .or_else(|| choices.first())
            .map(|option| option.id.clone())
            .unwrap_or_default();
        rows.push(ConfigRow {
            id: if category == "mode" {
                "thought_level"
            } else {
                "model"
            }
            .into(),
            category: if category == "mode" {
                "thought_level"
            } else {
                "model"
            }
            .into(),
            name: name.into(),
            value,
            options: choices
                .into_iter()
                .map(|option| ConfigChoice {
                    value: option.id.clone(),
                    name: option.label.clone(),
                    description: option.description.clone(),
                })
                .collect(),
        });
    }
    rows
}

fn grok_session_selection(meta: Option<&Meta>) -> Option<(Option<String>, Option<String>)> {
    let options = grok_session_options(meta)?;
    let model = options
        .iter()
        .find(|option| option.category == "model" && option.selected)
        .map(|option| option.id.clone());
    let effort = options
        .iter()
        .find(|option| option.category == "mode" && option.selected)
        .map(|option| option.id.clone());
    Some((model, effort))
}

fn grok_session_options(meta: Option<&Meta>) -> Option<Vec<GrokSessionOption>> {
    let config: GrokSessionConfig =
        serde_json::from_value(meta?.get("x.ai/sessionConfig")?.clone()).ok()?;
    Some(config.options)
}

fn grok_model_menus(meta: Option<&Meta>) -> Option<Vec<GrokModelMenu>> {
    let state: GrokModelState = serde_json::from_value(meta?.get("modelState")?.clone()).ok()?;
    let mut menus: Vec<GrokModelMenu> = state
        .available_models
        .into_iter()
        .map(|model| {
            let model_id = model.model_id;
            let details = model.meta.unwrap_or_default();
            let efforts: Vec<ConfigChoice> = details
                .reasoning_efforts
                .into_iter()
                .filter_map(|effort| {
                    let value = if !effort.value.is_empty() {
                        effort.value
                    } else {
                        effort.id
                    };
                    if value.is_empty() {
                        return None;
                    }
                    let name = if effort.label.is_empty() {
                        value.clone()
                    } else {
                        effort.label
                    };
                    Some(ConfigChoice {
                        value,
                        name,
                        description: effort.description,
                    })
                })
                .collect();
            let effort = details
                .reasoning_effort
                .filter(|level| efforts.iter().any(|choice| choice.value == *level))
                .or_else(|| efforts.first().map(|choice| choice.value.clone()))
                .unwrap_or_default();
            GrokModelMenu {
                id: model_id.clone(),
                name: if model.name.is_empty() {
                    model_id
                } else {
                    model.name
                },
                effort,
                efforts,
            }
        })
        .filter(|menu| !menu.id.is_empty())
        .collect();
    if menus.is_empty() {
        return None;
    }
    if let Some(index) = menus
        .iter()
        .position(|menu| menu.id == state.current_model_id)
    {
        menus.swap(0, index);
    }
    Some(menus)
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct GrokModelState {
    current_model_id: String,
    available_models: Vec<GrokAvailableModel>,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct GrokAvailableModel {
    model_id: String,
    #[serde(default)]
    name: String,
    #[serde(default, rename = "_meta")]
    meta: Option<GrokModelMeta>,
}

#[derive(Default, Deserialize)]
#[serde(rename_all = "camelCase")]
struct GrokModelMeta {
    #[serde(default)]
    reasoning_effort: Option<String>,
    #[serde(default)]
    reasoning_efforts: Vec<GrokEffortOption>,
}

#[derive(Deserialize)]
struct GrokEffortOption {
    #[serde(default)]
    id: String,
    #[serde(default)]
    value: String,
    #[serde(default)]
    label: String,
    #[serde(default)]
    description: Option<String>,
}

#[derive(Deserialize)]
struct GrokSessionConfig {
    #[serde(default)]
    options: Vec<GrokSessionOption>,
}

#[derive(Deserialize)]
struct GrokSessionOption {
    id: String,
    #[serde(default)]
    category: String,
    #[serde(default)]
    label: String,
    #[serde(default)]
    description: Option<String>,
    #[serde(default)]
    selected: bool,
}

fn with_grok_choice(
    mut rows: Vec<ConfigRow>,
    category: &str,
    value: &str,
    menus: &[GrokModelMenu],
) -> Vec<ConfigRow> {
    if category == "model" {
        if let Some(menu) = menus.iter().find(|menu| menu.id == value) {
            let current_effort = rows
                .iter()
                .find(|row| row.category == "thought_level")
                .map(|row| row.value.as_str());
            let effort = current_effort
                .filter(|level| menu.efforts.iter().any(|choice| choice.value == *level))
                .unwrap_or(menu.effort.as_str());
            return grok_rows_from_menus(menus, value, Some(effort));
        }
    }
    for row in &mut rows {
        if row.category == category {
            row.value = value.to_string();
        }
    }
    rows
}

async fn set_grok_choice(
    cx: &ConnectionTo<Agent>,
    session: &SessionId,
    category: &str,
    value: &str,
    current: &[ConfigRow],
    menus: &[GrokModelMenu],
) -> Result<Vec<ConfigRow>, agent_client_protocol::Error> {
    let model_id = if category == "model" {
        value.to_string()
    } else {
        current
            .iter()
            .find(|row| row.category == "model")
            .map(|row| row.value.clone())
            .or_else(|| menus.first().map(|menu| menu.id.clone()))
            .ok_or_else(agent_client_protocol::Error::internal_error)?
    };
    let effort = if category == "thought_level" {
        Some(value.to_string())
    } else {
        let wanted = current
            .iter()
            .find(|row| row.category == "thought_level")
            .map(|row| row.value.clone());
        match menus.iter().find(|menu| menu.id == model_id) {
            Some(menu)
                if wanted.as_ref().is_some_and(|level| {
                    menu.efforts.iter().any(|choice| choice.value == *level)
                }) =>
            {
                wanted
            }
            Some(menu) if !menu.effort.is_empty() => Some(menu.effort.clone()),
            _ => wanted,
        }
    };
    let mut meta = Meta::new();
    if let Some(effort) = effort {
        meta.insert("reasoningEffort".into(), serde_json::Value::String(effort));
    }
    cx.send_request(SetSessionModelRequest {
        session_id: session.clone(),
        model_id,
        meta: (!meta.is_empty()).then_some(meta),
    })
    .block_task()
    .await?;
    Ok(with_grok_choice(current.to_vec(), category, value, menus))
}

/// ACP's config options, narrowed to the two the picker draws and put in the
/// order they are applied. Matched on category rather than option id, because
/// the ids differ per agent (Claude's `effort` is Codex's `reasoning_effort`).
/// Anything that is not a select is dropped rather than half-rendered.
fn rows(options: &[SessionConfigOption]) -> Vec<ConfigRow> {
    crate::prefs::SHOWN
        .iter()
        .filter_map(|category| {
            let option = options.iter().find(|o| {
                o.category
                    .as_ref()
                    .is_some_and(|c| wire_string(c) == *category)
            })?;
            let SessionConfigKind::Select(select) = &option.kind else {
                return None;
            };
            let choices = match &select.options {
                SessionConfigSelectOptions::Ungrouped(list) => list.clone(),
                SessionConfigSelectOptions::Grouped(groups) => {
                    groups.iter().flat_map(|g| g.options.clone()).collect()
                }
                // The enum is non_exhaustive; a shape we cannot draw is no list.
                _ => Vec::new(),
            };
            Some(ConfigRow {
                id: wire_string(&option.id),
                category: (*category).to_string(),
                name: option.name.clone(),
                value: wire_string(&select.current_value),
                options: choices
                    .into_iter()
                    .map(|choice| ConfigChoice {
                        value: wire_string(&choice.value),
                        name: choice.name,
                        description: choice.description,
                    })
                    .collect(),
            })
        })
        .collect()
}

/// Put the user's remembered picks onto a session the moment it exists, before
/// the first prompt can go out on the wrong model. A pick the agent no longer
/// offers (a model dropped from an account's allowlist) is skipped, leaving the
/// agent's own default in place.
async fn apply_choices(
    cx: &ConnectionTo<Agent>,
    session: &SessionId,
    mut current: Vec<ConfigRow>,
    chosen: Vec<(String, String)>,
    kind: AgentKind,
    menus: &[GrokModelMenu],
) -> Vec<ConfigRow> {
    for (category, value) in chosen {
        // The pick is stored by category; this session's own id for it comes
        // from the list the agent just handed us.
        let Some(id) = current
            .iter()
            .find(|row| {
                row.category == category
                    && row.value != value
                    && row.options.iter().any(|choice| choice.value == value)
            })
            .map(|row| row.id.clone())
        else {
            continue;
        };
        if kind == AgentKind::Grok {
            match set_grok_choice(cx, session, &category, &value, &current, menus).await {
                Ok(updated) => current = updated,
                Err(error) => {
                    let _ = writeln!(
                        std::io::stderr(),
                        "[chat-config] could not set {category}={value}: {}",
                        error.message
                    );
                }
            }
            continue;
        }
        match cx
            .send_request(SetSessionConfigOptionRequest::new(
                session.clone(),
                id.clone(),
                value.as_str(),
            ))
            .block_task()
            .await
        {
            // Setting the model rebuilds the effort list, so each answer
            // replaces the whole set rather than patching one row.
            Ok(response) => current = rows(&response.config_options),
            Err(error) => {
                let _ = writeln!(
                    std::io::stderr(),
                    "[chat-config] could not set {id}={value}: {}",
                    error.message
                );
            }
        }
    }
    current
}

/// What the picker draws. A part's chat has no adapter until its first message,
/// so with no session running this answers from the remembered lists.
#[tauri::command]
pub fn chat_config(
    app: tauri::AppHandle,
    agent: String,
    session_id: Option<String>,
) -> Result<Vec<ConfigRow>, String> {
    use tauri::Manager;
    let kind = AgentKind::parse(&agent)?;
    if let Some(id) = session_id {
        let sessions = app.state::<Chats>();
        let sessions = sessions.sessions.lock().unwrap();
        if let Some(chat) = sessions.get(&id) {
            return Ok(chat.config.lock().unwrap().clone());
        }
    }
    Ok(app.state::<PrefStore>().rows(kind.id()))
}

/// Remember a pick and, when a session is running, move it there now. The
/// choice is stored either way, so it still lands on the next session if this
/// chat has not started one yet. Addressed by category, since that is the key
/// the picker and the store share; the agent's own option id comes from the
/// live session's list.
#[tauri::command]
pub async fn set_chat_config(
    app: tauri::AppHandle,
    agent: String,
    session_id: Option<String>,
    category: String,
    value: String,
) -> Result<Vec<ConfigRow>, String> {
    use tauri::Manager;
    let kind = AgentKind::parse(&agent)?;
    app.state::<PrefStore>()
        .remember(kind.id(), &category, &value);
    let live = session_id.and_then(|id| {
        let sessions = app.state::<Chats>();
        let sessions = sessions.sessions.lock().unwrap();
        sessions.get(&id).and_then(|chat| {
            let current = chat.config.lock().unwrap().clone();
            let config_id = current
                .iter()
                .find(|row| row.category == category)
                .map(|row| row.id.clone())?;
            Some((
                id.clone(),
                chat.conn.clone(),
                chat.session.clone(),
                chat.agent,
                chat.grok_models.clone(),
                current,
                config_id,
            ))
        })
    });
    let Some((id, conn, session, agent_kind, menus, current, config_id)) = live else {
        return Ok(app.state::<PrefStore>().rows(kind.id()));
    };
    let updated = if agent_kind == AgentKind::Grok {
        set_grok_choice(&conn, &session, &category, &value, &current, &menus)
            .await
            .map_err(|error| friendly(kind, error))?
    } else {
        let response = conn
            .send_request(SetSessionConfigOptionRequest::new(
                session,
                config_id,
                value.as_str(),
            ))
            .block_task()
            .await
            .map_err(|error| friendly(kind, error))?;
        rows(&response.config_options)
    };
    app.state::<PrefStore>().cache(kind.id(), updated.clone());
    let sessions = app.state::<Chats>();
    let sessions = sessions.sessions.lock().unwrap();
    if let Some(chat) = sessions.get(&id) {
        *chat.config.lock().unwrap() = updated.clone();
    }
    Ok(updated)
}

#[tauri::command]
pub fn close_chat(app: tauri::AppHandle, session_id: String) {
    use tauri::Manager;
    // Dropping the entry drops the close sender; the connection task sees it,
    // returns, and kills the adapter's process group.
    app.state::<Chats>()
        .sessions
        .lock()
        .unwrap()
        .remove(&session_id);
}

type Ready = Result<String, agent_client_protocol::Error>;

/// Owns one adapter process and its connection, start to grave.
#[allow(clippy::too_many_arguments)]
async fn run_chat(
    app: tauri::AppHandle,
    project: PathBuf,
    kind: AgentKind,
    resume: Option<String>,
    channel: Channel<ChatEvent>,
    pending: Pending,
    ready_tx: oneshot::Sender<Ready>,
    close_tx: oneshot::Sender<()>,
    close_rx: oneshot::Receiver<()>,
) {
    use tauri::Manager;
    let launcher = app.state::<crate::env::Launcher>();
    let (program, args) = launcher.adapter(kind);
    let (program, args) = sandbox::wrap(program, args, &project, &launcher.engine_root());
    let mut config = AcpAgentConfig::new(program).args(args);
    if let Some(path) = launcher.adapter_path() {
        config = config.env("PATH", path);
    }
    if kind == AgentKind::Gemini {
        if let Ok(key) = crate::agents::gemini_api_key() {
            config = config.env("GEMINI_API_KEY", key);
        }
    }
    let agent = AcpAgent::new(config);
    let (stdin, stdout, stderr, child) = match agent.spawn_process() {
        Ok(spawned) => spawned,
        Err(error) => {
            let _ = ready_tx.send(Err(error));
            return;
        }
    };
    let tree = crate::proc::ProcessTree::attach_pid_owned(child.id());
    drain_stderr(kind, stderr);

    let counter = AtomicU32::new(1);
    // True only while a session/load replay streams; the dispatch loop runs
    // notification handlers to completion before routing the load response,
    // so flipping it around the request brackets exactly the replay.
    let replaying = Arc::new(AtomicBool::new(false));
    let notify_replaying = Arc::clone(&replaying);
    let notify_channel = channel.clone();
    let ask_channel = channel.clone();
    let ask_pending = pending.clone();
    // The handler cannot reach these through Chats, which is not populated
    // until after the connection is up, and it cannot snapshot the flag
    // either: the user flips it mid-turn by answering a live dialog.
    let ask_approvals = app.state::<Approvals>().inner().clone();
    let ask_project = project.clone();
    let live_session = Arc::new(Mutex::new(None));
    let ask_session = Arc::clone(&live_session);
    let connected_session = Arc::clone(&live_session);
    let chat_app = app.clone();
    let chat_project = project.clone();
    let chat_pending = pending.clone();
    let chat_channel = channel.clone();
    let session_tree = tree.clone();
    let mut ready_tx = Some(ready_tx);
    let mut close_tx = Some(close_tx);

    let result = Client
        .builder()
        .on_receive_notification(
            async move |notification: SessionNotification, _cx| {
                forward(
                    &notify_channel,
                    notification.update,
                    notify_replaying.load(Ordering::Relaxed),
                );
                Ok(())
            },
            agent_client_protocol::on_receive_notification!(),
        )
        .on_receive_request(
            async move |request: RequestPermissionRequest, responder, cx| {
                // The app answers yes for the user only where something other
                // than the user is keeping this turn honest: the OS sandbox
                // the adapter runs under (sandbox.rs), or the standing yes the
                // user gave this project (approvals.rs). Reads go through
                // either way, because the sandbox profile never constrained
                // them. Everything else reaches a dialog.
                let guarded = ask_approvals.auto(&ask_project);
                if let Some(option) = policy::auto_allow(&request, guarded) {
                    let _ = writeln!(
                        std::io::stderr(),
                        "[acp:{}] auto-allowed: {}",
                        kind.id(),
                        request.tool_call.fields.title.as_deref().unwrap_or("(untitled)")
                    );
                    return responder.respond(RequestPermissionResponse::new(
                        RequestPermissionOutcome::Selected(SelectedPermissionOutcome::new(option)),
                    ));
                }
                // The chat is registered one line after the session id lands,
                // both before the app is told the chat is ready, so no id here
                // means nothing on screen could answer a dialog yet. Refusing
                // beats hanging the adapter on a prompt nobody can see.
                if ask_session.lock().unwrap().is_none() {
                    return responder.respond(RequestPermissionResponse::new(
                        RequestPermissionOutcome::Cancelled,
                    ));
                }
                // What the policy saw, for tuning it against real requests.
                let fields = &request.tool_call.fields;
                let _ = writeln!(
                    std::io::stderr(),
                    "[acp:policy] dialog: kind={:?} locations={} raw_keys={:?}",
                    fields.kind,
                    fields.locations.as_ref().map_or(0, |l| l.len()),
                    fields
                        .raw_input
                        .as_ref()
                        .and_then(|v| v.as_object())
                        .map(|o| o.keys().cloned().collect::<Vec<_>>())
                        .unwrap_or_default()
                );
                let id = counter.fetch_add(1, Ordering::Relaxed);
                let (reply_tx, reply_rx) = oneshot::channel();
                ask_pending.lock().unwrap().insert(id, reply_tx);
                let ask = ChatEvent::PermissionRequest {
                    id,
                    title: permission_title(kind.label(), &request),
                    kind: fields.kind.as_ref().map(wire_string),
                    detail: events::permission_detail(&request),
                    options: request.options.iter().map(permission_choice).collect(),
                };
                events::mirror(&ask);
                let _ = ask_channel.send(ask);
                let done_pending = ask_pending.clone();
                // The dispatch loop must never wait on the UI, so the answer
                // is awaited on a spawned task and responded from there.
                // If the spawn fails the connection is already gone and there
                // is nobody left to answer.
                let _ = cx.spawn(async move {
                    let outcome = reply_rx
                        .await
                        .unwrap_or(RequestPermissionOutcome::Cancelled);
                    done_pending.lock().unwrap().remove(&id);
                    responder.respond(RequestPermissionResponse::new(outcome))
                });
                Ok(())
            },
            agent_client_protocol::on_receive_request!(),
        )
        .connect_with(
            ByteStreams::new(stdin, stdout),
            move |cx: ConnectionTo<Agent>| {
                let ready_tx = ready_tx.take().expect("main_fn runs once");
                let close_tx = close_tx.take().expect("main_fn runs once");
                let connected_session = Arc::clone(&connected_session);
                let load_replaying = Arc::clone(&replaying);
                let resume = resume.clone();
                let chat_app = chat_app.clone();
                let chat_project = chat_project.clone();
                let chat_pending = chat_pending.clone();
                let chat_channel = chat_channel.clone();
                async move {
                    let session = async {
                        let init = cx
                            .send_request(InitializeRequest::new(ProtocolVersion::V1))
                            .block_task()
                            .await?;
                        let menus = grok_model_menus(init.meta.as_ref()).unwrap_or_default();
                        let chosen = chat_app.state::<PrefStore>().chosen(kind.id());
                        let open_meta = grok_open_meta(kind, &chosen);
                        if let Some(id) = resume {
                            // Restore chain: session/load replays the whole
                            // transcript through the notification handler
                            // before its response resolves. If the agent
                            // cannot load (or errors), fall through to a new
                            // session with an honest note; session/resume is
                            // deliberately skipped, since without a local
                            // transcript cache it restores context but shows
                            // the user an empty conversation.
                            let restored = if init.agent_capabilities.load_session {
                                let requested = SessionId::new(id.clone());
                                load_replaying.store(true, Ordering::Relaxed);
                                let mut request =
                                    LoadSessionRequest::new(requested.clone(), project.clone());
                                if let Some(meta) = open_meta.clone() {
                                    request = request.meta(meta);
                                }
                                let loaded = cx.send_request(request).block_task().await;
                                load_replaying.store(false, Ordering::Relaxed);
                                loaded.map(|loaded| {
                                    (
                                        requested,
                                        picker_rows(
                                            &loaded.config_options.unwrap_or_default(),
                                            loaded.meta.as_ref(),
                                            init.meta.as_ref(),
                                        ),
                                    )
                                })
                            } else {
                                Err(agent_client_protocol::Error::method_not_found())
                            };
                            match restored {
                                Ok(session) => {
                                    let _ = writeln!(
                                        std::io::stderr(),
                                        "[chat-session] restore path: session/load ok ({id})"
                                    );
                                    return Ok((session.0, session.1, menus, chosen));
                                }
                                Err(error) => {
                                    let _ = writeln!(
                                        std::io::stderr(),
                                        "[chat-session] restore path: session/load failed ({}), starting fresh ({id})",
                                        error.message
                                    );
                                    let note = ChatEvent::Note {
                                        text: "Couldn't restore this conversation, so this is a fresh one."
                                            .into(),
                                    };
                                    events::mirror(&note);
                                    let _ = chat_channel.send(note);
                                }
                            }
                        }
                        let mut request = NewSessionRequest::new(project);
                        if let Some(meta) = open_meta {
                            request = request.meta(meta);
                        }
                        cx.send_request(request)
                            .block_task()
                            .await
                            .map(|new_session| {
                                (
                                    new_session.session_id,
                                    picker_rows(
                                        &new_session.config_options.unwrap_or_default(),
                                        new_session.meta.as_ref(),
                                        init.meta.as_ref(),
                                    ),
                                    menus,
                                    chosen,
                                )
                            })
                    }
                    .await;
                    let session_id = match session {
                        Ok((session, current, menus, chosen)) => {
                            // Before ready_tx: the picker's choice has to be on
                            // the session by the time the first prompt can go
                            // out, or the opening turn runs on the wrong model.
                            let config = apply_choices(
                                &cx,
                                &session,
                                current,
                                chosen,
                                kind,
                                &menus,
                            )
                            .await;
                            let prefs = chat_app.state::<PrefStore>();
                            prefs.cache(kind.id(), config.clone());
                            if kind == AgentKind::Grok {
                                prefs.cache_model_rows(kind.id(), grok_rows_by_model(&menus));
                            }
                            let id = wire_string(&session);
                            *connected_session.lock().unwrap() = Some(id.clone());
                            chat_app.state::<Chats>().sessions.lock().unwrap().insert(
                                id.clone(),
                                ChatSession {
                                    conn: cx.clone(),
                                    session,
                                    project: chat_project,
                                    agent: kind,
                                    pending: chat_pending,
                                    channel: chat_channel,
                                    config: Mutex::new(config),
                                    grok_models: menus,
                                    tree: session_tree.clone(),
                                    _close: close_tx,
                                },
                            );
                            if ready_tx.send(Ok(id.clone())).is_err() {
                                chat_app
                                    .state::<Chats>()
                                    .sessions
                                    .lock()
                                    .unwrap()
                                    .remove(&id);
                                return Ok(None);
                            }
                            id
                        }
                        Err(error) => {
                            let _ = ready_tx.send(Err(error));
                            return Ok(None);
                        }
                    };
                    tokio::select! {
                        // Ok or Err both mean the app closed this chat on purpose.
                        _ = close_rx => Ok(None),
                        // The adapter died underneath a live session.
                        _ = cx.incoming_closed() => Ok(Some(session_id)),
                    }
                }
            },
        )
        .await;

    // Whichever way the connection ended, take the process tree with it.
    reap(tree, child).await;

    if let Err(error) = &result {
        let _ = writeln!(
            std::io::stderr(),
            "[acp:{}] connection failed: {error:?}",
            kind.id()
        );
    }
    let live_session = live_session.lock().unwrap().clone();
    if let Some(session_id) = session_to_remove(&result, &live_session) {
        app.state::<Chats>()
            .sessions
            .lock()
            .unwrap()
            .remove(&session_id);
        let error = ChatEvent::SessionError {
            message: format!(
                "{} stopped unexpectedly. Send a message to start a fresh chat.",
                kind.label()
            ),
        };
        events::mirror(&error);
        let _ = channel.send(error);
    }
}

/// Clean UI closes return `Ok(None)`. Every other end state must identify the
/// session to evict, including transport errors that cannot return it normally.
pub(crate) fn session_to_remove(
    result: &Result<Option<String>, agent_client_protocol::Error>,
    live_session: &Option<String>,
) -> Option<String> {
    match result {
        Ok(session) => session.clone(),
        Err(_) => live_session.clone(),
    }
}

/// Terminate the adapter's process tree and reap the child, escalating to a
/// hard kill if it lingers.
async fn reap(tree: crate::proc::ProcessTree, mut child: async_process::Child) {
    tree.terminate();
    if tokio::time::timeout(Duration::from_secs(5), child.status())
        .await
        .is_err()
    {
        tree.kill();
        let _ = child.status().await;
    }
}

/// Adapter stderr is diagnostics; forward it, non-panicking (a broken stderr
/// after the dev harness dies must not kill anything).
fn drain_stderr(kind: AgentKind, stderr: async_process::ChildStderr) {
    tauri::async_runtime::spawn(async move {
        use futures_lite::io::{AsyncBufReadExt, BufReader};
        use futures_lite::stream::StreamExt;
        let mut lines = BufReader::new(stderr).lines();
        while let Some(Ok(line)) = lines.next().await {
            let _ = writeln!(std::io::stderr(), "[acp:{}] {line}", kind.id());
        }
    });
}

/// -32000 is ACP's auth-required code, so it means signed out for every
/// agent; they just raise it at different moments (Claude on session/prompt,
/// Codex as early as session/new or session/list). The `auth_required:`
/// prefix is the frontend's marker.
///
/// A token revoked or expired server-side never earns -32000: the local
/// credential store still looks signed in, so Claude wraps the API's 401 as
/// an internal error containing "Failed to authenticate" (the bundled CLI's
/// wording for both cases). Without matching the message the user gets a
/// dead-end note and no sign-in button (#115).
fn friendly(kind: AgentKind, error: agent_client_protocol::Error) -> String {
    if error.code == ErrorCode::AuthRequired || error.message.contains("Failed to authenticate") {
        format!(
            "auth_required: {} is not signed in on this computer",
            kind.label()
        )
    } else {
        format!("{} error: {}", kind.label(), error.message)
    }
}

#[cfg(test)]
mod tests {
    use super::{
        attachment_block, friendly, grok_open_meta, grok_rows, picker_rows, rows, with_grok_choice,
        AgentKind,
    };
    use agent_client_protocol::schema::v1::{ContentBlock, Meta, SessionConfigOption};

    /// The exact message a revoked token produces (#115): an internal error,
    /// not -32000, so only the message can route it to the sign-in button.
    #[test]
    fn revoked_token_reads_as_auth_required() {
        let error = agent_client_protocol::Error::new(
            -32603,
            "Internal error: Failed to authenticate. API Error: 401 OAuth access token has been revoked.",
        );
        assert!(friendly(AgentKind::Claude, error).starts_with("auth_required:"));
    }

    /// What claude-agent-acp 0.64.2 actually answers session/new with, captured
    /// off the wire. Mode, fast, and agent ride along and must not reach the
    /// picker.
    const CLAUDE: &str = r#"[
      {"id":"mode","name":"Mode","category":"mode","type":"select","currentValue":"default",
       "options":[{"value":"default","name":"Default"},{"value":"plan","name":"Plan"}]},
      {"id":"model","name":"Model","category":"model","type":"select","currentValue":"opus[1m]",
       "options":[{"value":"default","name":"Default (recommended)"},
                  {"value":"opus[1m]","name":"Opus (1M context)"},
                  {"value":"sonnet","name":"Sonnet"}]},
      {"id":"effort","name":"Effort","category":"thought_level","type":"select","currentValue":"xhigh",
       "options":[{"value":"default","name":"Default"},{"value":"low","name":"Low"},
                  {"value":"xhigh","name":"Xhigh"}]},
      {"id":"fast","name":"Fast mode","category":"model_config","type":"boolean","currentValue":false},
      {"id":"agent","name":"Agent","type":"select","currentValue":"default",
       "options":[{"value":"default","name":"Default"}]}
    ]"#;

    /// codex-acp 1.1.9's answer, also captured off the wire. It names effort
    /// `reasoning_effort` and adds a collaboration mode; only the shared
    /// categories may reach the picker.
    const CODEX: &str = r#"[
      {"id":"mode","name":"Mode","category":"mode","type":"select","currentValue":"agent",
       "options":[{"value":"read-only","name":"Read-only"},{"value":"agent","name":"Agent"}]},
      {"id":"collaboration_mode","name":"Collaboration mode","category":"collaboration_mode",
       "type":"select","currentValue":"default",
       "options":[{"value":"default","name":"Default"},{"value":"plan","name":"Plan"}]},
      {"id":"model","name":"Model","category":"model","type":"select","currentValue":"gpt-5.6-sol",
       "options":[{"value":"gpt-5.6-sol","name":"GPT-5.6-Sol"},{"value":"gpt-5.5","name":"GPT-5.5"}]},
      {"id":"reasoning_effort","name":"Reasoning effort","category":"thought_level","type":"select",
       "currentValue":"low",
       "options":[{"value":"low","name":"Low"},{"value":"high","name":"High"}]},
      {"id":"fast-mode","name":"Fast mode","category":"model_config","type":"select","currentValue":"off",
       "options":[{"value":"off","name":"Off"},{"value":"on","name":"On"}]}
    ]"#;

    #[test]
    fn the_picker_gets_model_then_effort_and_nothing_else() {
        let options: Vec<SessionConfigOption> = serde_json::from_str(CLAUDE).unwrap();
        let rows = rows(&options);

        let ids: Vec<&str> = rows.iter().map(|row| row.id.as_str()).collect();
        assert_eq!(ids, ["model", "effort"]);
        assert_eq!(rows[0].value, "opus[1m]");
        // Names, not wire ids: the button reads "Opus (1M context) · Xhigh".
        assert_eq!(rows[0].options[1].name, "Opus (1M context)");
        assert_eq!(rows[1].value, "xhigh");
        assert_eq!(rows[1].options.len(), 3);
    }

    /// The bug this replaced: matching on option id showed Codex nothing,
    /// because its effort option is called `reasoning_effort`.
    #[test]
    fn codex_gets_a_picker_too_under_its_own_option_names() {
        let options: Vec<SessionConfigOption> = serde_json::from_str(CODEX).unwrap();
        let rows = rows(&options);

        let ids: Vec<&str> = rows.iter().map(|row| row.id.as_str()).collect();
        assert_eq!(ids, ["model", "reasoning_effort"]);
        let categories: Vec<&str> = rows.iter().map(|row| row.category.as_str()).collect();
        assert_eq!(categories, ["model", "thought_level"]);
        assert_eq!(rows[1].name, "Reasoning effort");
        // Codex's fast mode is a select, not a boolean, so category is the only
        // thing keeping it out.
        assert!(!rows.iter().any(|row| row.id == "fast-mode"));
    }

    #[test]
    fn an_agent_that_offers_no_config_yields_no_picker() {
        assert!(rows(&[]).is_empty());
    }

    /// Grok 1.0.5's session/new, captured off the wire: no `configOptions`,
    /// effort advertised as vendor session-config category `mode`.
    const GROK_SESSION: &str = r#"{
      "x.ai/sessionConfig": {
        "options": [
          {"id":"grok-4.6","category":"model","label":"Grok 4.6","selected":true},
          {"id":"grok-4.5","category":"model","label":"Grok 4.5","selected":false},
          {"id":"xhigh","category":"mode","label":"Extra High Effort",
           "description":"Highest effort and reasoning level","selected":false},
          {"id":"high","category":"mode","label":"High Effort",
           "description":"Higher implementation quality with extensive reasoning","selected":true},
          {"id":"medium","category":"mode","label":"Medium Effort","selected":false},
          {"id":"low","category":"mode","label":"Low Effort","selected":false}
        ]
      }
    }"#;

    /// initialize `_meta.modelState` from the same CLI: per-model effort menus,
    /// including Extra High on 4.6 only.
    const GROK_INIT: &str = r#"{
      "modelState": {
        "currentModelId": "grok-4.6",
        "availableModels": [
          {
            "modelId": "grok-4.6",
            "name": "Grok 4.6",
            "_meta": {
              "supportsReasoningEffort": true,
              "reasoningEffort": "high",
              "reasoningEfforts": [
                {"id":"xhigh","value":"xhigh","label":"Extra High Effort"},
                {"id":"high","value":"high","label":"High Effort","default":true},
                {"id":"medium","value":"medium","label":"Medium Effort"},
                {"id":"low","value":"low","label":"Low Effort"}
              ]
            }
          },
          {
            "modelId": "grok-4.5",
            "name": "Grok 4.5",
            "_meta": {
              "supportsReasoningEffort": true,
              "reasoningEffort": "high",
              "reasoningEfforts": [
                {"id":"high","value":"high","label":"High Effort","default":true},
                {"id":"medium","value":"medium","label":"Medium Effort"},
                {"id":"low","value":"low","label":"Low Effort"}
              ]
            }
          }
        ]
      }
    }"#;

    fn grok_meta(json: &str) -> Meta {
        serde_json::from_str(json).unwrap()
    }

    #[test]
    fn grok_gets_a_picker_from_vendor_session_config() {
        let rows = grok_rows(Some(&grok_meta(GROK_SESSION)), None);
        let ids: Vec<&str> = rows.iter().map(|row| row.id.as_str()).collect();
        assert_eq!(ids, ["model", "thought_level"]);
        assert_eq!(rows[0].value, "grok-4.6");
        assert_eq!(rows[0].options[0].name, "Grok 4.6");
        assert_eq!(rows[1].value, "high");
        assert_eq!(rows[1].name, "Effort");
        assert_eq!(rows[1].options.len(), 4);
        assert_eq!(rows[1].options[0].name, "Extra High Effort");
    }

    #[test]
    fn grok_thinking_level_follows_the_current_models_menu() {
        let init = grok_meta(GROK_INIT);
        let session = grok_meta(GROK_SESSION);
        let rows = grok_rows(Some(&session), Some(&init));
        assert_eq!(rows[0].value, "grok-4.6");
        assert_eq!(rows[1].options.len(), 4);

        let menus = super::grok_model_menus(Some(&init)).unwrap();
        let switched = with_grok_choice(rows.clone(), "model", "grok-4.5", &menus);
        assert_eq!(switched[0].value, "grok-4.5");
        assert_eq!(switched[1].value, "high");
        assert_eq!(switched[1].options.len(), 3);
        assert!(!switched[1]
            .options
            .iter()
            .any(|choice| choice.value == "xhigh"));

        let xhigh = with_grok_choice(rows, "thought_level", "xhigh", &menus);
        let dropped = with_grok_choice(xhigh, "model", "grok-4.5", &menus);
        assert_eq!(dropped[1].value, "high");
    }

    /// The bug this replaced: matching only ACP `thought_level` config options
    /// showed Grok nothing, because it never advertises `configOptions`.
    #[test]
    fn grok_picker_does_not_need_acp_config_options() {
        let rows = picker_rows(
            &[],
            Some(&grok_meta(GROK_SESSION)),
            Some(&grok_meta(GROK_INIT)),
        );
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[1].category, "thought_level");
    }

    #[test]
    fn acp_config_options_still_win_over_grok_vendor_meta() {
        let options: Vec<SessionConfigOption> = serde_json::from_str(CLAUDE).unwrap();
        let rows = picker_rows(&options, Some(&grok_meta(GROK_SESSION)), None);
        assert_eq!(rows[0].value, "opus[1m]");
        assert_eq!(rows[1].id, "effort");
    }

    #[test]
    fn grok_open_meta_carries_model_and_effort() {
        let meta = grok_open_meta(
            AgentKind::Grok,
            &[
                ("model".into(), "grok-4.5".into()),
                ("thought_level".into(), "low".into()),
            ],
        )
        .unwrap();
        assert_eq!(meta["modelId"], "grok-4.5");
        assert_eq!(meta["reasoningEffort"], "low");
        assert!(grok_open_meta(AgentKind::Claude, &[("model".into(), "sonnet".into())]).is_none());
    }

    fn scratch(name: &str, bytes: &[u8]) -> std::path::PathBuf {
        let dir = std::env::temp_dir().join(format!("nurb-attach-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join(name);
        std::fs::write(&path, bytes).unwrap();
        path
    }

    #[test]
    fn images_embed_and_everything_else_links() {
        let png = scratch("photo.PNG", b"fake image bytes");
        match attachment_block(&png).unwrap() {
            ContentBlock::Image(image) => {
                assert_eq!(image.mime_type, "image/png");
                use base64::Engine;
                assert_eq!(
                    base64::engine::general_purpose::STANDARD
                        .decode(image.data)
                        .unwrap(),
                    b"fake image bytes"
                );
            }
            other => panic!("expected an image block, got {other:?}"),
        }

        let step = scratch("bracket.step", b"ISO-10303");
        match attachment_block(&step).unwrap() {
            ContentBlock::ResourceLink(link) => {
                assert_eq!(link.name, "bracket.step");
                assert!(link.uri.starts_with("file://"));
                assert!(link.uri.ends_with("/bracket.step"));
            }
            other => panic!("expected a resource link, got {other:?}"),
        }

        let missing = std::path::Path::new("/nowhere/gone.png");
        assert!(attachment_block(missing).unwrap_err().contains("gone.png"));

        let huge = scratch("huge.png", &vec![0u8; 10 * 1024 * 1024 + 1]);
        assert!(attachment_block(&huge).unwrap_err().contains("too large"));
    }
}
