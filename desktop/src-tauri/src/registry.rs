use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

/// The app-owned project index. Folders on disk stay the source of truth; this
/// is only what the rail lists, so a missing folder is a removable dead entry,
/// never an error.
pub struct Registry {
    file: PathBuf,
    projects: Mutex<Vec<Project>>,
}

#[derive(Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct Project {
    pub name: String,
    pub path: PathBuf,
    pub last_opened: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_part: Option<String>,
}

/// What the rail renders: a registry entry plus whether its folder still exists.
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProjectView {
    #[serde(flatten)]
    pub project: Project,
    pub missing: bool,
}

impl Registry {
    pub fn load(dir: &Path) -> Self {
        let file = dir.join("projects.json");
        let projects = fs::read_to_string(&file)
            .ok()
            .and_then(|text| serde_json::from_str(&text).ok())
            .unwrap_or_default();
        Self {
            file,
            projects: Mutex::new(projects),
        }
    }

    pub fn list(&self) -> Vec<ProjectView> {
        let mut projects = self.projects.lock().unwrap().clone();
        // The rail lists alphabetically; last_opened still decides which
        // project the app restores at launch.
        projects.sort_by_key(|project| project.name.to_lowercase());
        projects
            .into_iter()
            .map(|project| ProjectView {
                missing: !project.path.is_dir(),
                project,
            })
            .collect()
    }

    /// Insert or refresh an entry, keyed by path, and mark it just-opened.
    pub fn upsert(&self, name: &str, path: &Path, selected_part: Option<String>) {
        let mut projects = self.projects.lock().unwrap();
        match projects.iter_mut().find(|p| p.path == path) {
            Some(existing) => {
                existing.last_opened = now_ms();
                if selected_part.is_some() {
                    existing.selected_part = selected_part;
                }
            }
            None => projects.push(Project {
                name: name.to_string(),
                path: path.to_path_buf(),
                last_opened: now_ms(),
                selected_part,
            }),
        }
        self.save(&projects);
    }

    pub fn touch(&self, path: &Path) {
        let mut projects = self.projects.lock().unwrap();
        if let Some(project) = projects.iter_mut().find(|p| p.path == path) {
            project.last_opened = now_ms();
            self.save(&projects);
        }
    }

    pub fn remove(&self, path: &Path) {
        let mut projects = self.projects.lock().unwrap();
        projects.retain(|p| p.path != path);
        self.save(&projects);
    }

    pub fn select_part(&self, path: &Path, part: Option<String>) {
        let mut projects = self.projects.lock().unwrap();
        if let Some(project) = projects.iter_mut().find(|p| p.path == path) {
            project.selected_part = part;
            self.save(&projects);
        }
    }

    fn save(&self, projects: &[Project]) {
        // Write-then-rename so a crash mid-write never eats the registry.
        let tmp = self.file.with_extension("json.tmp");
        let text = serde_json::to_string_pretty(projects).expect("registry serializes");
        if fs::write(&tmp, text)
            .and_then(|_| fs::rename(&tmp, &self.file))
            .is_err()
        {
            eprintln!("[registry] could not save {}", self.file.display());
        }
    }
}

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis() as u64)
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_upsert_remove_and_selection() {
        let dir = std::env::temp_dir().join(format!("nurb-registry-test-{}", std::process::id()));
        fs::create_dir_all(&dir).unwrap();
        let path = PathBuf::from("/tmp/some-project");

        let registry = Registry::load(&dir);
        registry.upsert("some-project", &path, Some("bracket".into()));
        registry.upsert("some-project", &path, None); // re-open, not a duplicate
        registry.select_part(&path, Some("shelf".into()));

        // Opening bumps recency: touch must move lastOpened forward.
        let before = registry.list()[0].project.last_opened;
        std::thread::sleep(std::time::Duration::from_millis(5));
        registry.touch(&path);
        assert!(registry.list()[0].project.last_opened > before);

        let reloaded = Registry::load(&dir);
        let listed = reloaded.list();
        assert_eq!(listed.len(), 1);
        assert_eq!(listed[0].project.name, "some-project");
        assert_eq!(listed[0].project.selected_part.as_deref(), Some("shelf"));
        assert!(listed[0].missing);

        reloaded.remove(&path);
        assert!(Registry::load(&dir).list().is_empty());
        fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn lists_alphabetically_regardless_of_recency() {
        let dir = std::env::temp_dir().join(format!("nurb-registry-sort-{}", std::process::id()));
        fs::create_dir_all(&dir).unwrap();
        let registry = Registry::load(&dir);
        registry.upsert("Zeta", &PathBuf::from("/tmp/zeta"), None);
        registry.upsert("alpha", &PathBuf::from("/tmp/alpha"), None);
        let names: Vec<_> = registry
            .list()
            .into_iter()
            .map(|view| view.project.name)
            .collect();
        assert_eq!(names, ["alpha", "Zeta"]);
        fs::remove_dir_all(&dir).unwrap();
    }
}
