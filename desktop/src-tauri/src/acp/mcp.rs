//! The nurb MCP server every ACP session is handed, and the pieces around it.
//!
//! The native Claude driver has always passed the serve's `/mcp` endpoint on
//! its command line (see claude.rs). Adapter-hosted agents got nothing, so
//! they could talk about a part and never touch one. ACP carries the same
//! entry as a session-scoped MCP server, over http. The serve speaks http
//! only, so an agent that does not advertise http gets no entry and works in
//! the folder fallback instead.
//!
//! ACP has no way to ask a model what tools it can see, so whether the entry
//! actually landed is answered by a throwaway probe session and remembered
//! per adapter version.

use std::collections::HashMap;
use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::time::Duration;

use agent_client_protocol::schema::v1::{
    HttpHeader, McpCapabilities, McpServer, McpServerHttp, SessionUpdate, ToolCallStatus,
};

use crate::supervisor::ServeInfo;

/// The name the entry carries, and the prefix a tool call wears once a model
/// has it. Changing it renames every tool the models see.
pub(crate) const SERVER: &str = "nurb";

/// How long a capture waits on the serve. It is a local process, so a slow
/// answer means something is wrong rather than something is far away.
const CAPTURE_TIMEOUT: Duration = Duration::from_secs(10);

/// The MCP entry for one session, or nothing when the agent cannot speak
/// http. The serve publishes its tools over http alone.
pub(crate) fn nurb_mcp_server(caps: &McpCapabilities, serve: &ServeInfo) -> Option<McpServer> {
    if !caps.http {
        return None;
    }
    let mut http = McpServerHttp::new(SERVER, format!("{}/mcp", serve.url.trim_end_matches('/')));
    http.headers.push(HttpHeader::new(
        "Authorization",
        format!("Bearer {}", serve.token),
    ));
    Some(McpServer::Http(http))
}

/// Check one project out into a folder the agent can work in. The serve owns
/// the database, so the copy comes from it rather than from a command.
pub(crate) async fn checkout(
    serve: &ServeInfo,
    project_id: &str,
    root: &Path,
) -> Result<(), String> {
    let port = serve.port;
    let path = format!("/api/projects/{project_id}/checkout");
    let request = serde_json::json!({ "directory": root.display().to_string() }).to_string();
    tauri::async_runtime::spawn_blocking(move || {
        let (status, body) = loopback_post(port, &path, &request, CAPTURE_TIMEOUT)
            .map_err(|error| format!("Could not copy the project out: {error}"))?;
        if (200..300).contains(&status) {
            return Ok(());
        }
        let message = serde_json::from_str::<serde_json::Value>(&body)
            .ok()
            .and_then(|json| {
                json.get("error")
                    .and_then(|error| error.as_str())
                    .map(str::to_string)
            })
            .or_else(|| Some(body.trim().to_string()).filter(|text| !text.is_empty()))
            .unwrap_or_else(|| "Could not copy the project out.".into());
        Err(message)
    })
    .await
    .map_err(|error| format!("Could not copy the project out: {error}"))?
}

/// Keep one chat photo with the project, where find_photos reads it.
pub(crate) async fn save_photo(
    serve: &ServeInfo,
    project_id: &str,
    name: String,
    mime: &str,
    data: Vec<u8>,
) -> Result<(), String> {
    use base64::Engine;
    let port = serve.port;
    let path = format!("/api/projects/{project_id}/attachments");
    let request = serde_json::json!({
        "name": name,
        "mime": mime,
        "data": base64::engine::general_purpose::STANDARD.encode(data),
    })
    .to_string();
    tauri::async_runtime::spawn_blocking(move || {
        let (status, body) = loopback_post(port, &path, &request, CAPTURE_TIMEOUT)?;
        if (200..300).contains(&status) {
            Ok(())
        } else {
            Err(format!("the serve answered {status}: {body}"))
        }
    })
    .await
    .map_err(|error| error.to_string())?
}

/// A downloaded mesh can run to a million triangles, and reading one plus drawing
/// it takes the serve several seconds.
const DESCRIBE_TIMEOUT: Duration = Duration::from_secs(90);

/// A mesh file as the serve sees it: its measurements in words, and a PNG of it
/// from four sides. Claude cannot open a file at all, and no agent can be
/// counted on to read a 3MF.
pub(crate) async fn describe_mesh(serve: &ServeInfo, path: &str) -> Result<(String, Vec<u8>), String> {
    use base64::Engine;
    let port = serve.port;
    let request = serde_json::json!({ "path": path }).to_string();
    tauri::async_runtime::spawn_blocking(move || {
        let (status, body) = loopback_post(port, "/api/mesh", &request, DESCRIBE_TIMEOUT)?;
        let json: serde_json::Value =
            serde_json::from_str(&body).map_err(|_| format!("the serve answered {status}: {body}"))?;
        if !(200..300).contains(&status) {
            return Err(json["error"].as_str().unwrap_or(body.trim()).to_string());
        }
        let text = json["text"].as_str().ok_or("the serve sent no description")?.to_string();
        let png = base64::engine::general_purpose::STANDARD
            .decode(json["png"].as_str().unwrap_or_default())
            .map_err(|e| format!("the serve sent a broken picture: {e}"))?;
        Ok((text, png))
    })
    .await
    .map_err(|error| error.to_string())?
}

/// The tool names the serve publishes, read at compile time so this list and
/// the server's cannot drift.
fn tool_names() -> &'static [String] {
    use std::sync::OnceLock;
    static NAMES: OnceLock<Vec<String>> = OnceLock::new();
    NAMES.get_or_init(|| {
        let raw = include_str!("../../../../engine/src/nurb/tools.json");
        serde_json::from_str::<Vec<serde_json::Value>>(raw)
            .unwrap_or_default()
            .iter()
            .filter_map(|tool| tool.get("name")?.as_str().map(str::to_string))
            .collect()
    })
}

/// The bare tool name behind whatever spelling an adapter gave it. Agents
/// namespace MCP tools differently (`mcp__nurb__run_build`, `mcp.nurb.run_build`,
/// `nurb/run_build`), and some pass the name through untouched, so the
/// namespace is peeled off a separator at a time.
pub(crate) fn nurb_tool(title: &str) -> Option<String> {
    let mut rest = title;
    for host in ["mcp__", "mcp.", "mcp:"] {
        if let Some(without) = rest.strip_prefix(host) {
            rest = without;
            break;
        }
    }
    let rest = rest.strip_prefix(SERVER).unwrap_or(rest);
    for separator in ["__", "/", ".", ":"] {
        if let Some(tool) = rest.strip_prefix(separator) {
            if !tool.is_empty() {
                return Some(tool.to_string());
            }
        }
    }
    tool_names()
        .iter()
        .any(|name| name == title)
        .then(|| title.to_string())
}

/// Title and kind for a tool call row: a nurb tool loses its namespace and
/// gains the kind the card renders verbs from, anything else is untouched.
pub(crate) fn named(title: String, kind: String) -> (String, String) {
    match nurb_tool(&title) {
        Some(tool) => (tool, SERVER.to_string()),
        None => (title, kind),
    }
}

/// The one question the probe asks. Enumeration cannot answer it: Codex loads
/// an MCP server's tools lazily, so a model with the tools connected still
/// lists none. Only a call reaches the server, so the probe asks for the
/// cheapest one there is.
// On a machine with many MCP servers Codex keeps their tools out of the prompt
// until the model searches for them, and asked plainly it answered NO TOOL twice
// with the server connected; told to search first it called the tool every time.
pub(crate) const PROBE_PROMPT: &str = "The MCP server named \"nurb\" is attached to this session. Call its tool list_projects (it may be spelled list_projects, mcp__nurb__list_projects or mcp.nurb.list_projects; if it is not in your tool list, search your MCP tools for it first) and reply with its raw output. Do not call any other tool. If it truly does not exist, reply NO TOOL.";

/// Whether the probe reached the server: a tool call the app recognised as
/// nurb's, or an answer carrying the key `list_projects` replies with.
pub(crate) fn tools_reached(reply: &str, saw_nurb_call: bool) -> bool {
    saw_nurb_call || reply.contains("projects")
}

/// The part a written path names, or None for anything that is not a part:
/// the underscore-prefixed shared modules and every other file.
pub(crate) fn captured_part(path: &str, root: &Path) -> Option<String> {
    let rest = Path::new(path).strip_prefix(root).ok()?;
    let mut parts = rest.components();
    if parts.next()?.as_os_str() != "parts" {
        return None;
    }
    let file = parts.next()?.as_os_str().to_str()?.to_string();
    if parts.next().is_some() {
        return None;
    }
    let name = file.strip_suffix(".py")?;
    if name.is_empty() || name.starts_with('_') {
        return None;
    }
    name.chars()
        .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_')
        .then(|| name.to_string())
}

/// One remembered verdict: did the tools reach this adapter version.
#[derive(Clone, serde::Serialize, serde::Deserialize)]
pub(crate) struct Verdict {
    pub tools: bool,
    pub transport: String,
    pub checked_at: String,
}

/// Keyed by adapter version, because a bumped adapter is a different program
/// and its answer has to be asked again.
pub(crate) fn verdict_key(agent_id: &str, pin: Option<&str>) -> String {
    format!("{agent_id}@{}", pin.unwrap_or("native"))
}

/// An RFC 3339 stamp for the verdict, so a cache entry says when it was
/// asked. No date crate: this is the only date the app writes.
pub(crate) fn now() -> String {
    let seconds = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|since| since.as_secs())
        .unwrap_or_default();
    let (days, rest) = (seconds / 86_400, seconds % 86_400);
    // Days from the civil epoch back to a calendar date (Howard Hinnant's).
    let z = days as i64 + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1_460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let day = doy - (153 * mp + 2) / 5 + 1;
    let month = if mp < 10 { mp + 3 } else { mp - 9 };
    let year = era * 400 + yoe + i64::from(month <= 2);
    format!(
        "{year:04}-{month:02}-{day:02}T{:02}:{:02}:{:02}Z",
        rest / 3_600,
        (rest % 3_600) / 60,
        rest % 60
    )
}

pub(crate) fn verdict_path(data: &Path) -> PathBuf {
    data.join("mcp-tools.json")
}

pub(crate) fn read_verdict(data: &Path, key: &str) -> Option<Verdict> {
    let text = std::fs::read_to_string(verdict_path(data)).ok()?;
    serde_json::from_str::<HashMap<String, Verdict>>(&text)
        .ok()?
        .remove(key)
}

pub(crate) fn write_verdict(data: &Path, key: &str, verdict: &Verdict) {
    let path = verdict_path(data);
    let mut all: HashMap<String, Verdict> = std::fs::read_to_string(&path)
        .ok()
        .and_then(|text| serde_json::from_str(&text).ok())
        .unwrap_or_default();
    all.insert(key.to_string(), verdict.clone());
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    if let Ok(text) = serde_json::to_string_pretty(&all) {
        let _ = std::fs::write(path, text);
    }
}


/// The working folder a session runs in. Only a verdict that says the tools
/// did not arrive moves the agent off the project directory.
pub(crate) fn session_cwd(tools: bool, project: &Path, checkout: &Path) -> PathBuf {
    if tools {
        project.to_path_buf()
    } else {
        checkout.to_path_buf()
    }
}

/// Every part file in a working folder, by name. The snapshot the sweep
/// compares against, and what a capture updates.
pub(crate) fn snapshot_parts(root: &Path) -> HashMap<String, String> {
    let mut parts = HashMap::new();
    let Ok(entries) = std::fs::read_dir(root.join("parts")) else {
        return parts;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        let Some(name) = captured_part(&path.display().to_string(), root) else {
            continue;
        };
        if let Ok(source) = std::fs::read_to_string(&path) {
            parts.insert(name, source);
        }
    }
    parts
}

/// The parts whose source differs from the snapshot: what the agent wrote
/// while it worked, and nothing it only read.
pub(crate) fn changed_parts(
    snapshot: &HashMap<String, String>,
    root: &Path,
) -> Vec<(String, String)> {
    let mut changed: Vec<(String, String)> = snapshot_parts(root)
        .into_iter()
        .filter(|(name, source)| snapshot.get(name) != Some(source))
        .collect();
    changed.sort_by(|a, b| a.0.cmp(&b.0));
    changed
}

/// The parts a finished tool call named, from the locations it reported and
/// from the path keys adapters put in raw input.
pub(crate) fn completed_parts(update: &SessionUpdate, root: &Path) -> Vec<String> {
    let SessionUpdate::ToolCallUpdate(update) = update else {
        return Vec::new();
    };
    if update.fields.status != Some(ToolCallStatus::Completed) {
        return Vec::new();
    }
    let mut named: Vec<String> = update
        .fields
        .locations
        .as_deref()
        .unwrap_or_default()
        .iter()
        .filter_map(|location| captured_part(&location.path.display().to_string(), root))
        .collect();
    if let Some(raw) = update.fields.raw_input.as_ref() {
        for key in ["file_path", "path", "abs_path"] {
            if let Some(part) = raw
                .get(key)
                .and_then(|value| value.as_str())
                .and_then(|path| captured_part(path, root))
            {
                named.push(part);
            }
        }
    }
    named.sort();
    named.dedup();
    named
}

/// Hand one part back to the project it was checked out of. Ok(true) means
/// the source was new to the project; Err carries the sentence to show.
pub(crate) async fn capture(
    serve: &ServeInfo,
    project_id: &str,
    part: &str,
    source: &str,
    label: &str,
) -> Result<bool, String> {
    let port = serve.port;
    let path = format!("/api/projects/{project_id}/parts/{part}/source");
    let request = serde_json::json!({
        "source": source,
        "note": format!("captured from {label}'s working folder"),
    })
    .to_string();
    let part = part.to_string();
    tauri::async_runtime::spawn_blocking(move || {
        let (status, body) = loopback_post(port, &path, &request, CAPTURE_TIMEOUT)
            .map_err(|error| format!("Could not save {part} back to the project: {error}"))?;
        let body: serde_json::Value = serde_json::from_str(&body).unwrap_or_default();
        if !(200..300).contains(&status) {
            return Err(body
                .get("error")
                .and_then(|error| error.as_str())
                .unwrap_or("The project would not take that part back.")
                .to_string());
        }
        Ok(body
            .get("changed")
            .and_then(serde_json::Value::as_bool)
            .unwrap_or(false))
    })
    .await
    .map_err(|error| format!("Could not save the part back to the project: {error}"))?
}

/// A minimal loopback POST, the mirror of the supervisor's GET. The serve is
/// always on 127.0.0.1, so there is no TLS here and never will be, and it
/// answers with Content-Length and honours Connection: close, which makes
/// read-to-end the whole protocol.
fn loopback_post(port: u16, path: &str, body: &str, timeout: Duration) -> Result<(u16, String), String> {
    let address = SocketAddr::from(([127, 0, 0, 1], port));
    let mut stream = TcpStream::connect_timeout(&address, CAPTURE_TIMEOUT)
        .map_err(|e| format!("connect to the serve: {e}"))?;
    stream.set_read_timeout(Some(timeout)).ok();
    stream.set_write_timeout(Some(timeout)).ok();
    write!(
        stream,
        "POST {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
        body.len()
    )
    .map_err(|e| format!("request: {e}"))?;
    let mut response = String::new();
    stream
        .read_to_string(&mut response)
        .map_err(|e| format!("response: {e}"))?;
    let (head, body) = response
        .split_once("\r\n\r\n")
        .ok_or("malformed response from the serve")?;
    let status = head
        .lines()
        .next()
        .and_then(|line| line.split_whitespace().nth(1))
        .and_then(|code| code.parse().ok())
        .ok_or("malformed response from the serve")?;
    Ok((status, body.to_string()))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn serve() -> ServeInfo {
        ServeInfo {
            url: "http://127.0.0.1:7373".into(),
            port: 7373,
            pid: 1,
            token: "t".into(),
        }
    }

    fn caps(http: bool) -> McpCapabilities {
        let mut caps = McpCapabilities::new();
        caps.http = http;
        caps
    }

    #[test]
    fn an_http_agent_gets_the_serve_endpoint_with_its_token() {
        let entry = nurb_mcp_server(&caps(true), &serve());

        assert_eq!(
            serde_json::to_value(entry.unwrap()).unwrap(),
            serde_json::json!({
                "type": "http",
                "name": "nurb",
                "url": "http://127.0.0.1:7373/mcp",
                "headers": [{ "name": "Authorization", "value": "Bearer t" }],
            })
        );
    }

    /// No http, no server entry: the session falls back to a folder copy
    /// rather than carrying a transport the serve does not speak.
    #[test]
    fn an_agent_without_http_gets_no_server() {
        assert!(nurb_mcp_server(&caps(false), &serve()).is_none());
    }

    #[test]
    fn every_spelling_of_a_nurb_tool_becomes_one_row() {
        for title in [
            "mcp__nurb__run_build",
            "mcp.nurb.run_build",
            "mcp:nurb:run_build",
            "nurb__run_build",
            "nurb/run_build",
            "nurb.run_build",
            "nurb:run_build",
            "run_build",
        ] {
            assert_eq!(
                named(title.into(), "other".into()),
                ("run_build".to_string(), "nurb".to_string()),
                "{title}"
            );
        }
        assert_eq!(
            named("mcp.nurb.read_guide".into(), "execute".into()),
            ("read_guide".to_string(), "nurb".to_string())
        );
        assert_eq!(
            named("Read".into(), "read".into()),
            ("Read".to_string(), "read".to_string())
        );
    }

    #[test]
    fn the_probe_believes_an_answer_from_the_server_and_nothing_else() {
        assert!(tools_reached("{\"projects\": []}", false));
        // A model that calls the tool and says nothing still proved it.
        assert!(tools_reached("", true));
        assert!(!tools_reached("NO TOOL", false));
    }

    /// A stand-in for the serve: takes one request, answers it, and hands the
    /// request back so the test can read what was actually on the wire.
    fn one_request(answer: &'static str) -> (u16, std::sync::mpsc::Receiver<String>) {
        let listener = std::net::TcpListener::bind(("127.0.0.1", 0)).unwrap();
        let port = listener.local_addr().unwrap().port();
        let (sent, heard) = std::sync::mpsc::channel();
        std::thread::spawn(move || {
            let (mut stream, _) = listener.accept().unwrap();
            let mut reader = std::io::BufReader::new(stream.try_clone().unwrap());
            let mut head = String::new();
            loop {
                let mut line = String::new();
                if std::io::BufRead::read_line(&mut reader, &mut line).unwrap() == 0 {
                    break;
                }
                if line == "\r\n" {
                    break;
                }
                head.push_str(&line);
            }
            let length: usize = head
                .lines()
                .find_map(|line| line.strip_prefix("Content-Length: "))
                .and_then(|value| value.trim().parse().ok())
                .unwrap_or(0);
            let mut body = vec![0u8; length];
            reader.read_exact(&mut body).unwrap();
            stream.write_all(answer.as_bytes()).unwrap();
            stream.flush().unwrap();
            drop(stream);
            sent.send(format!("{head}\r\n{}", String::from_utf8(body).unwrap()))
                .ok();
        });
        (port, heard)
    }

    fn serve_on(port: u16) -> ServeInfo {
        ServeInfo {
            url: format!("http://127.0.0.1:{port}"),
            port,
            ..serve()
        }
    }

    #[test]
    fn a_capture_posts_the_source_and_reads_the_answer() {
        let (port, heard) = one_request(
            "HTTP/1.1 200 OK\r\nContent-Length: 17\r\nConnection: close\r\n\r\n{\"changed\": true}",
        );

        let changed = tauri::async_runtime::block_on(capture(
            &serve_on(port),
            "shelf",
            "clip",
            "print(1)",
            "Claude",
        ));

        let request = heard.recv().unwrap();
        let (head, body) = request.split_once("\r\n\r\n").unwrap();
        assert_eq!(
            head.lines().next().unwrap(),
            "POST /api/projects/shelf/parts/clip/source HTTP/1.1"
        );
        assert!(head.contains("Content-Type: application/json"), "{head}");
        assert!(head.contains("Content-Length: "), "{head}");
        let body: serde_json::Value = serde_json::from_str(body).unwrap();
        assert_eq!(body["source"], "print(1)");
        assert_eq!(body["note"], "captured from Claude's working folder");
        assert_eq!(changed, Ok(true));
    }

    /// A refusal is the serve's own sentence, because it knows why.
    #[test]
    fn a_refused_capture_carries_the_serves_own_words() {
        let (port, heard) = one_request(
            "HTTP/1.1 400 Bad Request\r\nContent-Length: 21\r\nConnection: close\r\n\r\n{\"error\": \"bad name\"}",
        );

        let refused = tauri::async_runtime::block_on(capture(
            &serve_on(port),
            "shelf",
            "clip",
            "print(1)",
            "Claude",
        ));

        heard.recv().unwrap();
        assert_eq!(refused, Err("bad name".to_string()));
    }

    #[test]
    fn a_checkout_asks_the_serve_for_the_folder() {
        let (port, heard) = one_request(
            "HTTP/1.1 200 OK\r\nContent-Length: 39\r\nConnection: close\r\n\r\n{\"directory\": \"/work\", \"parts\": []}",
        );

        let written = tauri::async_runtime::block_on(checkout(
            &serve_on(port),
            "shelf",
            Path::new("/work/checkout"),
        ));

        let request = heard.recv().unwrap();
        let (head, body) = request.split_once("\r\n\r\n").unwrap();
        assert_eq!(
            head.lines().next().unwrap(),
            "POST /api/projects/shelf/checkout HTTP/1.1"
        );
        let body: serde_json::Value = serde_json::from_str(body).unwrap();
        assert_eq!(body["directory"], "/work/checkout");
        assert_eq!(written, Ok(()));
    }

    /// A refusal is the serve's own sentence, in either shape it sends.
    #[test]
    fn a_refused_checkout_carries_the_serves_own_words() {
        let (port, heard) = one_request(
            "HTTP/1.1 400 Bad Request\r\nContent-Length: 27\r\nConnection: close\r\n\r\nthat folder is not empty do",
        );

        let refused = tauri::async_runtime::block_on(checkout(
            &serve_on(port),
            "shelf",
            Path::new("/work/checkout"),
        ));

        heard.recv().unwrap();
        assert_eq!(refused, Err("that folder is not empty do".to_string()));
    }

    #[test]
    fn only_a_real_part_file_is_captured_back() {
        let root = Path::new("/work/checkout");

        assert_eq!(
            captured_part("/work/checkout/parts/clip.py", root).as_deref(),
            Some("clip")
        );
        assert_eq!(captured_part("/work/checkout/parts/_helper.py", root), None);
        assert_eq!(captured_part("/work/checkout/notes.md", root), None);
        assert_eq!(captured_part("/elsewhere/parts/clip.py", root), None);
    }
}

#[cfg(test)]
mod fallback_tests {
    use super::*;

    #[test]
    fn only_a_failed_verdict_moves_the_agent_into_a_working_folder() {
        let project = Path::new("/data/projects/p1");
        let checkout = project.join("checkout");

        assert_eq!(session_cwd(true, project, &checkout), project);
        assert_eq!(session_cwd(false, project, &checkout), checkout);
    }

    #[test]
    fn the_sweep_reports_the_changed_part_and_not_the_shared_module() {
        let root = std::env::temp_dir().join(format!("nurb-sweep-{}", std::process::id()));
        std::fs::create_dir_all(root.join("parts")).unwrap();
        std::fs::write(root.join("parts/clip.py"), "old").unwrap();
        std::fs::write(root.join("parts/_shared.py"), "old").unwrap();
        let snapshot = snapshot_parts(&root);
        std::fs::write(root.join("parts/clip.py"), "new").unwrap();
        std::fs::write(root.join("parts/_shared.py"), "new").unwrap();

        let changed = changed_parts(&snapshot, &root);

        std::fs::remove_dir_all(&root).ok();
        assert_eq!(changed, vec![("clip".to_string(), "new".to_string())]);
    }
}
