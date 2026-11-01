//! nurb 0.x kept the user's project folders in `projects.json` in this same
//! data directory. The update lands on the same bundle id, so the folders are
//! still on disk and only the list is lost. This hands that list to the page
//! once, for it to import.

use std::fs;
use std::path::{Path, PathBuf};

#[derive(serde::Deserialize)]
struct V1Project {
    path: PathBuf,
}

/// The v1 folders that still hold `parts/`, deduplicated. The file is renamed
/// before anything is imported, so a second launch, or a second call from the
/// same page, gets nothing back. A crash mid-import costs the rest of the list
/// rather than a library of duplicates, and the folders are still there for
/// Import folder.
pub fn take_folders(dir: &Path) -> Vec<String> {
    let file = dir.join("projects.json");
    let Ok(text) = fs::read_to_string(&file) else {
        return Vec::new();
    };
    if let Err(e) = fs::rename(&file, dir.join("projects.v1-imported.json")) {
        eprintln!("[v1] could not mark {} imported: {e}", file.display());
        return Vec::new();
    }
    let projects: Vec<V1Project> = match serde_json::from_str(&text) {
        Ok(projects) => projects,
        Err(e) => {
            eprintln!("[v1] could not read {}: {e}", file.display());
            return Vec::new();
        }
    };
    let mut folders: Vec<String> = Vec::new();
    for project in projects {
        if !project.path.join("parts").is_dir() {
            eprintln!("[v1] skipping {}: no parts/ there", project.path.display());
            continue;
        }
        let path = project.path.to_string_lossy().into_owned();
        if !folders.contains(&path) {
            folders.push(path);
        }
    }
    folders
}

#[cfg(test)]
mod tests {
    use super::take_folders;
    use std::fs;

    #[test]
    fn hands_over_live_folders_once() {
        let dir = std::env::temp_dir().join(format!("nurb-v1-{}", std::process::id()));
        let alpha = dir.join("alpha");
        fs::create_dir_all(alpha.join("parts")).unwrap();
        fs::create_dir_all(dir.join("no-parts")).unwrap();
        let registry = serde_json::json!([
            { "name": "alpha", "path": alpha, "lastOpened": 5, "selectedPart": "bracket" },
            { "name": "alpha again", "path": alpha, "lastOpened": 0 },
            { "name": "empty", "path": dir.join("no-parts"), "lastOpened": 0 },
            { "name": "gone", "path": dir.join("deleted"), "lastOpened": 0 },
        ]);
        fs::write(dir.join("projects.json"), registry.to_string()).unwrap();

        assert_eq!(take_folders(&dir), [alpha.to_string_lossy()]);
        assert!(!dir.join("projects.json").exists());
        assert!(dir.join("projects.v1-imported.json").exists());
        assert!(take_folders(&dir).is_empty());

        fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn no_registry_and_a_broken_one_both_hand_over_nothing() {
        let dir = std::env::temp_dir().join(format!("nurb-v1-broken-{}", std::process::id()));
        fs::create_dir_all(&dir).unwrap();
        assert!(take_folders(&dir).is_empty());

        fs::write(dir.join("projects.json"), "not json").unwrap();
        assert!(take_folders(&dir).is_empty());
        // Marked anyway, so a file v2 cannot read is not retried every launch.
        assert!(!dir.join("projects.json").exists());

        fs::remove_dir_all(&dir).unwrap();
    }
}
