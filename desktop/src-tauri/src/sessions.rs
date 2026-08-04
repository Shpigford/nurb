use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

use serde::{Deserialize, Serialize};

/// The thin app-owned sidecar to the agent's session store: what ACP cannot
/// tell us about a session, keyed by its sessionId. The agent owns the
/// transcript, title, and timestamps; this only carries what the app itself
/// decided (which agent ran it, which part was on screen).
pub struct SessionStore {
    file: PathBuf,
    sessions: Mutex<HashMap<String, SessionMeta>>,
    part_chats_file: PathBuf,
    part_chats: Mutex<Vec<PartChat>>,
}

#[derive(Serialize, Deserialize, Clone, Default)]
#[serde(rename_all = "camelCase")]
pub struct SessionMeta {
    pub agent: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub part: Option<String>,
}

/// The conversation currently attached to a part. `None` is a durable
/// "start fresh": older sessions stay in history but must not reattach on the
/// next launch before the new conversation receives its first prompt.
#[derive(Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
struct PartChat {
    project: PathBuf,
    part: String,
    session_id: Option<String>,
}

impl SessionStore {
    pub fn load(dir: &Path) -> Self {
        let file = dir.join("sessions.json");
        let sessions = fs::read_to_string(&file)
            .ok()
            .and_then(|text| serde_json::from_str(&text).ok())
            .unwrap_or_default();
        let part_chats_file = dir.join("part-chats.json");
        let part_chats = fs::read_to_string(&part_chats_file)
            .ok()
            .and_then(|text| serde_json::from_str(&text).ok())
            .unwrap_or_default();
        Self {
            file,
            sessions: Mutex::new(sessions),
            part_chats_file,
            part_chats: Mutex::new(part_chats),
        }
    }

    /// The part on screen when the session last took a prompt; recorded per
    /// send so reopening the session can restore the viewer.
    pub fn record(&self, session_id: &str, agent: &str, project: &Path, part: Option<String>) {
        {
            let mut sessions = self.sessions.lock().unwrap();
            let meta = sessions.entry(session_id.to_string()).or_default();
            meta.agent = agent.to_string();
            if part.is_some() {
                meta.part = part.clone();
            }
            self.save_sessions(&sessions);
        }
        if let Some(part) = part {
            self.select_part_chat(project, &part, Some(session_id.to_string()));
        }
    }

    pub fn part_of(&self, session_id: &str, project: &Path) -> Option<String> {
        let part = self
            .sessions
            .lock()
            .unwrap()
            .get(session_id)
            .and_then(|meta| meta.part.clone())?;
        let part_chats = self.part_chats.lock().unwrap();
        match part_chats
            .iter()
            .find(|chat| chat.project == project && chat.part == part)
        {
            Some(chat) if chat.session_id.as_deref() == Some(session_id) => Some(part),
            Some(_) => None,
            // Existing metadata predates the current-session pointer. Preserve
            // its old newest-session behavior until the user picks or clears it.
            None => Some(part),
        }
    }

    pub fn select_part_chat(&self, project: &Path, part: &str, session_id: Option<String>) {
        let mut part_chats = self.part_chats.lock().unwrap();
        match part_chats
            .iter_mut()
            .find(|chat| chat.project == project && chat.part == part)
        {
            Some(chat) => chat.session_id = session_id,
            None => part_chats.push(PartChat {
                project: project.to_path_buf(),
                part: part.to_string(),
                session_id,
            }),
        }
        self.save_part_chats(&part_chats);
    }

    fn save_sessions(&self, sessions: &HashMap<String, SessionMeta>) {
        // Write-then-rename so a crash mid-write never eats the store.
        let tmp = self.file.with_extension("json.tmp");
        let text = serde_json::to_string_pretty(sessions).expect("session store serializes");
        if fs::write(&tmp, text)
            .and_then(|_| fs::rename(&tmp, &self.file))
            .is_err()
        {
            eprintln!("[sessions] could not save {}", self.file.display());
        }
    }

    fn save_part_chats(&self, part_chats: &[PartChat]) {
        let tmp = self.part_chats_file.with_extension("json.tmp");
        let text = serde_json::to_string_pretty(part_chats).expect("part chats serialize");
        if fs::write(&tmp, text)
            .and_then(|_| fs::rename(&tmp, &self.part_chats_file))
            .is_err()
        {
            eprintln!(
                "[sessions] could not save {}",
                self.part_chats_file.display()
            );
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn record_and_reload_roundtrip() {
        let dir = std::env::temp_dir().join(format!(
            "nurb-sessions-test-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&dir).unwrap();
        let project = PathBuf::from("/tmp/project");

        let store = SessionStore::load(&dir);
        store.record("s1", "claude", &project, Some("bracket".into()));
        // A part-less prompt must not erase the remembered part.
        store.record("s1", "claude", &project, None);
        assert_eq!(store.part_of("s1", &project).as_deref(), Some("bracket"));
        assert_eq!(store.part_of("missing", &project), None);

        // Starting fresh suppresses the old conversation across reloads.
        store.select_part_chat(&project, "bracket", None);
        assert_eq!(store.part_of("s1", &project), None);

        let reloaded = SessionStore::load(&dir);
        assert_eq!(reloaded.part_of("s1", &project), None);

        // The next real session becomes the durable conversation for the part.
        reloaded.record("s2", "codex", &project, Some("bracket".into()));
        assert_eq!(reloaded.part_of("s2", &project).as_deref(), Some("bracket"));
        assert_eq!(reloaded.part_of("s1", &project), None);
        fs::remove_dir_all(dir).unwrap();
    }
}
