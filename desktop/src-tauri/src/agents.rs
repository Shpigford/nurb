//! The agents the app can host, and everything that differs between them:
//! how their ACP process starts, display name, sign-in state, and the login
//! flow.
//!
//! Claude and Codex run through npm adapters the app provisions; each bundles
//! its agent's real CLI (claude-agent-acp carries the native Claude Code
//! binary, codex-acp carries @openai/codex), so nothing has to be on the
//! user's PATH except node/npx. Cursor and Grok ship CLIs that speak ACP
//! natively, so the app never installs those: it finds the binary the
//! vendor's own installer put on the machine. Signing in through the app
//! shares credentials with any terminal install either way, because every
//! agent reads its own store (~/.claude, ~/.codex, Cursor's, ~/.grok).

use std::path::PathBuf;
use std::process::Command;
use std::sync::Mutex;
use std::time::Duration;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum AgentKind {
    Claude,
    Codex,
    Cursor,
    Grok,
}

pub const ALL: [AgentKind; 4] = [
    AgentKind::Claude,
    AgentKind::Codex,
    AgentKind::Cursor,
    AgentKind::Grok,
];

impl AgentKind {
    pub fn parse(id: &str) -> Result<Self, String> {
        match id {
            "claude" => Ok(Self::Claude),
            "codex" => Ok(Self::Codex),
            "cursor" => Ok(Self::Cursor),
            "grok" => Ok(Self::Grok),
            other => Err(format!("unknown agent: {other}")),
        }
    }

    pub fn id(self) -> &'static str {
        match self {
            Self::Claude => "claude",
            Self::Codex => "codex",
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
            Self::Cursor | Self::Grok => None,
        }
    }

    /// The executable name npm installs for the adapter, for spawning it out
    /// of the provisioned runtime without npx.
    pub fn adapter_bin(self) -> Option<&'static str> {
        match self {
            Self::Claude => Some("claude-agent-acp"),
            Self::Codex => Some("codex-acp"),
            Self::Cursor | Self::Grok => None,
        }
    }

    /// Binary name and the args that start ACP over stdio, for the CLIs that
    /// speak it natively. None for the adapter-hosted agents.
    pub fn native_command(self) -> Option<(&'static str, &'static [&'static str])> {
        match self {
            Self::Cursor => Some(("agent", &["acp"])),
            Self::Grok => Some(("grok", &["agent", "stdio"])),
            Self::Claude | Self::Codex => None,
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
            Self::Claude | Self::Codex => return None,
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
            Self::Claude | Self::Codex => None,
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
pub async fn agent_login(app: tauri::AppHandle, agent: String) -> Result<(), String> {
    use tauri::Manager;
    let kind = AgentKind::parse(&agent)?;
    let launcher = app.state::<crate::env::Launcher>();
    let (program, mut args) = launcher.adapter(kind);
    let adapter_path = launcher.adapter_path();
    match kind {
        AgentKind::Claude => {
            args.extend(["--cli", "auth", "login", "--claudeai"].map(String::from))
        }
        AgentKind::Codex => args.push("login".into()),
        // Native CLIs: drop the ACP args the launcher put on, login is its
        // own subcommand.
        AgentKind::Cursor | AgentKind::Grok => args = vec!["login".into()],
    }
    let (pgid_tx, pgid_rx) = std::sync::mpsc::channel::<i32>();
    let done = tauri::async_runtime::spawn_blocking(move || -> Result<(), String> {
        use std::os::unix::process::CommandExt;
        let mut command = Command::new(program);
        if let Some(path) = adapter_path {
            command.env("PATH", path);
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
            Err("The sign-in did not finish. Try again, or sign in from a terminal.".into())
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
    fn agent_ids_roundtrip() {
        for agent in super::ALL {
            assert_eq!(AgentKind::parse(agent.id()), Ok(agent));
        }
        assert!(AgentKind::parse("gemini").is_err());
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
}
