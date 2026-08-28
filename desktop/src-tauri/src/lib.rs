mod acp;
mod agents;
mod env;
mod prefs;
mod proc;
mod provision;
mod registry;
mod sessions;
mod supervisor;

use std::io::{Read, Write};
use std::net::TcpStream;
use std::path::PathBuf;
use std::time::Duration;

use registry::{ProjectView, Registry};
use supervisor::Supervisor;
use tauri::{AppHandle, Manager, RunEvent, State};

#[derive(serde::Serialize)]
struct ServerInfo {
    url: String,
    port: u16,
}

#[tauri::command]
fn list_projects(registry: State<Registry>) -> Vec<ProjectView> {
    registry.list()
}

/// A first-part name `nurb new` will accept: it derives the Python module and
/// function from this, so it has to survive becoming an identifier.
fn seed_part_name(project: &str) -> String {
    let slug: String = project
        .to_lowercase()
        .chars()
        .map(|c| if c.is_whitespace() { '-' } else { c })
        .filter(|c| c.is_ascii_alphanumeric() || *c == '-' || *c == '_')
        .collect();
    let module = slug.replace('-', "_");
    let keyword = [
        "and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del",
        "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with",
        "yield",
    ]
    .contains(&module.as_str());
    match slug.chars().next() {
        Some(c) if c.is_ascii_alphabetic() && !keyword => slug,
        Some(_) => format!("part-{slug}"),
        None => "part".into(),
    }
}

/// A name that becomes a folder on any platform the project might sync to:
/// no path separators, none of Windows' reserved characters or device names,
/// no trailing dot or space (which Explorer cannot create or delete). The
/// rules apply everywhere so a project born on a Mac still opens on a PC.
fn valid_project_name(name: &str) -> bool {
    if name.is_empty() || name.starts_with('.') || name.ends_with('.') || name.ends_with(' ') {
        return false;
    }
    if name.contains(['/', '\\', ':', '*', '?', '"', '<', '>', '|']) {
        return false;
    }
    if name.chars().any(|c| c.is_control()) {
        return false;
    }
    let stem = name.split('.').next().unwrap_or(name).to_ascii_uppercase();
    let reserved = matches!(
        stem.as_str(),
        "CON" | "PRN" | "AUX" | "NUL"
            | "COM1" | "COM2" | "COM3" | "COM4" | "COM5" | "COM6" | "COM7" | "COM8" | "COM9"
            | "LPT1" | "LPT2" | "LPT3" | "LPT4" | "LPT5" | "LPT6" | "LPT7" | "LPT8" | "LPT9"
    );
    !reserved
}

fn project_base(folder: Option<String>, default: PathBuf) -> PathBuf {
    match folder
        .as_deref()
        .map(str::trim)
        .filter(|path| !path.is_empty())
    {
        Some(path) => PathBuf::from(path),
        None => default,
    }
}

fn default_projects_folder_path(app: &AppHandle) -> Result<PathBuf, String> {
    Ok(app
        .path()
        .document_dir()
        .map_err(|e| format!("no Documents folder: {e}"))?
        .join("nurb"))
}

#[tauri::command]
fn default_projects_folder(app: AppHandle) -> Result<String, String> {
    Ok(default_projects_folder_path(&app)?
        .to_string_lossy()
        .into_owned())
}

#[tauri::command]
async fn create_project(
    app: AppHandle,
    name: String,
    folder: Option<String>,
) -> Result<String, String> {
    let name = name.trim().to_string();
    if !valid_project_name(&name) {
        return Err("project names cannot be empty or contain slashes".into());
    }
    let base = project_base(folder, default_projects_folder_path(&app)?);
    let dir = base.join(&name);
    if dir.exists() {
        return Err(format!(
            "{} already exists. Use \"add existing\" to bring it in.",
            dir.display()
        ));
    }
    let part = seed_part_name(&name);
    let module = part.replace('-', "_");
    let launcher = app.state::<env::Launcher>().inner().clone();
    let created = tauri::async_runtime::spawn_blocking(move || -> Result<PathBuf, String> {
        std::fs::create_dir_all(&dir)
            .map_err(|e| format!("could not create {}: {e}", dir.display()))?;
        // Seed the project with a first part named after it; nurb new also
        // writes the card and AGENTS.md.
        let seeded = seed(&launcher, &dir, &part);
        if seeded.is_err() {
            // The folder did not exist before this call, so a failed seed
            // must not leave a husk behind that blocks retrying the name.
            let _ = std::fs::remove_dir_all(&dir);
        }
        seeded.map(|_| dir)
    })
    .await
    .map_err(|e| e.to_string())??;
    let registry = app.state::<Registry>();
    registry.upsert(&name, &created, Some(module));
    Ok(created.to_string_lossy().into_owned())
}

fn seed(launcher: &env::Launcher, dir: &std::path::Path, part: &str) -> Result<(), String> {
    let output = launcher
        .nurb()
        .args(["new", "--embed", "--root"])
        .arg(dir)
        .arg(part)
        .current_dir(dir)
        .output()
        .map_err(|e| format!("could not run nurb new: {e}"))?;
    if !output.status.success() {
        return Err(format!(
            "nurb new failed: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    // Keep the subprocess contract honest if its explicit-root behavior changes.
    if !dir.join("parts").is_dir() {
        return Err(format!("nurb new did not create {}/parts", dir.display()));
    }
    Ok(())
}

#[tauri::command]
fn add_project(registry: State<Registry>, path: String) -> Result<String, String> {
    let (name, dir) = validated_project(PathBuf::from(path))?;
    registry.upsert(&name, &dir, None);
    Ok(dir.to_string_lossy().into_owned())
}

fn validated_project(path: PathBuf) -> Result<(String, PathBuf), String> {
    let dir = path
        .canonicalize()
        .map_err(|e| format!("cannot read that folder: {e}"))?;
    if !dir.join("parts").is_dir() {
        return Err("that folder has no parts/ directory, so it is not a nurb project".into());
    }
    let name = dir
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .ok_or("cannot use the filesystem root as a project")?;
    Ok((name, dir))
}

fn register_projects_in_folder(
    registry: &Registry,
    folder: PathBuf,
) -> Result<Vec<String>, String> {
    let folder = folder
        .canonicalize()
        .map_err(|e| format!("cannot read that folder: {e}"))?;
    let entries =
        std::fs::read_dir(&folder).map_err(|e| format!("cannot read {}: {e}", folder.display()))?;
    let mut projects = Vec::new();
    for entry in entries.flatten() {
        let path = entry.path();
        if !path.join("parts").is_dir() {
            continue;
        }
        if let Ok((name, dir)) = validated_project(path) {
            registry.adopt(&name, &dir);
            projects.push(dir.to_string_lossy().into_owned());
        }
    }
    projects.sort();
    Ok(projects)
}

#[tauri::command]
fn add_projects_from_folder(
    registry: State<Registry>,
    folder: String,
) -> Result<Vec<String>, String> {
    register_projects_in_folder(&registry, PathBuf::from(folder))
}

#[tauri::command]
fn remove_project(app: AppHandle, path: String) {
    let dir = PathBuf::from(&path);
    app.state::<Registry>().remove(&dir);
    // A project the app no longer knows about keeps no standing permission
    // grant, so a different folder put here later starts from the default.
    app.state::<acp::Approvals>().forget(&dir);
    // Removing an open project also stops its server; the files stay put.
    tauri::async_runtime::spawn_blocking(move || app.state::<Supervisor>().close(&dir));
}

#[tauri::command]
fn select_part(registry: State<Registry>, path: String, part: Option<String>) {
    registry.select_part(&PathBuf::from(path), part);
}

#[tauri::command]
fn select_part_chat(
    sessions: State<sessions::SessionStore>,
    path: String,
    part: String,
    session_id: Option<String>,
) {
    sessions.select_part_chat(&PathBuf::from(path), &part, session_id);
}

#[tauri::command]
async fn open_project(app: AppHandle, path: String) -> Result<ServerInfo, String> {
    // The registry's stored path is the key everywhere (supervisor map, close,
    // list_parts, touch). Canonicalizing only here would split the keys the
    // moment a symlink is involved, so it is deliberately not done.
    let project = PathBuf::from(&path);
    if !project.is_dir() {
        return Err(format!("project folder missing: {}", project.display()));
    }
    // Supervisor::open blocks until the server is ready, so keep it off the
    // async runtime's core threads.
    let opened = project.clone();
    let handle = app.clone();
    let port =
        tauri::async_runtime::spawn_blocking(move || handle.state::<Supervisor>().open(&opened))
            .await
            .map_err(|e| e.to_string())??;
    app.state::<Registry>().touch(&project);
    Ok(ServerInfo {
        url: format!("http://127.0.0.1:{port}"),
        port,
    })
}

/// Delete a part by moving its source and card to the Trash, so a mistake is
/// recoverable. Derived files under build/ stay; they are regenerated anyway.
#[tauri::command]
async fn delete_part(path: String, part: String) -> Result<(), String> {
    let module = part.replace('-', "_");
    let parts = PathBuf::from(&path).join("parts");
    let py = parts.join(format!("{module}.py"));
    if !py.is_file() {
        return Err(format!("no part named {part} in {}", parts.display()));
    }
    let mut targets = vec![py];
    let md = parts.join(format!("{module}.md"));
    if md.is_file() {
        targets.push(md);
    }
    tauri::async_runtime::spawn_blocking(move || {
        trash::delete_all(&targets).map_err(|e| e.to_string())
    })
    .await
    .map_err(|e| e.to_string())?
}

/// Create a new part in an existing project via `nurb new`. Returns the part
/// name as list_parts will report it (the module stem, hyphens folded).
#[tauri::command]
async fn create_part(app: AppHandle, path: String, name: String) -> Result<String, String> {
    let part = seed_part_name(name.trim());
    let dir = PathBuf::from(&path);
    if !dir.join("parts").is_dir() {
        return Err(format!("no parts/ directory in {}", dir.display()));
    }
    let launcher = app.state::<env::Launcher>().inner().clone();
    let spawned = part.clone();
    tauri::async_runtime::spawn_blocking(move || seed(&launcher, &dir, &spawned))
        .await
        .map_err(|e| e.to_string())??;
    Ok(part.replace('-', "_"))
}

/// A pasted image has no path for the attachment list, so it lands in a
/// temporary file first. Each paste gets its own directory so the friendly
/// filename never collides across pastes.
#[tauri::command]
fn save_pasted_image(request: tauri::ipc::Request) -> Result<String, String> {
    let tauri::ipc::InvokeBody::Raw(bytes) = request.body() else {
        return Err("expected raw image bytes".into());
    };
    let mime = request.headers().get("mime").and_then(|m| m.to_str().ok());
    Ok(write_pasted_image(mime, bytes)?
        .to_string_lossy()
        .into_owned())
}

fn write_pasted_image(mime: Option<&str>, bytes: &[u8]) -> Result<PathBuf, String> {
    // Keep the real type: attachment_block embeds the formats agents support
    // and links everything else. Renaming TIFF or HEIC bytes to PNG makes an
    // invalid embedded image instead of a readable file attachment.
    let extension = match mime {
        Some("image/png") => "png",
        Some("image/jpeg") => "jpg",
        Some("image/gif") => "gif",
        Some("image/webp") => "webp",
        Some("image/tiff") => "tiff",
        Some("image/bmp") => "bmp",
        Some("image/avif") => "avif",
        Some("image/heic") => "heic",
        Some("image/heif") => "heif",
        Some("image/svg+xml") => "svg",
        Some("image/x-icon") | Some("image/vnd.microsoft.icon") => "ico",
        Some(other) => return Err(format!("cannot paste {other} images")),
        None => return Err("pasted image has no type".into()),
    };
    let dir = std::env::temp_dir().join(format!(
        "nurb-paste-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos()
    ));
    std::fs::create_dir_all(&dir).map_err(|e| format!("could not save pasted image: {e}"))?;
    let path = dir.join(format!("pasted-image.{extension}"));
    std::fs::write(&path, bytes).map_err(|e| format!("could not save pasted image: {e}"))?;
    Ok(path)
}

#[tauri::command]
async fn list_parts(app: AppHandle, path: String) -> Result<serde_json::Value, String> {
    let project = PathBuf::from(path);
    let port = app
        .state::<Supervisor>()
        .port(&project)
        .ok_or("project is not open")?;
    let body = tauri::async_runtime::spawn_blocking(move || http_get(port, "/api/parts"))
        .await
        .map_err(|e| e.to_string())??;
    part_views(&project, &body)
}

/// The server response only contains builds that have finished. The rail is a
/// source-file index, so merge build errors onto every source instead of hiding
/// slow parts during startup.
fn part_views(project: &std::path::Path, body: &str) -> Result<serde_json::Value, String> {
    let built: Vec<serde_json::Value> =
        serde_json::from_str(body).map_err(|e| format!("bad /api/parts response: {e}"))?;
    let mut names = Vec::new();
    let entries = std::fs::read_dir(project.join("parts"))
        .map_err(|e| format!("cannot read {}/parts: {e}", project.display()))?;
    for entry in entries {
        let path = entry
            .map_err(|e| format!("cannot read part entry: {e}"))?
            .path();
        let Some(file) = path.file_name().and_then(|name| name.to_str()) else {
            continue;
        };
        if path.extension().and_then(|ext| ext.to_str()) == Some("py") && !file.starts_with('_') {
            names.push(path.file_stem().unwrap().to_string_lossy().into_owned());
        }
    }
    names.sort();
    Ok(serde_json::Value::Array(
        names
            .into_iter()
            .map(|name| {
                let entry = built
                    .iter()
                    .find(|entry| entry.get("name").and_then(|value| value.as_str()) == Some(&name));
                let error = entry
                    .and_then(|entry| entry.get("error"))
                    .cloned()
                    .unwrap_or(serde_json::Value::Null);
                // A refusal (reject() in the part) sets error too, but it is the part
                // declining a configuration, not breaking; the rail marks it amber
                // rather than with the crash red.
                let refused = entry
                    .and_then(|entry| entry.get("refused"))
                    .is_some_and(|value| !value.is_null());
                // The joints payload is the marker the viewer already uses: only an
                // assembly carries one, even empty. A source that has not built yet
                // reads as a part and corrects itself on the next poll.
                let assembly = entry.is_some_and(|entry| entry.get("joints").is_some());
                let uses = entry
                    .and_then(|entry| entry.get("uses"))
                    .cloned()
                    .unwrap_or_else(|| serde_json::Value::Array(Vec::new()));
                // The card's variants, plus which one the server resolved as active,
                // so the rail can nest them the way the browser viewer does.
                let variants = entry
                    .and_then(|entry| entry.get("variants"))
                    .cloned()
                    .unwrap_or_else(|| serde_json::Value::Array(Vec::new()));
                let variant = entry
                    .and_then(|entry| entry.get("variant"))
                    .cloned()
                    .unwrap_or(serde_json::Value::Null);
                serde_json::json!({ "name": name, "error": error, "refused": refused, "assembly": assembly, "uses": uses, "variants": variants, "variant": variant })
            })
            .collect(),
    ))
}

/// A minimal loopback GET. The nurb server always answers with Content-Length
/// and Connection: close, so read-to-end is the whole protocol.
fn http_get(port: u16, path: &str) -> Result<String, String> {
    let address = std::net::SocketAddr::from(([127, 0, 0, 1], port));
    let mut stream = TcpStream::connect_timeout(&address, Duration::from_secs(5))
        .map_err(|e| format!("connect to nurb dev: {e}"))?;
    stream.set_read_timeout(Some(Duration::from_secs(10))).ok();
    stream.set_write_timeout(Some(Duration::from_secs(5))).ok();
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
        .ok_or("malformed response from nurb dev")?;
    let status = head.lines().next().unwrap_or_default();
    if !status.contains(" 200 ") {
        return Err(format!("nurb dev answered: {status}"));
    }
    Ok(body.to_string())
}

/// Dev-build test hook: this machine's UI automation cannot type into a
/// WKWebView (AX rejects value writes on its text areas), so debug builds
/// accept composer text on a loopback socket and forward it to the webview.
/// Never compiled into release builds.
#[cfg(debug_assertions)]
fn test_hook(app: AppHandle) {
    use std::io::Read;
    std::thread::spawn(move || {
        let Ok(listener) = std::net::TcpListener::bind(("127.0.0.1", 7399)) else {
            return;
        };
        for stream in listener.incoming().flatten() {
            let mut text = String::new();
            let mut stream = stream;
            if stream.read_to_string(&mut text).is_ok() && !text.is_empty() {
                use tauri::Emitter;
                // "create:<name>" drives project creation, "open:<name>"
                // switches to a listed project, "send:" submits the visible
                // composer; anything else is composer text. AX presses
                // buttons only while the webview is frontmost and cannot
                // reach WKWebView text fields or list rows, hence all four.
                let _ = if let Some(name) = text.strip_prefix("create:") {
                    app.emit("test-create", name.to_string())
                } else if let Some(name) = text.strip_prefix("open:") {
                    app.emit("test-open", name.to_string())
                } else if text == "send:" {
                    app.emit("test-send", ())
                } else {
                    app.emit("test-type", text)
                };
            }
        }
    });
}

/// macOS ships an empty Help submenu, and a chromeless window has nowhere else to
/// put a link. The two Help items are the only place in the app that reaches the
/// outside world, alongside the same pair in the about box. "Check for Updates…"
/// sits under About where every Mac app keeps it; the webview owns the update
/// state, so the click is forwarded there as an event. Windows has no app menu;
/// its update check and help links live in the about box alone.
#[cfg(target_os = "macos")]
fn install_menu(app: &AppHandle) -> tauri::Result<()> {
    use tauri::menu::{Menu, MenuItem, HELP_SUBMENU_ID};
    let menu = Menu::default(app)?;
    if let Some(appmenu) = menu.items()?.first().and_then(|i| i.as_submenu().cloned()) {
        appmenu.insert(
            &MenuItem::with_id(app, "app:check-updates", "Check for Updates…", true, None::<&str>)?,
            1,
        )?;
    }
    if let Some(help) = menu.get(HELP_SUBMENU_ID).and_then(|i| i.as_submenu().cloned()) {
        help.append_items(&[
            &MenuItem::with_id(app, "help:github", "nurb on GitHub", true, None::<&str>)?,
            &MenuItem::with_id(app, "help:issue", "Report an Issue", true, None::<&str>)?,
        ])?;
    }
    app.set_menu(menu)?;
    app.on_menu_event(|app, event| {
        use tauri::Emitter;
        use tauri_plugin_opener::OpenerExt;
        let url = match event.id().as_ref() {
            "app:check-updates" => {
                let _ = app.emit("menu:check-updates", ());
                return;
            }
            "help:github" => "https://github.com/Shpigford/nurb",
            "help:issue" => "https://github.com/Shpigford/nurb/issues/new",
            _ => return,
        };
        let _ = app.opener().open_url(url, None::<&str>);
    });
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .manage(acp::Chats::new())
        .manage(agents::Logins::new())
        .manage(provision::Provisioner::new())
        .setup(|app| {
            let dir = app.path().app_data_dir()?;
            // Debug-only override so tests can point the whole app (registry,
            // sessions, provisioned env) at a scratch directory while HOME
            // stays real. Never compiled into release builds.
            #[cfg(debug_assertions)]
            let dir = std::env::var_os("NURB_DESKTOP_DATA")
                .map(PathBuf::from)
                .unwrap_or(dir);
            std::fs::create_dir_all(&dir)?;
            let launcher = env::Launcher::resolve(dir.clone());
            app.manage(Supervisor::new(launcher.clone()));
            app.manage(launcher);
            app.manage(Registry::load(&dir));
            app.manage(sessions::SessionStore::load(&dir));
            app.manage(prefs::PrefStore::load(&dir));
            app.manage(acp::Approvals::load(&dir));
            #[cfg(target_os = "macos")]
            install_menu(app.handle())?;
            #[cfg(debug_assertions)]
            test_hook(app.handle().clone());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            list_projects,
            default_projects_folder,
            create_project,
            add_project,
            add_projects_from_folder,
            remove_project,
            select_part,
            select_part_chat,
            open_project,
            create_part,
            delete_part,
            list_parts,
            save_pasted_image,
            acp::start_chat,
            acp::list_sessions,
            acp::send_prompt,
            acp::cancel_turn,
            acp::respond_permission,
            acp::approval_state,
            acp::set_project_auto,
            acp::chat_config,
            acp::set_chat_config,
            acp::close_chat,
            agents::agent_statuses,
            agents::agent_login,
            provision::provision_status,
            provision::provision,
            provision::about_info
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                app.state::<Supervisor>().shutdown();
                app.state::<acp::Chats>().shutdown();
                app.state::<agents::Logins>().shutdown();
                app.state::<provision::Provisioner>().shutdown();
            }
        });
}

#[cfg(test)]
mod tests {
    use super::registry::Registry;
    use super::{
        part_views, project_base, register_projects_in_folder, seed_part_name, write_pasted_image,
    };
    use std::path::PathBuf;

    #[test]
    fn pasted_images_land_in_unique_files_with_honest_extensions() {
        let png = write_pasted_image(Some("image/png"), b"png bytes").unwrap();
        assert_eq!(png.file_name().unwrap(), "pasted-image.png");
        assert_eq!(std::fs::read(&png).unwrap(), b"png bytes");

        let jpg = write_pasted_image(Some("image/jpeg"), b"jpg bytes").unwrap();
        assert_eq!(jpg.file_name().unwrap(), "pasted-image.jpg");
        // Two pastes in one session must not overwrite each other.
        assert_ne!(png.parent(), jpg.parent());

        // Finder preserves native image bytes, so non-embeddable types must
        // retain an honest extension and travel as file links.
        let odd = write_pasted_image(Some("image/tiff"), b"bytes").unwrap();
        assert_eq!(odd.file_name().unwrap(), "pasted-image.tiff");
        assert!(write_pasted_image(Some("image/vnd.unknown"), b"bytes")
            .unwrap_err()
            .contains("cannot paste"));
        assert!(write_pasted_image(None, b"bytes")
            .unwrap_err()
            .contains("no type"));

        for path in [png, jpg, odd] {
            std::fs::remove_dir_all(path.parent().unwrap()).unwrap();
        }
    }

    #[test]
    fn seed_part_names_survive_becoming_identifiers() {
        assert_eq!(seed_part_name("test-shelf"), "test-shelf");
        assert_eq!(seed_part_name("My Shelf 2.0"), "my-shelf-20");
        assert_eq!(seed_part_name("2020 bracket"), "part-2020-bracket");
        assert_eq!(seed_part_name("class"), "part-class");
        assert_eq!(seed_part_name("_widget"), "part-_widget");
        assert_eq!(seed_part_name("émile"), "mile");
        assert_eq!(seed_part_name("支架"), "part");
    }

    #[test]
    fn project_base_uses_the_custom_folder_or_the_documents_default() {
        let documents = PathBuf::from("/Users/test/Documents");
        assert_eq!(
            project_base(Some("/Volumes/Work/nurb".into()), documents.join("nurb")),
            PathBuf::from("/Volumes/Work/nurb")
        );
        assert_eq!(
            project_base(None, documents.join("nurb")),
            documents.join("nurb")
        );
        assert_eq!(
            project_base(Some("  ".into()), documents.join("nurb")),
            documents.join("nurb")
        );
    }

    #[test]
    fn a_projects_folder_loads_only_its_direct_nurb_projects() {
        let root = std::env::temp_dir().join(format!(
            "nurb-project-folder-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let folder = root.join("projects");
        std::fs::create_dir_all(folder.join("alpha/parts")).unwrap();
        std::fs::create_dir_all(folder.join("beta/parts")).unwrap();
        std::fs::create_dir_all(folder.join("not-a-project")).unwrap();
        std::fs::create_dir_all(folder.join("group/nested/parts")).unwrap();

        let registry = Registry::load(&root);
        let loaded = register_projects_in_folder(&registry, folder).unwrap();

        assert_eq!(loaded.len(), 2);
        assert_eq!(
            registry
                .list()
                .into_iter()
                .map(|view| view.project.name)
                .collect::<Vec<_>>(),
            ["alpha", "beta"]
        );
        // Swept-in projects were never opened, so none of them may win the
        // launch-time "most recently opened" restore.
        assert!(registry
            .list()
            .iter()
            .all(|view| view.project.last_opened == 0));
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn part_views_include_sources_that_are_still_building() {
        let root = std::env::temp_dir().join(format!(
            "nurb-part-views-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let parts = root.join("parts");
        std::fs::create_dir_all(&parts).unwrap();
        std::fs::write(parts.join("alpha.py"), "").unwrap();
        std::fs::write(parts.join("broken.py"), "").unwrap();
        std::fs::write(parts.join("rig.py"), "").unwrap();
        std::fs::write(parts.join("_helper.py"), "").unwrap();

        std::fs::write(parts.join("held.py"), "").unwrap();

        let views = part_views(
            &root,
            r#"[{"name":"broken","error":"trace"},{"name":"gone","error":null},
                {"name":"held","error":"hole too small","refused":"hole"},
                {"name":"alpha","error":null,"variant":"tall",
                 "variants":[{"name":"tall","params":{"height":200.0},"note":"the pantry"}]},
                {"name":"rig","error":null,"joints":[],"uses":["alpha"]}]"#,
        )
        .unwrap();

        assert_eq!(
            views,
            serde_json::json!([
                { "name": "alpha", "error": null, "refused": false, "assembly": false, "uses": [],
                  "variants": [{ "name": "tall", "params": { "height": 200.0 }, "note": "the pantry" }],
                  "variant": "tall" },
                { "name": "broken", "error": "trace", "refused": false, "assembly": false, "uses": [], "variants": [], "variant": null },
                { "name": "held", "error": "hole too small", "refused": true, "assembly": false, "uses": [], "variants": [], "variant": null },
                { "name": "rig", "error": null, "refused": false, "assembly": true, "uses": ["alpha"], "variants": [], "variant": null }
            ])
        );
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn transport_errors_still_evict_the_live_chat_session() {
        let failed = Err(agent_client_protocol::Error::internal_error());
        let live = Some("session-1".to_string());

        assert_eq!(
            super::acp::session_to_remove(&failed, &live).as_deref(),
            Some("session-1")
        );
        assert_eq!(super::acp::session_to_remove(&Ok(None), &live), None);
    }
}
