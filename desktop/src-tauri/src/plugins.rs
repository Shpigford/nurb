//! The engine plugin registry surface: status for the Settings panel and the
//! per-project enable/disable toggle.
//!
//! The engine (Python) owns plugin loading. The app owns only two things:
//! showing what the engine reports, and persisting the user's on/off choice in
//! the same file the engine reads. Status comes from the running dev server's
//! `/api/plugins` (the same seam `list_parts` uses), so the app never parses a
//! manifest and cannot drift from what the engine actually loaded. The toggle
//! writes `<project>/.nurb/plugins.toml`, which the engine's loader and the
//! `nurb plugin enable|disable` CLI both read, so the two surfaces agree.

use std::path::{Path, PathBuf};
use tauri::Manager;

/// Fetch plugin status from the project's running dev server.
#[tauri::command]
pub async fn plugin_statuses(
    app: tauri::AppHandle,
    path: String,
) -> Result<serde_json::Value, String> {
    let project = PathBuf::from(&path);
    let port = app
        .state::<crate::supervisor::Supervisor>()
        .port(&project)
        .ok_or("project is not open")?;
    let body = tauri::async_runtime::spawn_blocking(move || crate::http_get(port, "/api/plugins"))
        .await
        .map_err(|e| e.to_string())??;
    serde_json::from_str(&body).map_err(|e| format!("bad /api/plugins response: {e}"))
}

/// Flip a plugin's enabled state for a project. Writes the state file the
/// engine reads; unknown ids are accepted (the engine ignores ids it does not
/// know, and the Settings panel only offers ids the server reported).
#[tauri::command]
pub fn set_plugin_enabled(path: String, id: String, enabled: bool) -> Result<(), String> {
    set_enabled(Path::new(&path), &id, enabled)
}

/// Persist whether a plugin is enabled for the project at `path`.
///
/// The file is `<path>/.nurb/plugins.toml`, one table:
///
/// ```toml
/// [plugins]
/// disabled = ["everything"]
/// ```
///
/// The file is engine-managed and rewritten wholesale (sorted), matching what
/// the Python `set_enabled` writes.
pub fn set_enabled(path: &Path, id: &str, enabled: bool) -> Result<(), String> {
    let state_file = path.join(".nurb").join("plugins.toml");
    let mut disabled: Vec<String> = Vec::new();
    if state_file.is_file() {
        let text = std::fs::read_to_string(&state_file).map_err(|e| e.to_string())?;
        if let Ok(value) = text.parse::<toml::Value>() {
            if let Some(list) = value
                .get("plugins")
                .and_then(|v| v.as_table())
                .and_then(|section| section.get("disabled"))
                .and_then(|v| v.as_array())
            {
                disabled = list
                    .iter()
                    .filter_map(|v| v.as_str().map(String::from))
                    .collect();
            }
        }
    }
    if enabled {
        disabled.retain(|d| d != id);
    } else if !disabled.iter().any(|d| d == id) {
        disabled.push(id.to_string());
    }
    disabled.sort();
    let listed = disabled
        .iter()
        .map(|d| format!("\"{}\"", d.replace('\\', "\\\\").replace('"', "\\\"")))
        .collect::<Vec<_>>()
        .join(", ");
    let body = format!("[plugins]\ndisabled = [{listed}]\n");
    if let Some(parent) = state_file.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    std::fs::write(&state_file, body).map_err(|e| e.to_string())?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn set_enabled_persists_disabled_and_enables_again() {
        let dir = std::env::temp_dir().join(format!("nurb-plugin-state-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        set_enabled(&dir, "everything", false).unwrap();
        let text = std::fs::read_to_string(dir.join(".nurb/plugins.toml")).unwrap();
        assert!(text.contains("everything"));
        set_enabled(&dir, "everything", true).unwrap();
        let text = std::fs::read_to_string(dir.join(".nurb/plugins.toml")).unwrap();
        assert!(!text.contains("everything"));
        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn set_enabled_keeps_multiple_ids_and_preserves_existing_file() {
        let dir = std::env::temp_dir().join(format!("nurb-plugin-state2-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        // A file written by the Python side has the same shape; the Rust side
        // must read it and add to it rather than overwriting.
        std::fs::create_dir_all(dir.join(".nurb")).unwrap();
        std::fs::write(
            dir.join(".nurb").join("plugins.toml"),
            "[plugins]\ndisabled = [\"a\"]\n",
        )
        .unwrap();
        set_enabled(&dir, "b", false).unwrap();
        let text = std::fs::read_to_string(dir.join(".nurb/plugins.toml")).unwrap();
        assert!(text.contains("\"a\"") && text.contains("\"b\""));
        set_enabled(&dir, "a", true).unwrap();
        let text = std::fs::read_to_string(dir.join(".nurb/plugins.toml")).unwrap();
        assert!(!text.contains("\"a\""));
        assert!(text.contains("\"b\""));
        std::fs::remove_dir_all(&dir).unwrap();
    }
}
