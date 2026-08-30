//! Which nurb and which adapter runtime the app actually runs: the dev
//! checkout (debug builds, through PATH uv and npx, as phases 1-5 did) or the
//! self-provisioned environment under app data that provision.rs installs.
//! Release builds only know the provisioned form; the checkout path is never
//! compiled into them.
//!
//! Every path that differs between platforms lives here: a Python venv is
//! `bin/` on Unix and `Scripts/` on Windows, node is `bin/node` vs `node.exe`,
//! npm's `.bin` shims are symlinks on Unix and cmd scripts on Windows, and the
//! PATH list separator is `:` vs `;`.

use std::path::PathBuf;
use std::process::Command;

use crate::agents::AgentKind;

/// The Node runtime the provisioner installs. The adapters need >= 22; this
/// is the current LTS, pinned with its published tarball checksums so the
/// runtime download is verified.
pub const NODE_VERSION: &str = "v24.19.0";

/// The executable a program name resolves to on this platform.
fn exe(name: &str) -> String {
    if cfg!(windows) && !name.to_ascii_lowercase().ends_with(".exe") {
        format!("{name}.exe")
    } else {
        name.into()
    }
}

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
            Self::Provisioned { paths } => Command::new(paths.venv_bin().join(exe("nurb"))),
        }
    }

    /// Program and arguments that run an agent's ACP process. Native CLIs
    /// (Cursor, Grok) are the user's own install and spawn the same way in
    /// both modes. Provisioned adapters are spawned as `node <script>` rather
    /// than through the .bin shebang, which would resolve whatever node `env`
    /// finds on PATH. On Windows the .bin entry is a shell script, not a
    /// symlink to the JS file, so it is resolved through the package's own
    /// `bin` field instead.
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

    /// PATH for adapter processes. Agents run `nurb build` and friends while
    /// they work, and on an end-user machine the only nurb (and node) anywhere
    /// is the provisioned one, so their shells must see it. Checkout mode
    /// inherits the dev machine's PATH untouched.
    pub fn adapter_path(&self) -> Option<String> {
        match self {
            Self::Checkout { .. } => None,
            Self::Provisioned { paths } => {
                let inherited = std::env::var_os("PATH").unwrap_or_default();
                // Split the inherited PATH first. Treating the entire PATH as one
                // entry makes Windows resolve it as a single literal directory and
                // breaks every external command after the provisioned entries.
                // join_paths then reconstructs it with the native separator and
                // quoting rules.
                let mut entries = vec![paths.venv_bin(), paths.node_bin_dir()];
                entries.extend(std::env::split_paths(&inherited));
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

    /// The venv's executable directory: `bin` on Unix, `Scripts` on Windows.
    pub fn venv_bin(&self) -> PathBuf {
        if cfg!(windows) {
            self.venv().join("Scripts")
        } else {
            self.venv().join("bin")
        }
    }

    pub fn venv_python(&self) -> PathBuf {
        self.venv_bin().join(if cfg!(windows) { "python.exe" } else { "python" })
    }

    pub fn node_dir(&self) -> PathBuf {
        self.data.join("node")
    }

    /// The node executable: `bin/node` in the Unix tarball layout, `node.exe`
    /// at the root of the Windows zip layout.
    pub fn node_bin(&self) -> PathBuf {
        if cfg!(windows) {
            self.node_dir().join("node.exe")
        } else {
            self.node_dir().join("bin").join("node")
        }
    }

    /// The directory containing the node executable, for PATH entries.
    pub fn node_bin_dir(&self) -> PathBuf {
        if cfg!(windows) {
            self.node_dir()
        } else {
            self.node_dir().join("bin")
        }
    }

    /// npm as shipped inside the Node archive, invoked through its JS entry
    /// so nothing depends on PATH. The Windows zip keeps it under
    /// node_modules/, the Unix tarball under lib/.
    pub fn npm_cli(&self) -> PathBuf {
        let base = if cfg!(windows) {
            self.node_dir().join("node_modules")
        } else {
            self.node_dir().join("lib").join("node_modules")
        };
        base.join("npm").join("bin").join("npm-cli.js")
    }

    pub fn adapters(&self) -> PathBuf {
        self.data.join("adapters")
    }

    /// The script an adapter's ACP server runs as, spawned through node. On
    /// Unix that is npm's `.bin/<name>` symlink; on Windows the `.bin` entry
    /// is a POSIX sh script that node cannot execute, so the real JS file is
    /// read out of the package's own `bin` field instead.
    pub fn adapter_script(&self, kind: AgentKind) -> PathBuf {
        let name = kind.adapter_bin().expect("adapter-hosted");
        #[cfg(windows)]
        {
            self.adapter_js(kind).unwrap_or_else(|| {
                self.adapters().join("node_modules/.bin").join(name)
            })
        }
        #[cfg(not(windows))]
        {
            self.adapters().join("node_modules/.bin").join(name)
        }
    }

    /// The adapter package's `bin.<name>` JS entry, from its installed
    /// package.json: `node_modules/@scope/pkg/dist/index.js` for both shipped
    /// adapters. None when the package is not installed or has no such entry.
    #[cfg(windows)]
    fn adapter_js(&self, kind: AgentKind) -> Option<PathBuf> {
        let pin = kind.adapter()?;
        let package = pin.rsplit_once('@')?.0;
        let name = kind.adapter_bin()?;
        let dir = self.adapters().join("node_modules").join(package);
        let manifest: serde_json::Value =
            serde_json::from_str(&std::fs::read_to_string(dir.join("package.json")).ok()?).ok()?;
        let bin = &manifest["bin"];
        let entry = match bin {
            serde_json::Value::String(path) => path.as_str().to_string(),
            serde_json::Value::Object(map) => map.get(name)?.as_str()?.to_string(),
            _ => return None,
        };
        Some(dir.join(entry))
    }

    /// The Codex CLI npm installs as a dependency of the Codex adapter.
    /// codex-acp's ACP server falls back to this copy on its own, but its
    /// login path spawns a bare `codex` off PATH instead, so the app has to
    /// name it. See `CODEX_PATH` in agents.rs.
    pub fn codex_cli(&self) -> PathBuf {
        #[cfg(windows)]
        {
            // The adapter's native binary: the platform package vendors
            // codex.exe under vendor/<triple>/bin, and spawning a .cmd or the
            // JS entry through cmd would lean on PATH. Fall back to the .cmd
            // shim if the package layout changes.
            let arch = match std::env::consts::ARCH {
                "aarch64" => "codex-win32-arm64",
                _ => "codex-win32-x64",
            };
            let triple = match std::env::consts::ARCH {
                "aarch64" => "aarch64-pc-windows-msvc",
                _ => "x86_64-pc-windows-msvc",
            };
            let native = self
                .adapters()
                .join("node_modules/@openai")
                .join(arch)
                .join("vendor")
                .join(triple)
                .join("bin")
                .join("codex.exe");
            if native.is_file() {
                return native;
            }
            self.adapters().join("node_modules/.bin/codex.cmd")
        }
        #[cfg(not(windows))]
        {
            self.adapters().join("node_modules/.bin/codex")
        }
    }

    pub fn stamp(&self) -> PathBuf {
        self.data.join("provisioned.json")
    }
}

/// The bundled uv sidecar: Tauri strips the target-triple suffix and places
/// it next to the app executable (Contents/MacOS in a bundle, target/debug
/// during dev; tests run one level down in deps/). On Windows the sidecar is
/// uv.exe.
pub fn uv_sidecar() -> Result<PathBuf, String> {
    let exe = std::env::current_exe().map_err(|e| format!("no current exe: {e}"))?;
    let dir = exe.parent().ok_or("current exe has no parent")?;
    let dir = if dir.ends_with("deps") {
        dir.parent().unwrap()
    } else {
        dir
    };
    let uv = dir.join(if cfg!(windows) { "uv.exe" } else { "uv" });
    if uv.is_file() {
        Ok(uv)
    } else {
        Err(format!("bundled uv missing at {}", uv.display()))
    }
}

#[cfg(test)]
mod tests {
    use super::{exe, Paths};

    #[test]
    fn venv_layout_matches_the_platform() {
        let paths = Paths::new("/tmp/appdata".into());
        let venv_python = paths.venv_python();
        if cfg!(windows) {
            assert!(venv_python.ends_with("Scripts\\python.exe"));
        } else {
            assert!(venv_python.ends_with("bin/python"));
        }
    }

    #[test]
    fn npm_cli_layout_matches_the_platform() {
        let paths = Paths::new("/tmp/appdata".into());
        let npm = paths.npm_cli();
        assert!(npm.ends_with("npm-cli.js"));
        if cfg!(windows) {
            assert!(npm.to_string_lossy().contains("node_modules\\npm"));
        } else {
            assert!(npm.to_string_lossy().contains("lib/node_modules/npm"));
        }
    }

    #[test]
    fn executables_gain_the_windows_suffix() {
        if cfg!(windows) {
            assert_eq!(exe("uv"), "uv.exe");
            assert_eq!(exe("uv.exe"), "uv.exe");
            assert_eq!(exe("nurb"), "nurb.exe");
        } else {
            assert_eq!(exe("uv"), "uv");
        }
    }
}
