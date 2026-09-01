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

#[cfg(not(windows))]
use std::io::Write;
use std::path::PathBuf;
use std::process::Command;
#[cfg(not(windows))]
use std::process::Stdio;
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
    /// Windows installs carry an extension, so each name is tried with the
    /// executable suffixes the platform launches.
    pub fn native_bin(self) -> Option<PathBuf> {
        let (name, _) = self.native_command()?;
        let install_dir = match self {
            Self::Cursor => ".local/bin",
            Self::Grok => ".grok/bin",
            Self::Claude | Self::Codex | Self::Gemini => return None,
        };
        let names: Vec<String> = if cfg!(windows) {
            vec![format!("{name}.exe"), format!("{name}.cmd")]
        } else {
            vec![name.to_string()]
        };
        let home = crate::env::home_dir()?;
        for file in &names {
            let default = home.join(install_dir).join(file);
            if default.is_file() {
                return Some(default);
            }
        }
        std::env::split_paths(&std::env::var_os("PATH")?)
            .flat_map(|dir| names.iter().map(move |file| dir.join(file)))
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
    home.unwrap_or_else(|| crate::env::home_dir().unwrap_or_default().join(dir))
        .join("auth.json")
}

const GEMINI_KEYCHAIN_SERVICE: &str = "dev.nurb.desktop.gemini-api-key";
const GEMINI_KEYCHAIN_ACCOUNT: &str = "gemini";

/// Windows keeps the key in Credential Manager under the same service name
/// the macOS Keychain uses.
#[cfg(windows)]
fn gemini_entry() -> Result<keyring::Entry, String> {
    keyring::Entry::new(GEMINI_KEYCHAIN_SERVICE, GEMINI_KEYCHAIN_ACCOUNT)
        .map_err(|error| format!("could not open the credential store: {error}"))
}

#[cfg(windows)]
pub(crate) fn gemini_api_key() -> Result<String, String> {
    match gemini_entry()?.get_password() {
        Ok(key) if !key.trim().is_empty() => Ok(key.trim().to_string()),
        Ok(_) => Err("Gemini API key is empty".into()),
        Err(keyring::Error::NoEntry) => Err("Gemini API key not found".into()),
        Err(error) => Err(format!("could not read the Gemini API key: {error}")),
    }
}

#[cfg(windows)]
fn save_gemini_api_key(key: &str) -> Result<(), String> {
    if key.contains(['\r', '\n']) {
        return Err("Gemini API key contains an invalid line break".into());
    }
    gemini_entry()?
        .set_password(key)
        .map_err(|error| format!("could not save the Gemini API key: {error}"))
}

#[cfg(not(windows))]
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

#[cfg(not(windows))]
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

#[cfg(not(windows))]
fn security_interactive_argument(value: &str) -> Result<String, String> {
    if value.contains(['\r', '\n']) {
        return Err("Gemini API key contains an invalid line break".into());
    }
    Ok(format!(
        "\"{}\"",
        value.replace('\\', "\\\\").replace('"', "\\\"")
    ))
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

/// Login children still running at app exit, killed as trees like every
/// other child the app spawns.
pub struct Logins(Mutex<Vec<crate::proc::ProcessTree>>);

impl Logins {
    pub fn new() -> Self {
        Self(Mutex::new(Vec::new()))
    }

    pub fn shutdown(&self) {
        for tree in self.0.lock().unwrap().drain(..) {
            tree.terminate();
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
    let (tree_tx, tree_rx) = std::sync::mpsc::channel::<crate::proc::ProcessTree>();
    let done = tauri::async_runtime::spawn_blocking(move || -> Result<(), String> {
        let mut command = Command::new(program);
        if let Some(path) = adapter_path {
            command.env("PATH", path);
        }
        if let Some(cli) = codex_cli {
            command.env("CODEX_PATH", cli);
        }
        command
            .args(&args)
            .stdin(std::process::Stdio::null())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped());
        crate::proc::configure(&mut command);
        let mut child = command
            .spawn()
            .map_err(|e| format!("could not start the sign-in: {e}"))?;
        let pid = child.id();
        let tree = crate::proc::ProcessTree::attach(&child);
        let _ = tree_tx.send(tree.clone());
        let handle = app.state::<Logins>();
        handle.0.lock().unwrap().push(tree);
        let status = child.wait();
        handle.0.lock().unwrap().retain(|t| !t.same_child(pid));
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
            if let Ok(tree) = tree_rx.try_recv() {
                tree.terminate();
            }
            Err("The sign-in timed out. Try again.".into())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::AgentKind;

    #[cfg(not(windows))]
    #[test]
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
        }
    }

    /// The adapter entry scripts env.rs names must be the same files npm's
    /// lock says each package's bin points at, or a version bump that moves
    /// an entry would break every chat spawn silently.
    #[test]
    fn adapter_scripts_match_the_lock_bin_entries() {
        let lock: serde_json::Value =
            serde_json::from_str(include_str!("../../adapter-runtime/package-lock.json")).unwrap();
        let paths = crate::env::Paths::new(std::path::PathBuf::from("scratch"));
        for agent in super::ALL {
            let Some(adapter) = agent.adapter() else {
                continue;
            };
            let (package, _) = adapter.rsplit_once('@').unwrap();
            let bins = lock["packages"][format!("node_modules/{package}")]["bin"]
                .as_object()
                .unwrap_or_else(|| panic!("no bin entries for {package}"));
            let script = paths.adapter_script(agent);
            let script = script.to_string_lossy().replace('\\', "/");
            assert!(
                bins.values()
                    .filter_map(|entry| entry.as_str())
                    .any(|entry| script.ends_with(&format!("{package}/{entry}"))),
                "adapter_script for {package} does not match its lock bin: {script}"
            );
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
        // Windows points CODEX_PATH at the native exe inside the platform
        // package (env.rs codex_cli), so the lock must still carry it.
        for platform in ["win32-x64", "win32-arm64"] {
            let native = &lock["packages"][format!("node_modules/@openai/codex-{platform}")];
            assert!(native.is_object(), "no @openai/codex-{platform} in the lock");
        }
    }
}
