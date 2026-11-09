//! Which engine and which adapter runtime the app actually runs: the dev
//! checkout (debug builds, through PATH uv and npx, as phases 1-5 did) or the
//! self-provisioned environment under app data that provision.rs installs.
//! Release builds only know the provisioned form; the checkout path is never
//! compiled into them.

use std::path::PathBuf;
use std::process::Command;

use crate::agents::AgentKind;

/// The Node runtime the provisioner installs. The adapters need >= 22; this
/// is the current LTS, pinned with its published tarball checksums so the
/// runtime download is verified.
pub const NODE_VERSION: &str = "v24.19.0";

#[derive(Clone)]
pub enum Launcher {
    Checkout { repo: PathBuf },
    Provisioned { paths: Paths },
}

impl Launcher {
    pub fn resolve(data: PathBuf) -> Self {
        #[cfg(debug_assertions)]
        if std::env::var_os("NURB_DESKTOP_PROVISIONED").is_none() {
            // The uv project is engine/, not the monorepo root: that is where
            // `uv run --project` finds nurb and where the venv lives.
            return Self::Checkout {
                repo: PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../engine"),
            };
        }
        Self::Provisioned {
            paths: Paths::new(data),
        }
    }

    pub fn paths(&self) -> Option<&Paths> {
        match self {
            Self::Checkout { .. } => None,
            Self::Provisioned { paths } => Some(paths),
        }
    }

    /// A command that runs the serve; callers append `--port` and friends.
    pub fn serve(&self) -> Command {
        match self {
            Self::Checkout { repo } => {
                let mut command = Command::new("uv");
                command
                    .args(["run", "--project"])
                    .arg(repo)
                    .args(["python", "-m", "nurb.serve"]);
                command
            }
            Self::Provisioned { paths } => {
                let mut command = Command::new(paths.venv_python());
                command.args(["-m", "nurb.serve"]);
                command
            }
        }
    }

    /// Program and arguments that run an agent's ACP process. Native CLIs
    /// (Cursor, Grok) are the user's own install and spawn the same way in
    /// both modes. Provisioned adapters are spawned as `node <script>` rather
    /// than through the .bin shebang, which would resolve whatever node `env`
    /// finds on PATH.
    pub fn adapter(&self, kind: AgentKind) -> (String, Vec<String>) {
        if let Some((name, args)) = kind.native_command() {
            let program = kind
                .native_bin()
                .map(|bin| bin.to_string_lossy().into_owned())
                // Not found: spawn the bare name so the failure is an honest
                // "No such file", not a panic.
                .unwrap_or_else(|| name.into());
            return (program, args.iter().map(|a| a.to_string()).collect());
        }
        let pin = kind.adapter().expect("adapter-hosted");
        let acp_args = if kind == AgentKind::Gemini {
            vec!["--acp".into()]
        } else {
            Vec::new()
        };
        match self {
            Self::Checkout { .. } => {
                let mut args = vec!["-y".into(), pin.into()];
                args.extend(acp_args);
                ("npx".into(), args)
            }
            Self::Provisioned { paths } => (
                paths.node_bin().to_string_lossy().into_owned(),
                std::iter::once(paths.adapter_script(kind).to_string_lossy().into_owned())
                    .chain(acp_args)
                    .collect(),
            ),
        }
    }

    /// PATH for adapter processes. On an end-user machine the provisioned
    /// Python environment and node come first, so their shells see those,
    /// then the user's own PATH (see `user_path`) for the native CLIs and the
    /// tools they run. Checkout mode inherits the dev machine's PATH
    /// untouched.
    pub fn adapter_path(&self) -> Option<String> {
        match self {
            Self::Checkout { .. } => None,
            Self::Provisioned { paths } => Some(format!(
                "{}:{}:{}",
                paths.venv().join("bin").display(),
                paths.node_dir().join("bin").display(),
                user_path(),
            )),
        }
    }

    /// The directory the engine writes while it works, granted to the agent
    /// sandbox: the provisioned app-data dir on user machines, the repo
    /// checkout in dev builds (where `uv run --project` and npx put venvs
    /// and caches).
    pub fn engine_root(&self) -> PathBuf {
        match self {
            Self::Checkout { repo } => repo.clone(),
            Self::Provisioned { paths } => paths.data().clone(),
        }
    }

    /// Whether this agent's ACP process can be spawned at all.
    pub fn adapter_available(&self, kind: AgentKind) -> bool {
        if kind.native_command().is_some() {
            return kind.native_bin().is_some();
        }
        match self {
            Self::Checkout { .. } => Command::new("npx")
                .arg("--version")
                .output()
                .map(|out| out.status.success())
                .unwrap_or(false),
            Self::Provisioned { paths } => {
                paths.node_bin().is_file() && paths.adapter_script(kind).is_file()
            }
        }
    }
}

/// Everything the provisioned environment owns lives under one app data dir,
/// including uv's Python installs and cache: ComfyUI Desktop let managed
/// Python land in uv's default location and got unrecoverable half-installs
/// out of it, so nothing here leaves this directory.
#[derive(Clone)]
pub struct Paths {
    data: PathBuf,
}

impl Paths {
    pub(crate) fn new(data: PathBuf) -> Self {
        Self { data }
    }

    pub fn data(&self) -> &PathBuf {
        &self.data
    }

    pub fn python_dir(&self) -> PathBuf {
        self.data.join("python")
    }

    pub fn uv_cache(&self) -> PathBuf {
        self.data.join("uv-cache")
    }

    pub fn venv(&self) -> PathBuf {
        self.data.join("env")
    }

    pub fn venv_python(&self) -> PathBuf {
        self.venv().join("bin/python")
    }

    pub fn node_dir(&self) -> PathBuf {
        self.data.join("node")
    }

    pub fn node_bin(&self) -> PathBuf {
        self.node_dir().join("bin/node")
    }

    /// npm as shipped inside the Node tarball, invoked through its JS entry
    /// so nothing depends on PATH.
    pub fn npm_cli(&self) -> PathBuf {
        self.node_dir().join("lib/node_modules/npm/bin/npm-cli.js")
    }

    pub fn adapters(&self) -> PathBuf {
        self.data.join("adapters")
    }

    pub fn adapter_script(&self, kind: AgentKind) -> PathBuf {
        self.adapters()
            .join("node_modules/.bin")
            .join(kind.adapter_bin().expect("adapter-hosted"))
    }

    /// The Codex CLI npm installs as a dependency of the Codex adapter.
    /// codex-acp's ACP server falls back to this copy on its own, but its
    /// login path spawns a bare `codex` off PATH instead, so the app has to
    /// name it. See `CODEX_PATH` in agents.rs.
    pub fn codex_cli(&self) -> PathBuf {
        self.adapters().join("node_modules/.bin/codex")
    }

    pub fn stamp(&self) -> PathBuf {
        self.data.join("provisioned.json")
    }
}

/// The PATH the user's own terminal has. An app opened from Finder or the Dock
/// inherits launchd's bare `/usr/bin:/bin:/usr/sbin:/sbin`, so an agent CLI
/// installed with Homebrew or npm is invisible to it, and so are the node and
/// git that CLI goes on to run. Asking the login shell once fixes both:
/// detection searches this PATH, and every agent child is handed it. The
/// Homebrew prefixes are appended as a cheap fallback for a shell that fails,
/// hangs, or prints nothing parseable. Resolved on first use, which launch
/// warms from a background thread so the first status check rarely waits.
pub fn user_path() -> &'static str {
    static USER_PATH: std::sync::OnceLock<String> = std::sync::OnceLock::new();
    USER_PATH.get_or_init(|| {
        let shell = std::env::var("SHELL").unwrap_or_else(|_| "/bin/zsh".into());
        merge_path(
            shell_path(&shell, std::time::Duration::from_secs(3)).as_deref(),
            std::env::var("PATH").ok().as_deref(),
        )
    })
}

const PATH_MARK: &str = "__NURB_PATH__";

/// `$PATH` as an interactive login shell sees it, or None when the shell
/// fails or outlasts the timeout. The markers fence the value off from
/// anything the user's rc files print.
fn shell_path(shell: &str, timeout: std::time::Duration) -> Option<String> {
    use std::os::unix::process::CommandExt;
    let child = Command::new(shell)
        .args([
            "-ilc",
            &format!("printf '{PATH_MARK}%s{PATH_MARK}' \"$PATH\""),
        ])
        .stdin(std::process::Stdio::null())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null())
        .process_group(0)
        .spawn()
        .ok()?;
    let pgid = child.id() as i32;
    let (tx, rx) = std::sync::mpsc::channel();
    std::thread::spawn(move || {
        let _ = tx.send(child.wait_with_output());
    });
    let Ok(Ok(output)) = rx.recv_timeout(timeout) else {
        // Also kills whatever the rc files started, which would otherwise
        // hold the pipe open.
        unsafe {
            libc::killpg(pgid, libc::SIGKILL);
        }
        return None;
    };
    let text = String::from_utf8_lossy(&output.stdout);
    let (before, _) = text.rsplit_once(PATH_MARK)?;
    let (_, path) = before.rsplit_once(PATH_MARK)?;
    (!path.is_empty()).then(|| path.to_string())
}

/// The shell's PATH first, then the app's own, then the Homebrew prefixes,
/// with repeats and empty entries dropped.
fn merge_path(shell: Option<&str>, inherited: Option<&str>) -> String {
    let mut dirs: Vec<&str> = Vec::new();
    let fallback = "/opt/homebrew/bin:/usr/local/bin";
    for dir in [shell, inherited, Some(fallback)]
        .into_iter()
        .flatten()
        .flat_map(|path| path.split(':'))
    {
        if !dir.is_empty() && !dirs.contains(&dir) {
            dirs.push(dir);
        }
    }
    dirs.join(":")
}

/// The bundled uv sidecar: Tauri strips the target-triple suffix and places
/// it next to the app executable (Contents/MacOS in a bundle, target/debug
/// during dev; tests run one level down in deps/).
pub fn uv_sidecar() -> Result<PathBuf, String> {
    let exe = std::env::current_exe().map_err(|e| format!("no current exe: {e}"))?;
    let dir = exe.parent().ok_or("current exe has no parent")?;
    let dir = if dir.ends_with("deps") {
        dir.parent().unwrap()
    } else {
        dir
    };
    let uv = dir.join("uv");
    if uv.is_file() {
        Ok(uv)
    } else {
        Err(format!("bundled uv missing at {}", uv.display()))
    }
}

#[cfg(test)]
mod tests {
    use std::time::{Duration, Instant};

    fn fake_shell(name: &str, body: &str) -> std::path::PathBuf {
        use std::os::unix::fs::PermissionsExt;
        let path = std::env::temp_dir().join(format!("nurb-shell-{name}-{}", std::process::id()));
        std::fs::write(&path, format!("#!/bin/sh\n{body}\n")).unwrap();
        std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o755)).unwrap();
        path
    }

    /// A noisy rc file must not leak into the PATH: only what sits between
    /// the markers counts.
    #[test]
    fn the_shell_path_is_read_from_between_the_markers() {
        // The fake ignores its flags and runs the printf the app passes in.
        let shell = fake_shell(
            "noisy",
            "echo 'Welcome back!'\nPATH=/opt/homebrew/bin:/usr/bin eval \"$2\"\necho done",
        );
        assert_eq!(
            super::shell_path(shell.to_str().unwrap(), Duration::from_secs(5)).as_deref(),
            Some("/opt/homebrew/bin:/usr/bin")
        );
        std::fs::remove_file(shell).ok();
    }

    #[test]
    fn a_hung_shell_gives_up_at_the_timeout() {
        let shell = fake_shell("hung", "sleep 30");
        let started = Instant::now();
        assert_eq!(
            super::shell_path(shell.to_str().unwrap(), Duration::from_millis(300)),
            None
        );
        assert!(started.elapsed() < Duration::from_secs(5));
        std::fs::remove_file(shell).ok();
    }

    #[test]
    fn a_missing_shell_falls_back_to_the_homebrew_prefixes() {
        assert_eq!(
            super::shell_path("/nonexistent/shell", Duration::from_secs(1)),
            None
        );
        assert_eq!(
            super::merge_path(None, Some("/usr/bin:/bin")),
            "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin"
        );
    }

    #[test]
    fn the_shell_path_leads_and_repeats_are_dropped() {
        assert_eq!(
            super::merge_path(
                Some("/Users/me/.nvm/bin:/opt/homebrew/bin:/usr/bin"),
                Some("/usr/bin:/bin:")
            ),
            "/Users/me/.nvm/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/local/bin"
        );
    }
}
