//! What the chat column runs on: the model and effort the user picked, and the
//! last lists the agent offered, both per agent.
//!
//! Nothing is stored until the user chooses something. That matters: Claude
//! Code already picks by plan (Sonnet 5 on a Pro subscription, Opus 5 on Max),
//! and an app that hardcoded a model would either spend a Max user's plan on
//! the cheaper one or spend a Pro user's on the dearer. An empty store means
//! "whatever the agent would have run on its own".
//!
//! The option lists are cached because a part's chat has no adapter until its
//! first message, and the picker has to draw before then.

use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

use serde::{Deserialize, Serialize};

/// The option categories the picker draws, in the order they are applied: the
/// model leads, because the effort list an agent offers depends on it.
///
/// Categories, not option ids, because the ids are per agent and picking by id
/// silently drops agents that name the same thing differently: Claude calls its
/// effort option `effort`, Codex calls it `reasoning_effort`, and both tag it
/// `thought_level`. Everything else an adapter offers (permission mode, Codex's
/// collaboration mode, fast mode, a subagent picker) stays session-local.
pub const SHOWN: [&str; 2] = ["model", "thought_level"];

/// One select the picker draws, flattened out of ACP's `SessionConfigOption`
/// so the cache and the webview share a shape. The category is the stable key
/// across agents; the id is what `session/set_config_option` wants back.
#[derive(Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ConfigRow {
    pub id: String,
    /// Defaulted so that changing this shape costs a stale cache and not the
    /// user's actual picks: without it one unreadable row fails the whole file.
    #[serde(default)]
    pub category: String,
    pub name: String,
    pub value: String,
    pub options: Vec<ConfigChoice>,
}

#[derive(Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ConfigChoice {
    pub value: String,
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

#[derive(Serialize, Deserialize, Clone, Default)]
#[serde(rename_all = "camelCase")]
struct AgentPrefs {
    /// Category to chosen value, for the categories in [`SHOWN`].
    #[serde(default)]
    chosen: HashMap<String, String>,
    #[serde(default)]
    rows: Vec<ConfigRow>,
}

pub struct PrefStore {
    file: PathBuf,
    agents: Mutex<HashMap<String, AgentPrefs>>,
}

impl PrefStore {
    pub fn load(dir: &Path) -> Self {
        let file = dir.join("agent-config.json");
        let agents = fs::read_to_string(&file)
            .ok()
            .and_then(|text| serde_json::from_str(&text).ok())
            .unwrap_or_default();
        Self {
            file,
            agents: Mutex::new(agents),
        }
    }

    /// The user's picks as (category, value), in [`SHOWN`] order, to apply to a
    /// new session.
    pub fn chosen(&self, agent: &str) -> Vec<(String, String)> {
        let agents = self.agents.lock().unwrap();
        let Some(prefs) = agents.get(agent) else {
            return Vec::new();
        };
        SHOWN
            .iter()
            .filter_map(|category| {
                prefs
                    .chosen
                    .get(*category)
                    .map(|value| ((*category).to_string(), value.clone()))
            })
            .collect()
    }

    /// What the picker draws with no session running: the cached lists, showing
    /// the user's picks rather than whatever the last session happened to end on.
    pub fn rows(&self, agent: &str) -> Vec<ConfigRow> {
        let agents = self.agents.lock().unwrap();
        let Some(prefs) = agents.get(agent) else {
            return Vec::new();
        };
        prefs
            .rows
            .iter()
            .filter(|row| !row.category.is_empty())
            .map(|row| match prefs.chosen.get(&row.category) {
                Some(value) => ConfigRow {
                    value: value.clone(),
                    ..row.clone()
                },
                None => row.clone(),
            })
            .collect()
    }

    pub fn remember(&self, agent: &str, category: &str, value: &str) {
        if !SHOWN.contains(&category) {
            return;
        }
        let mut agents = self.agents.lock().unwrap();
        agents
            .entry(agent.to_string())
            .or_default()
            .chosen
            .insert(category.to_string(), value.to_string());
        self.save(&agents);
    }

    /// Keep the lists a live session reported, for the next picker to draw.
    pub fn cache(&self, agent: &str, rows: Vec<ConfigRow>) {
        if rows.is_empty() {
            return;
        }
        let mut agents = self.agents.lock().unwrap();
        agents.entry(agent.to_string()).or_default().rows = rows;
        self.save(&agents);
    }

    /// Write-then-rename so a crash mid-write never eats the store.
    fn save(&self, agents: &HashMap<String, AgentPrefs>) {
        let tmp = self.file.with_extension("json.tmp");
        let text = serde_json::to_string_pretty(agents).expect("agent config serializes");
        if fs::write(&tmp, text)
            .and_then(|_| fs::rename(&tmp, &self.file))
            .is_err()
        {
            let _ = fs::remove_file(&tmp);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{ConfigChoice, ConfigRow, PrefStore};
    use std::path::PathBuf;

    fn scratch(name: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "nurb-prefs-{name}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir_all(&dir).unwrap();
        dir
    }

    fn row(id: &str, category: &str, value: &str) -> ConfigRow {
        ConfigRow {
            id: id.into(),
            category: category.into(),
            name: id.into(),
            value: value.into(),
            options: vec![ConfigChoice {
                value: value.into(),
                name: value.into(),
                description: None,
            }],
        }
    }

    #[test]
    fn nothing_is_stored_until_the_user_chooses() {
        let dir = scratch("empty");
        let store = PrefStore::load(&dir);
        assert!(store.chosen("claude").is_empty());
        assert!(store.rows("claude").is_empty());
    }

    #[test]
    fn picks_survive_a_reload_and_lead_with_the_model() {
        let dir = scratch("picks");
        let store = PrefStore::load(&dir);
        // Written out of order on purpose: applying effort before model would
        // set it against the wrong model's list.
        store.remember("claude", "thought_level", "low");
        store.remember("claude", "model", "sonnet");
        store.remember("claude", "mode", "plan");

        let reloaded = PrefStore::load(&dir);
        assert_eq!(
            reloaded.chosen("claude"),
            vec![
                ("model".to_string(), "sonnet".to_string()),
                ("thought_level".to_string(), "low".to_string()),
            ]
        );
        // Permission mode is session-local, so it is never written.
        assert!(reloaded.chosen("codex").is_empty());
    }

    /// The two agents name the same option differently; the category is what
    /// makes one store work for both.
    #[test]
    fn each_agent_keeps_its_own_picks_under_a_shared_category() {
        let dir = scratch("agents");
        let store = PrefStore::load(&dir);
        store.remember("claude", "thought_level", "low");
        store.remember("codex", "thought_level", "high");
        store.cache("claude", vec![row("effort", "thought_level", "xhigh")]);
        store.cache("codex", vec![row("reasoning_effort", "thought_level", "medium")]);

        let reloaded = PrefStore::load(&dir);
        assert_eq!(reloaded.rows("claude")[0].id, "effort");
        assert_eq!(reloaded.rows("claude")[0].value, "low");
        assert_eq!(reloaded.rows("codex")[0].id, "reasoning_effort");
        assert_eq!(reloaded.rows("codex")[0].value, "high");
    }

    /// A cache written by an older shape must cost the cache and nothing else.
    /// The picks are the part worth keeping, and the next project open rewrites
    /// the rows anyway.
    #[test]
    fn a_stale_cache_is_dropped_without_taking_the_picks_with_it() {
        let dir = scratch("stale");
        std::fs::write(
            dir.join("agent-config.json"),
            r#"{"claude":{"chosen":{"model":"sonnet"},
                 "rows":[{"id":"model","name":"Model","value":"opus[1m]","options":[]}]}}"#,
        )
        .unwrap();

        let store = PrefStore::load(&dir);
        assert_eq!(
            store.chosen("claude"),
            vec![("model".to_string(), "sonnet".to_string())]
        );
        assert!(store.rows("claude").is_empty());
    }

    #[test]
    fn cached_rows_show_the_users_pick_not_the_last_session() {
        let dir = scratch("cache");
        let store = PrefStore::load(&dir);
        store.cache("claude", vec![row("model", "model", "opus[1m]")]);
        store.remember("claude", "model", "sonnet");

        let rows = PrefStore::load(&dir).rows("claude");
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].value, "sonnet");
    }
}
