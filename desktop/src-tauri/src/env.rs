//! Which nurb and which adapter runtime the app actually runs: the dev
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
            return Self::Checkout {
                repo: PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../.."),
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

    /// A command that runs the nurb CLI; callers append `dev`, `new`, etc.
    pub fn nurb(&self) -> Command {
        match self {
            Self::Checkout { repo } => {
                let mut command = Command::new("uv");
                command.args(["run", "--project"]).arg(repo).arg("nurb");
                command
            }
            Self::Provisioned { paths } => Command::new(paths.venv_bin("nurb")),
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
                (npx().into(), args)
            }
            Self::Provisioned { paths } => (
                paths.node_bin().to_string_lossy().into_owned(),
                std::iter::once(paths.adapter_script(kind).to_string_lossy().into_owned())
                    .chain(acp_args)
                    .collect(),
            ),
        }
    }

    /// PATH for adapter processes. Agents run `nurb build` and friends while
    /// they work, and on an end-user machine the only nurb (and node) anywhere
    /// is the provisioned one, so their shells must see it. Checkout mode
    /// inherits the dev machine's PATH untouched.
    pub fn adapter_path(&self) -> Option<String> {
        match self {
            Self::Checkout { .. } => None,
            Self::Provisioned { paths } => {
                let mut entries = vec![paths.venv_bin_dir(), paths.node_bin_dir()];
                match std::env::var("PATH") {
                    Ok(inherited) => entries.extend(std::env::split_paths(&inherited)),
                    // A missing PATH is unheard of in practice; the platform's
                    // own tool directories keep child shells functional.
                    #[cfg(windows)]
                    Err(_) => {
                        let root =
                            std::env::var("SystemRoot").unwrap_or_else(|_| r"C:\Windows".into());
                        entries.push(std::path::Path::new(&root).join("System32"));
                    }
                    #[cfg(not(windows))]
                    Err(_) => {
                        entries.push("/usr/bin".into());
                        entries.push("/bin".into());
                    }
                }
                std::env::join_paths(entries)
                    .ok()
                    .map(|joined| joined.to_string_lossy().into_owned())
            }
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
            Self::Checkout { .. } => Command::new(npx())
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

    /// Where the venv keeps executables: `bin/` on unix, `Scripts\` with an
    /// `.exe` suffix on Windows.
    pub fn venv_bin_dir(&self) -> PathBuf {
        self.venv().join(if cfg!(windows) { "Scripts" } else { "bin" })
    }

    pub fn venv_bin(&self, name: &str) -> PathBuf {
        self.venv_bin_dir()
            .join(format!("{name}{}", std::env::consts::EXE_SUFFIX))
    }

    pub fn venv_python(&self) -> PathBuf {
        self.venv_bin("python")
    }

    pub fn node_dir(&self) -> PathBuf {
        self.data.join("node")
    }

    /// The Windows Node zip keeps node.exe (and npm's tree) at the archive
    /// root; the unix tarballs use bin/ and lib/.
    pub fn node_bin_dir(&self) -> PathBuf {
        if cfg!(windows) {
            self.node_dir()
        } else {
            self.node_dir().join("bin")
        }
    }

    pub fn node_bin(&self) -> PathBuf {
        self.node_bin_dir()
            .join(format!("node{}", std::env::consts::EXE_SUFFIX))
    }

    /// npm as shipped inside the Node archive, invoked through its JS entry
    /// so nothing depends on PATH.
    pub fn npm_cli(&self) -> PathBuf {
        if cfg!(windows) {
            self.node_dir().join("node_modules/npm/bin/npm-cli.js")
        } else {
            self.node_dir().join("lib/node_modules/npm/bin/npm-cli.js")
        }
    }

    pub fn adapters(&self) -> PathBuf {
        self.data.join("adapters")
    }

    /// The adapter's real JS entry, spawned as `node <script>`. Named by the
    /// package rather than through node_modules/.bin: the .bin entries are
    /// symlinks to these same files on unix but cmd shims on Windows, and
    /// node cannot run a shim.
    pub fn adapter_script(&self, kind: AgentKind) -> PathBuf {
        let entry = match kind {
            AgentKind::Claude => "@agentclientprotocol/claude-agent-acp/dist/index.js",
            AgentKind::Codex => "@agentclientprotocol/codex-acp/dist/index.js",
            AgentKind::Gemini => "@google/gemini-cli/bundle/gemini.js",
            AgentKind::Cursor | AgentKind::Grok => unreachable!("adapter-hosted"),
        };
        self.adapters().join("node_modules").join(entry)
    }

    /// The Codex CLI npm installs as a dependency of the Codex adapter.
    /// codex-acp's ACP server falls back to this copy on its own, but its
    /// login path spawns a bare `codex` off PATH instead, so the app has to
    /// name it. See `CODEX_PATH` in agents.rs. On Windows the .bin entry is a
    /// cmd shim nothing can spawn portably, but the platform package ships
    /// the real native binary, so name that instead.
    pub fn codex_cli(&self) -> PathBuf {
        if cfg!(windows) {
            let arch = if std::env::consts::ARCH == "aarch64" {
                "aarch64-pc-windows-msvc"
            } else {
                "x86_64-pc-windows-msvc"
            };
            self.adapters().join(format!(
                "node_modules/@openai/codex-win32-{}/vendor/{arch}/bin/codex.exe",
                if std::env::consts::ARCH == "aarch64" { "arm64" } else { "x64" },
            ))
        } else {
            self.adapters().join("node_modules/.bin/codex")
        }
    }

    pub fn stamp(&self) -> PathBuf {
        self.data.join("provisioned.json")
    }
}

/// The bundled uv sidecar: Tauri strips the target-triple suffix (keeping
/// .exe on Windows) and places it next to the app executable (Contents/MacOS
/// in a bundle, target/debug during dev; tests run one level down in deps/).
pub fn uv_sidecar() -> Result<PathBuf, String> {
    let exe = std::env::current_exe().map_err(|e| format!("no current exe: {e}"))?;
    let dir = exe.parent().ok_or("current exe has no parent")?;
    let dir = if dir.ends_with("deps") {
        dir.parent().unwrap()
    } else {
        dir
    };
    let uv = dir.join(format!("uv{}", std::env::consts::EXE_SUFFIX));
    if uv.is_file() {
        Ok(uv)
    } else {
        Err(format!("bundled uv missing at {}", uv.display()))
    }
}

/// npm's launcher is a cmd shim on Windows, which std::process can spawn only
/// under its full name. Dev-checkout only; user machines never see npx.
fn npx() -> &'static str {
    if cfg!(windows) {
        "npx.cmd"
    } else {
        "npx"
    }
}

/// The user's home. HOME is the unix contract; USERPROFILE is the Windows
/// one, and respecting HOME first keeps test overrides working everywhere.
pub fn home_dir() -> Option<PathBuf> {
    std::env::var_os("HOME")
        .or_else(|| std::env::var_os("USERPROFILE"))
        .map(PathBuf::from)
}
