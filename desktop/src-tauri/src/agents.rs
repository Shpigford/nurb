//! The agents the app can host, and everything that differs between them:
//! how their ACP process starts, display name, sign-in state, and the login
//! flow.
//!
//! Claude and Codex run through npm adapters the app provisions; each bundles
//! its agent's real CLI (claude-agent-acp carries the native Claude Code
//! binary, codex-acp carries @openai/codex). Gemini's official CLI speaks ACP
//! itself and is provisioned beside them, so nothing has to be on the user's
//! PATH except node/npx. Cursor and Grok ship CLIs that speak ACP natively, so the app never installs those: it finds the binary the
//! vendor's own installer put on the machine. Signing in through the app
//! shares credentials with any terminal install either way, because every
//! agent reads its own store (~/.claude, ~/.codex, Cursor's, ~/.grok).

use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum AgentKind {
    Claude,
    Codex,
    Gemini,
    Cursor,
    Grok,
}

pub const ALL: [AgentKind; 5] = [
    AgentKind::Claude,
    AgentKind::Codex,
    AgentKind::Gemini,
    AgentKind::Cursor,
    AgentKind::Grok,
];

impl AgentKind {
    pub fn parse(id: &str) -> Result<Self, String> {
        match id {
            "claude" => Ok(Self::Claude),
            "codex" => Ok(Self::Codex),
            "gemini" => Ok(Self::Gemini),
            "cursor" => Ok(Self::Cursor),
            "grok" => Ok(Self::Grok),
            other => Err(format!("unknown agent: {other}")),
        }
    }

    pub fn id(self) -> &'static str {
        match self {
            Self::Claude => "claude",
            Self::Codex => "codex",
            Self::Gemini => "gemini",
            Self::Cursor => "cursor",
            Self::Grok => "grok",
        }
    }

    /// The name the UI shows. "Claude", not "Claude Code": the audience is
    /// hobbyists, and the Code suffix is developer branding.
    pub fn label(self) -> &'static str {
        match self {
            Self::Claude => "Claude",
            Self::Codex => "Codex",
            Self::Gemini => "Gemini",
            Self::Cursor => "Cursor",
            Self::Grok => "Grok",
        }
    }

    /// Exact adapter pins for the adapter-hosted agents; both projects
    /// release weekly, so no ranges. None for the ACP-native CLIs.
    pub fn adapter(self) -> Option<&'static str> {
        match self {
            Self::Claude => Some("@agentclientprotocol/claude-agent-acp@0.64.2"),
            Self::Codex => Some("@agentclientprotocol/codex-acp@1.1.9"),
            Self::Gemini => Some("@google/gemini-cli@0.55.1"),
            Self::Cursor | Self::Grok => None,
        }
    }

    /// The executable name npm installs for the adapter, for spawning it out
    /// of the provisioned runtime without npx.
    pub fn adapter_bin(self) -> Option<&'static str> {
        match self {
            Self::Claude => Some("claude-agent-acp"),
            Self::Codex => Some("codex-acp"),
            Self::Gemini => Some("gemini"),
            Self::Cursor | Self::Grok => None,
        }
    }

    /// Binary name and the args that start ACP over stdio, for the CLIs that
    /// speak it natively. None for the adapter-hosted agents.
    pub fn native_command(self) -> Option<(&'static str, &'static [&'static str])> {
        match self {
            Self::Cursor => Some(("agent", &["acp"])),
            Self::Grok => Some(("grok", &["agent", "stdio"])),
            Self::Claude | Self::Codex | Self::Gemini => None,
        }
    }

    /// Where a native CLI actually is: the vendor installer's fixed spot
    /// first, then PATH for nonstandard installs. None when it is not on this
    /// machine, which is what "installed: false" means for these agents.
    pub fn native_bin(self) -> Option<PathBuf> {
        let (name, _) = self.native_command()?;
        let install_dir = match self {
            Self::Cursor => ".local/bin",
            Self::Grok => ".grok/bin",
            Self::Claude | Self::Codex | Self::Gemini => return None,
        };
        let home = PathBuf::from(std::env::var("HOME").ok()?);
        let default = home.join(install_dir).join(name);
        if default.is_file() {
            return Some(default);
        }
        std::env::split_paths(&std::env::var_os("PATH")?)
            .map(|dir| dir.join(name))
            .find(|candidate| candidate.is_file())
    }

    /// What a signed-out user needs, in the pane and the chat column.
    pub fn subscription_note(self) -> &'static str {
        match self {
            Self::Claude => "works with a Claude subscription (Pro, from $20/month)",
            Self::Codex => "works with a ChatGPT subscription (Go, from $8/month)",
            Self::Gemini => "works with a Gemini API key from Google AI Studio",
            Self::Cursor => "works with a Cursor subscription (Pro, from $20/month)",
            Self::Grok => "works with an xAI subscription (SuperGrok, from $30/month)",
        }
    }

    /// The vendor's one-line installer, for the "need another agent?" help.
    /// Only the native CLIs have one; the adapter-hosted pair arrive with the
    /// app and are never absent outside a broken dev machine.
    pub fn install_command(self) -> Option<&'static str> {
        match self {
            Self::Cursor => Some("curl https://cursor.com/install -fsSL | bash"),
            Self::Grok => Some("curl -fsSL https://x.ai/cli/install.sh | bash"),
            Self::Claude | Self::Codex | Self::Gemini => None,
        }
    }
}

#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AgentStatus {
    id: &'static str,
    label: &'static str,
    /// Whether the adapter can run at all: npx on PATH in dev, the
    /// provisioned node and adapter install otherwise.
    installed: bool,
    /// None means the check itself failed, not signed out.
    logged_in: Option<bool>,
    /// Extra detail worth showing ("max plan"), when the check provides it.
    detail: Option<String>,
    note: &'static str,
    /// The vendor's installer command, for agents the app finds but the user
    /// installs. The rail hides uninstalled agents; the help modal uses this.
    install: Option<&'static str>,
}

#[tauri::command]
pub async fn agent_statuses(app: tauri::AppHandle) -> Vec<AgentStatus> {
    use tauri::Manager;
    let launcher = app.state::<crate::env::Launcher>().inner().clone();
    let checks = ALL.map(|agent| {
        let launcher = launcher.clone();
        tauri::async_runtime::spawn_blocking(move || {
            let installed = launcher.adapter_available(agent);
            let (logged_in, detail) = if installed {
                match agent {
                    AgentKind::Claude => claude_auth_status(&launcher),
                    AgentKind::Codex => (Some(auth_file(".codex").is_file()), None),
                    AgentKind::Gemini => (Some(gemini_api_key().is_ok()), None),
                    AgentKind::Cursor => cursor_auth_status(agent),
                    AgentKind::Grok => (Some(auth_file(".grok").is_file()), None),
                }
            } else {
                (None, None)
            };
            AgentStatus {
                id: agent.id(),
                label: agent.label(),
                installed,
                logged_in,
                detail,
                note: agent.subscription_note(),
                install: agent.install_command(),
            }
        })
    });
    let mut statuses = Vec::new();
    for (agent, check) in ALL.into_iter().zip(checks) {
        statuses.push(check.await.unwrap_or(AgentStatus {
            id: agent.id(),
            label: agent.label(),
            installed: false,
            logged_in: None,
            detail: None,
            note: agent.subscription_note(),
            install: agent.install_command(),
        }));
    }
    statuses
}

/// The authoritative check, through the adapter's bundled Claude Code:
/// `auth status --json` prints `{"loggedIn": bool, ...}` and exits 0 in both
/// states, so only the JSON is trusted. Cheaper file checks lie: macOS
/// installs may hold credentials in the keychain, the file, or both.
fn claude_auth_status(launcher: &crate::env::Launcher) -> (Option<bool>, Option<String>) {
    let (program, mut args) = launcher.adapter(AgentKind::Claude);
    args.extend(["--cli", "auth", "status", "--json"].map(String::from));
    let mut command = Command::new(program);
    command.args(args);
    if let Some(path) = launcher.adapter_path() {
        command.env("PATH", path);
    }
    let output = command.output();
    let Ok(output) = output else {
        return (None, None);
    };
    let Ok(parsed) = serde_json::from_slice::<serde_json::Value>(&output.stdout) else {
        return (None, None);
    };
    let logged_in = parsed.get("loggedIn").and_then(|v| v.as_bool());
    let detail = parsed
        .get("subscriptionType")
        .and_then(|v| v.as_str())
        .map(|plan| format!("{plan} plan"));
    (logged_in, detail.filter(|_| logged_in == Some(true)))
}

/// Codex and Grok keep no status subcommand worth trusting, but both write
/// `auth.json` on every login and delete it on logout, so existence is the
/// signal. (An expired token still reads as signed in; the chat's -32000
/// handling catches that honestly on first use.) Codex alone honors a HOME
/// override env var.
fn auth_file(dir: &str) -> PathBuf {
    let home = if dir == ".codex" {
        std::env::var("CODEX_HOME").map(PathBuf::from).ok()
    } else {
        None
    };
    home.unwrap_or_else(|| PathBuf::from(std::env::var("HOME").unwrap_or_default()).join(dir))
        .join("auth.json")
}

#[cfg(target_os = "macos")]
const GEMINI_KEYCHAIN_SERVICE: &str = "dev.nurb.desktop.gemini-api-key";
#[cfg(target_os = "macos")]
const GEMINI_KEYCHAIN_ACCOUNT: &str = "gemini";

/// macOS has a system key store; Linux has none every desktop agrees on, so the
/// key lives in a file only its owner can read, beside the app's other config.
#[cfg(target_os = "macos")]
pub(crate) fn gemini_api_key() -> Result<String, String> {
    let output = Command::new("/usr/bin/security")
        .args([
            "find-generic-password",
            "-a",
            GEMINI_KEYCHAIN_ACCOUNT,
            "-s",
            GEMINI_KEYCHAIN_SERVICE,
            "-w",
        ])
        .output()
        .map_err(|error| format!("could not read the Gemini API key: {error}"))?;
    if !output.status.success() {
        return Err("Gemini API key not found".into());
    }
    let key = String::from_utf8(output.stdout)
        .map_err(|_| "the Gemini API key is not valid text".to_string())?
        .trim()
        .to_string();
    if key.is_empty() {
        Err("Gemini API key is empty".into())
    } else {
        Ok(key)
    }
}

#[cfg(target_os = "macos")]
fn save_gemini_api_key(key: &str) -> Result<(), String> {
    let key = security_interactive_argument(key)?;
    let command = format!(
        "add-generic-password -a \"{GEMINI_KEYCHAIN_ACCOUNT}\" -s \"{GEMINI_KEYCHAIN_SERVICE}\" -w {key} -U\n"
    );
    let mut child = Command::new("/usr/bin/security")
        .arg("-i")
        .stdin(Stdio::piped())
        .spawn()
        .map_err(|error| format!("could not save the Gemini API key: {error}"))?;
    let write_result = child
        .stdin
        .take()
        .ok_or_else(|| "could not open macOS Keychain input".to_string())?
        .write_all(command.as_bytes());
    let status = child
        .wait()
        .map_err(|error| format!("could not save the Gemini API key: {error}"))?;
    write_result.map_err(|error| format!("could not save the Gemini API key: {error}"))?;
    status
        .success()
        .then_some(())
        .ok_or_else(|| "macOS Keychain did not save the Gemini API key".into())
}

#[cfg(target_os = "macos")]
fn security_interactive_argument(value: &str) -> Result<String, String> {
    if value.contains(['\r', '\n']) {
        return Err("Gemini API key contains an invalid line break".into());
    }
    Ok(format!(
        "\"{}\"",
        value.replace('\\', "\\\\").replace('"', "\\\"")
    ))
}

/// $XDG_CONFIG_HOME/nurb/gemini-api-key, or ~/.config/nurb/gemini-api-key.
#[cfg(not(target_os = "macos"))]
fn gemini_key_file() -> Result<PathBuf, String> {
    let base = std::env::var_os("XDG_CONFIG_HOME")
        .map(PathBuf::from)
        .filter(|path| path.is_absolute())
        .or_else(|| std::env::var_os("HOME").map(|home| PathBuf::from(home).join(".config")))
        .ok_or_else(|| {
            "could not find a config folder for the Gemini API key. Set HOME, then try again."
                .to_string()
        })?;
    Ok(base.join("nurb").join("gemini-api-key"))
}

#[cfg(not(target_os = "macos"))]
pub(crate) fn gemini_api_key() -> Result<String, String> {
    let key = std::fs::read_to_string(gemini_key_file()?)
        .map_err(|_| "Gemini API key not found".to_string())?
        .trim()
        .to_string();
    if key.is_empty() {
        Err("Gemini API key is empty".into())
    } else {
        Ok(key)
    }
}

#[cfg(not(target_os = "macos"))]
fn save_gemini_api_key(key: &str) -> Result<(), String> {
    use std::os::unix::fs::OpenOptionsExt;

    let key = key.trim();
    if key.contains(['\r', '\n']) {
        return Err("Gemini API key contains an invalid line break".into());
    }
    let path = gemini_key_file()?;
    if let Some(dir) = path.parent() {
        std::fs::create_dir_all(dir)
            .map_err(|error| format!("could not save the Gemini API key: {error}"))?;
    }
    // 0600 on create, and again on write, so a file left behind by an earlier
    // version cannot keep looser permissions.
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .mode(0o600)
        .open(&path)
        .map_err(|error| format!("could not save the Gemini API key: {error}"))?;
    std::fs::set_permissions(
        &path,
        <std::fs::Permissions as std::os::unix::fs::PermissionsExt>::from_mode(0o600),
    )
    .map_err(|error| format!("could not save the Gemini API key: {error}"))?;
    file.write_all(format!("{key}\n").as_bytes())
        .map_err(|error| format!("could not save the Gemini API key: {error}"))
}

/// `agent status` prints "Not logged in" signed out and account details
/// signed in, with no JSON form, so the text is the signal and anything
/// unrecognizable is honestly unknown rather than guessed.
fn cursor_auth_status(kind: AgentKind) -> (Option<bool>, Option<String>) {
    let Some(bin) = kind.native_bin() else {
        return (None, None);
    };
    let Ok(output) = Command::new(bin).arg("status").output() else {
        return (None, None);
    };
    let text = String::from_utf8_lossy(&output.stdout);
    if text.contains("Not logged in") {
        (Some(false), None)
    } else if output.status.success() && !text.trim().is_empty() {
        (Some(true), None)
    } else {
        (None, None)
    }
}

/// Login children still running at app exit, killed by process group like
/// every other child the app spawns.
pub struct Logins(Mutex<Vec<i32>>);

impl Logins {
    pub fn new() -> Self {
        Self(Mutex::new(Vec::new()))
    }

    pub fn shutdown(&self) {
        for pgid in self.0.lock().unwrap().drain(..) {
            unsafe {
                libc::killpg(pgid, libc::SIGTERM);
            }
        }
    }
}

/// Every agent ships a browser OAuth flow as a CLI subcommand that opens the
/// browser itself and exits 0 once the login lands in the shared credential
/// store. Driving those beats holding an ACP `authenticate` request pending
/// for however long a human takes in a browser.
#[tauri::command]
pub async fn agent_login(
    app: tauri::AppHandle,
    agent: String,
    api_key: Option<String>,
) -> Result<(), String> {
    use tauri::Manager;
    let kind = AgentKind::parse(&agent)?;
    if kind == AgentKind::Gemini {
        let key = api_key
            .filter(|key| !key.trim().is_empty())
            .ok_or("Enter a Gemini API key from Google AI Studio.")?;
        crate::acp::authenticate(app, kind, "gemini-api-key", Some(&key)).await?;
        return save_gemini_api_key(&key);
    }
    let launcher = app.state::<crate::env::Launcher>();
    let (program, mut args) = launcher.adapter(kind);
    let adapter_path = launcher.adapter_path();
    // codex-acp's login spawns `codex app-server` off PATH, unlike the rest of
    // the adapter, which falls back to the copy npm installed beside it. On a
    // user's machine nothing but node is on that PATH, so the spawn fails with
    // ENOENT and the login reports only its exit code. Point it at the
    // bundled CLI. (Dev checkouts run the adapter through npx, which puts that
    // same CLI on PATH itself, which is why this only ever broke the shipped
    // app.)
    let codex_cli = match kind {
        AgentKind::Codex => launcher.paths().map(crate::env::Paths::codex_cli),
        _ => None,
    };
    match kind {
        AgentKind::Claude => {
            args.extend(["--cli", "auth", "login", "--claudeai"].map(String::from))
        }
        AgentKind::Codex => args.push("login".into()),
        // Native CLIs: drop the ACP args the launcher put on, login is its
        // own subcommand.
        AgentKind::Cursor | AgentKind::Grok => args = vec!["login".into()],
        AgentKind::Gemini => unreachable!(),
    }
    let (pgid_tx, pgid_rx) = std::sync::mpsc::channel::<i32>();
    let done = tauri::async_runtime::spawn_blocking(move || -> Result<(), String> {
        use std::os::unix::process::CommandExt;
        let mut command = Command::new(program);
        if let Some(path) = adapter_path {
            command.env("PATH", path);
        }
        if let Some(cli) = codex_cli {
            command.env("CODEX_PATH", cli);
        }
        let mut child = command
            .args(&args)
            .stdin(std::process::Stdio::null())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .process_group(0)
            .spawn()
            .map_err(|e| format!("could not start the sign-in: {e}"))?;
        let pgid = child.id() as i32;
        let _ = pgid_tx.send(pgid);
        let handle = app.state::<Logins>();
        handle.0.lock().unwrap().push(pgid);
        let status = child.wait();
        handle.0.lock().unwrap().retain(|p| *p != pgid);
        let status = status.map_err(|e| format!("sign-in failed: {e}"))?;
        if status.success() {
            Ok(())
        } else {
            // No terminal advice: the audience is hobbyists, and the usual
            // cause is a browser tab closed before the login landed.
            Err("The sign-in did not finish. Try again, and complete the sign-in in the browser tab that opens.".into())
        }
    });
    // A human in a browser sets the pace; ten minutes is generous. On timeout
    // the process group is killed, which also unblocks the waiting thread.
    match tokio::time::timeout(Duration::from_secs(600), done).await {
        Ok(joined) => joined.map_err(|e| e.to_string())?,
        Err(_) => {
            if let Ok(pgid) = pgid_rx.try_recv() {
                unsafe {
                    libc::killpg(pgid, libc::SIGTERM);
                }
            }
            Err("The sign-in timed out. Try again.".into())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::AgentKind;

    #[test]
    #[cfg(target_os = "macos")]
    fn keychain_input_quotes_the_key_as_one_interactive_argument() {
        assert_eq!(
            super::security_interactive_argument("dummy \\\"key"),
            Ok("\"dummy \\\\\\\"key\"".into())
        );
        assert!(super::security_interactive_argument("dummy\ncommand").is_err());
    }

    #[test]
    fn agent_ids_roundtrip() {
        for agent in super::ALL {
            assert_eq!(AgentKind::parse(agent.id()), Ok(agent));
        }
        assert!(AgentKind::parse("unknown").is_err());
    }

    /// Every agent starts one way or the other, never both: an npm adapter
    /// the app provisions, or a native CLI the app only finds.
    #[test]
    fn each_agent_is_adapter_hosted_or_native() {
        for agent in super::ALL {
            assert_eq!(agent.adapter().is_some(), agent.native_command().is_none());
            assert_eq!(agent.adapter().is_some(), agent.adapter_bin().is_some());
        }
    }

    #[test]
    fn adapter_runtime_manifest_and_lock_match_the_spawn_pins() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../adapter-runtime/package.json")).unwrap();
        let lock: serde_json::Value =
            serde_json::from_str(include_str!("../../adapter-runtime/package-lock.json")).unwrap();
        let locked = &lock["packages"][""]["dependencies"];

        for agent in super::ALL {
            let Some(adapter) = agent.adapter() else {
                continue;
            };
            let (package, version) = adapter.rsplit_once('@').unwrap();
            assert_eq!(manifest["dependencies"][package], version);
            assert_eq!(locked[package], version);
        }
    }

    /// `agent_login` hands Codex a CODEX_PATH pointing at `.bin/codex`, which
    /// only exists because the adapter depends on a Codex CLI that installs
    /// under that name. An adapter bump that dropped it would put the login
    /// back on the bare PATH lookup that broke it.
    #[test]
    fn the_codex_adapter_installs_the_cli_its_login_is_pointed_at() {
        let lock: serde_json::Value =
            serde_json::from_str(include_str!("../../adapter-runtime/package-lock.json")).unwrap();
        let codex = &lock["packages"]["node_modules/@openai/codex"];
        assert!(codex["bin"]["codex"].is_string(), "no codex bin: {codex}");
    }
}
