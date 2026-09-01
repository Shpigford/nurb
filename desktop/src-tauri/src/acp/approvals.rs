//! The one thing the user gets to decide about permissions: whether the app
//! may answer them on their behalf in a given project. The default is not a
//! preference, it is a fact about the machine. Where sandbox.rs confines the
//! adapter the app answers yes and the kernel catches whatever the agent gets
//! wrong; where it does not, the app has nothing to fall back on and asks.
//!
//! Keyed on the project path exactly as the registry stores it, never
//! canonicalized (see lib.rs), so a moved or renamed project is a project
//! nobody has answered for yet. That is the right default rather than an
//! oversight: the path is the only identity the app has, losing the grant
//! costs one click, and keeping it across a move could carry a yes onto files
//! the user never saw.
//!
//! Nothing is written until the user answers something, so an install that
//! never meets a dialog never grows a file.

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};

use serde::{Deserialize, Serialize};

/// Whether a project nobody has answered for may be answered for. The
/// platform picks this, not the user: it is exactly whether the adapter runs
/// confined.
const DEFAULT_AUTO: bool = super::sandbox::CONFINED;

/// Cloned into the permission handler, which is built before the chat is
/// registered and must still see a flip the user makes mid-turn, so the state
/// has to be shared rather than snapshotted.
#[derive(Clone)]
pub struct Approvals(Arc<Inner>);

struct Inner {
    file: PathBuf,
    projects: Mutex<Vec<ProjectApproval>>,
}

#[derive(Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
struct ProjectApproval {
    project: PathBuf,
    auto: bool,
}

impl Approvals {
    pub fn load(dir: &Path) -> Self {
        let file = dir.join("approvals.json");
        let projects = fs::read_to_string(&file)
            .ok()
            .and_then(|text| serde_json::from_str(&text).ok())
            .unwrap_or_default();
        Self(Arc::new(Inner {
            file,
            projects: Mutex::new(projects),
        }))
    }

    /// Whether the app may answer permission requests itself in this project.
    pub fn auto(&self, project: &Path) -> bool {
        self.0
            .projects
            .lock()
            .unwrap()
            .iter()
            .find(|entry| entry.project == project)
            .map_or(DEFAULT_AUTO, |entry| entry.auto)
    }

    /// Whether the OS confines the adapter on this machine. The UI's copy
    /// turns on this rather than on a user-agent sniff, so the shell cannot
    /// disagree with the kernel about what is protecting the user.
    pub fn confined(&self) -> bool {
        super::sandbox::CONFINED
    }

    pub fn set(&self, project: &Path, auto: bool) {
        let mut projects = self.0.projects.lock().unwrap();
        match projects.iter_mut().find(|entry| entry.project == project) {
            Some(entry) => entry.auto = auto,
            None => projects.push(ProjectApproval {
                project: project.to_path_buf(),
                auto,
            }),
        }
        self.save(&projects);
    }

    /// A project the app no longer knows about keeps no standing yes, so
    /// removing a folder and adding a different one in its place cannot
    /// inherit the answer.
    pub fn forget(&self, project: &Path) {
        let mut projects = self.0.projects.lock().unwrap();
        let before = projects.len();
        projects.retain(|entry| entry.project != project);
        if projects.len() != before {
            self.save(&projects);
        }
    }

    fn save(&self, projects: &[ProjectApproval]) {
        // Write-then-rename so a crash mid-write never eats the store.
        let tmp = self.0.file.with_extension("json.tmp");
        let text = serde_json::to_string_pretty(projects).expect("approvals serialize");
        if fs::write(&tmp, text)
            .and_then(|_| fs::rename(&tmp, &self.0.file))
            .is_err()
        {
            eprintln!("[approvals] could not save {}", self.0.file.display());
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn scratch(name: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "nurb-approvals-{name}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn a_project_defaults_to_what_the_sandbox_can_promise() {
        // The whole point of the fix: the answer the app gives itself is tied
        // to whether anything is actually enforcing it.
        let dir = scratch("default");
        let store = Approvals::load(&dir);
        assert_eq!(store.auto(Path::new("/tmp/project")), super::DEFAULT_AUTO);
        assert_eq!(store.confined(), super::DEFAULT_AUTO);
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn a_grant_survives_a_reload() {
        let dir = scratch("reload");
        let project = PathBuf::from("/tmp/project");
        let store = Approvals::load(&dir);
        store.set(&project, true);
        assert!(store.auto(&project));
        assert!(Approvals::load(&dir).auto(&project));

        // And it can be taken back.
        store.set(&project, false);
        assert!(!Approvals::load(&dir).auto(&project));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn a_moved_project_has_not_been_answered_for() {
        let dir = scratch("moved");
        let store = Approvals::load(&dir);
        store.set(Path::new("/tmp/project"), true);
        assert_eq!(
            store.auto(Path::new("/tmp/project-renamed")),
            super::DEFAULT_AUTO
        );
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn forgetting_a_project_drops_its_grant() {
        let dir = scratch("forget");
        let project = PathBuf::from("/tmp/project");
        let store = Approvals::load(&dir);
        store.set(&project, true);
        store.forget(&project);
        assert_eq!(store.auto(&project), super::DEFAULT_AUTO);
        assert_eq!(Approvals::load(&dir).auto(&project), super::DEFAULT_AUTO);
        fs::remove_dir_all(dir).unwrap();
    }
}
