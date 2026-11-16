//! A short name for a new part, from the person's own agent, while the real
//! turn is still thinking. Until the agent writes the part it has no name, and
//! the opening words of a prompt make a poor header ("I want to make a banana
//! airpod pro…"). One single-turn call to the agent the chat runs on, on its
//! cheapest model where the CLI lets us pick one, so nothing needs a key or a
//! subscription the person does not already have. Any failure is silent: the
//! prompt's words stay until the agent names the part itself.

use std::time::Duration;

use tauri::Manager;

use crate::acp::sandbox;
use crate::agents::AgentKind;

const ASK: &str = "Name the 3D-printable part this person wants in 2 to 4 plain words, \
title case, no quotes. Reply with the name and nothing else.\n\nWhat they said: ";

/// The CLI invocation for one single-turn answer, or None when this agent has
/// no way to give one here.
fn command(launcher: &crate::env::Launcher, kind: AgentKind, prompt: String) -> Option<(String, Vec<String>)> {
    let native = || kind.native_bin().map(|bin| bin.to_string_lossy().into_owned());
    let args = |list: &[&str]| list.iter().map(|arg| arg.to_string()).collect::<Vec<_>>();
    Some(match kind {
        AgentKind::Claude => {
            let mut a = args(&["-p", "--model", "haiku", "--tools", "", "--no-session-persistence", "--setting-sources", "", "--strict-mcp-config"]);
            a.push(prompt);
            (native()?, a)
        }
        AgentKind::Codex => {
            let mut a = args(&["exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only", "-c", "model_reasoning_effort=\"low\""]);
            a.push(prompt);
            match launcher.paths() {
                // The CLI the Codex adapter installed beside itself, run by the
                // provisioned node rather than whatever `env node` finds.
                Some(paths) => {
                    let mut with_script = vec![paths.codex_cli().to_string_lossy().into_owned()];
                    with_script.extend(a);
                    (paths.node_bin().to_string_lossy().into_owned(), with_script)
                }
                None => ("codex".into(), a),
            }
        }
        AgentKind::Gemini => {
            // The adapter is Gemini's own CLI; drop the ACP flag the launcher adds.
            let (program, mut a) = launcher.adapter(kind);
            a.retain(|arg| arg != "--acp");
            a.push("-p".into());
            a.push(prompt);
            (program, a)
        }
        AgentKind::Cursor => {
            let mut a = args(&["-p", "--output-format", "text"]);
            a.push(prompt);
            (native()?, a)
        }
        AgentKind::Grok => (native()?, vec!["-p".into(), prompt]),
    })
}

/// The model's answer as a title, or None when it is not one: a refusal, a
/// question back, or a paragraph.
fn title_from(output: &str) -> Option<String> {
    let line = output.lines().map(str::trim).filter(|line| !line.is_empty()).last()?;
    let title = line.trim_matches(|c: char| c == '"' || c == '\'' || c == '*' || c == '.' || c.is_whitespace());
    let words = title.split_whitespace().count();
    (1..=6).contains(&words).then(|| title.to_string()).filter(|t| t.len() <= 60 && !t.contains('?'))
}

#[tauri::command]
pub async fn name_part(app: tauri::AppHandle, agent: String, text: String) -> Option<String> {
    let kind = AgentKind::parse(&agent).ok()?;
    let text = text.trim();
    if text.is_empty() {
        return None;
    }
    let launcher = app.state::<crate::env::Launcher>().inner().clone();
    let (program, args) = command(&launcher, kind, format!("{ASK}{}", text.chars().take(2000).collect::<String>()))?;
    // A scratch folder to stand in, under the same sandbox every agent runs in.
    let cwd = std::env::temp_dir().join("nurb-naming");
    std::fs::create_dir_all(&cwd).ok()?;
    let (program, args) = sandbox::wrap(program, args, &cwd, &launcher.engine_root());
    let mut command = tokio::process::Command::new(program);
    command
        .args(args)
        .env("PATH", launcher.adapter_path().unwrap_or_else(|| crate::env::user_path().into()))
        .current_dir(&cwd)
        .stdin(std::process::Stdio::null())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null())
        .kill_on_drop(true);
    if kind == AgentKind::Gemini {
        command.env("GEMINI_API_KEY", crate::agents::gemini_api_key().ok()?);
    }
    let output = tokio::time::timeout(Duration::from_secs(45), command.output()).await.ok()?.ok()?;
    if !output.status.success() {
        return None;
    }
    title_from(&String::from_utf8_lossy(&output.stdout))
}

#[cfg(test)]
mod tests {
    use super::title_from;

    #[test]
    fn only_a_short_answer_is_a_title() {
        assert_eq!(title_from("Banana AirPods Pro Holder\n").as_deref(), Some("Banana AirPods Pro Holder"));
        assert_eq!(title_from("  \"Door Wedge.\"  ").as_deref(), Some("Door Wedge"));
        assert_eq!(title_from("thinking...\n**Shelf Bracket**").as_deref(), Some("Shelf Bracket"));
        assert_eq!(title_from("Could you tell me more about what it holds?"), None);
        assert_eq!(title_from("I would call this part something like a holder for your earbuds case"), None);
        assert_eq!(title_from(""), None);
    }
}
