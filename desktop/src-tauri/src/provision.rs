//! First-launch provisioning: the bundled uv sidecar installs a managed
//! Python, syncs the bundled hash-pinned lock, and installs the bundled nurb
//! wheel into a venv under app data; a downloaded Node LTS plus `npm ci`
//! from the bundled adapter lock gives chat a runtime. Everything
//! streams phase events to the setup screen, and every component is checked
//! and redone independently so an app update or a half-finished install
//! repairs itself instead of wedging.

use std::collections::VecDeque;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use sha2::{Digest, Sha256};
use tauri::ipc::Channel;
use tauri::Manager;

use crate::agents;
use crate::env::{uv_sidecar, Launcher, Paths, NODE_VERSION};
use crate::process;

const PYTHON_VERSION: &str = "3.13";
const HEALTH_TIMEOUT: Duration = Duration::from_secs(2);
// Generous because the first exec of a freshly written binary can stall for
// many seconds while macOS assesses it (Gatekeeper/XProtect), and these CLIs
// are large.
const NATIVE_CLI_HEALTH_TIMEOUT: Duration = Duration::from_secs(30);
const NPM_CI_ARGS: &[&str] = &["ci", "--include=optional", "--no-fund", "--no-audit"];
static PROBE_ID: AtomicU64 = AtomicU64::new(0);

/// The pinned Node archive for this platform: published SHASUMS256 entries.
fn node_archive() -> (&'static str, &'static str) {
    let arch = std::env::consts::ARCH;
    if cfg!(windows) {
        match arch {
            "aarch64" => (
                "node-v24.19.0-win-arm64.zip",
                "8502f4a50b458d4cc38ed8f2001556c2cd239d464920f74017926ccb1e1c157f",
            ),
            _ => (
                "node-v24.19.0-win-x64.zip",
                "57f71ab3652e797d84acddc79c81cc9ff1c6ddb2a1974cdb83f00fee9bff4c73",
            ),
        }
    } else if cfg!(target_os = "macos") {
        match arch {
            "aarch64" => (
                "node-v24.19.0-darwin-arm64.tar.xz",
                "3f1cf157479c1480352083105e13faf9d008ede98e7e157746b6df940d197b94",
            ),
            _ => (
                "node-v24.19.0-darwin-x64.tar.xz",
                "d35e95230f46f6f0751df497c56622c6735e05d5e1fb1630996a005b9d328fe4",
            ),
        }
    } else {
        unreachable!("the desktop app provisions node on macOS and Windows only")
    }
}

#[derive(Clone, serde::Serialize)]
#[serde(rename_all = "camelCase", tag = "kind")]
pub enum ProvisionEvent {
    /// A phase began; the frontend owns the copy per stage id.
    Stage { stage: &'static str },
    /// One line of tool output, for the setup screen's ticker.
    Detail { line: String },
}

/// What a finished install looked like. Compared per component: changed wheel
/// or lock contents redo the Python side, a new Node or adapter lock redoes
/// the chat side, and neither touches the other.
#[derive(serde::Serialize, serde::Deserialize, Default, Clone)]
struct Stamp {
    lock: String,
    wheel: String,
    node: String,
    adapters: Vec<String>,
    adapter_lock: String,
}

pub struct Provisioner {
    /// Single flight: React StrictMode double-invokes the setup effect, and
    /// the second call must wait out the first, then see a healthy install.
    run: Mutex<()>,
    pid: Mutex<Option<u32>>,
    shutting_down: AtomicBool,
}

impl Provisioner {
    pub fn new() -> Self {
        Self {
            run: Mutex::new(()),
            pid: Mutex::new(None),
            shutting_down: AtomicBool::new(false),
        }
    }

    pub fn shutdown(&self) {
        self.shutting_down.store(true, Ordering::SeqCst);
        if let Some(pid) = *self.pid.lock().unwrap() {
            process::kill_tree(pid);
        }
    }
}

struct Resources {
    wheel: PathBuf,
    wheel_hash: String,
    lock: PathBuf,
    lock_hash: String,
    adapter_package: PathBuf,
    adapter_lock: PathBuf,
    adapter_lock_hash: String,
}

fn file_hash(path: &std::path::Path, what: &str) -> Result<String, String> {
    let bytes = std::fs::read(path)
        .map_err(|e| format!("bundled {what} missing at {}: {e}", path.display()))?;
    Ok(format!("{:x}", Sha256::digest(&bytes)))
}

fn resources(app: &tauri::AppHandle) -> Result<Resources, String> {
    let dir = app
        .path()
        .resource_dir()
        .map_err(|e| format!("no resource dir: {e}"))?
        .join("resources");
    let lock = dir.join("requirements.lock");
    let lock_hash = file_hash(&lock, "lock")?;
    let adapter_package = dir.join("adapter-package.json");
    let adapter_lock = dir.join("adapter-package-lock.json");
    let adapter_lock_hash = file_hash(&adapter_lock, "adapter lock")?;
    let wheel = newest_wheel(&dir)?;
    let wheel_hash = file_hash(&wheel, "wheel")?;
    Ok(Resources {
        wheel,
        wheel_hash,
        lock,
        lock_hash,
        adapter_package,
        adapter_lock,
        adapter_lock_hash,
    })
}

fn read_stamp(paths: &Paths) -> Stamp {
    std::fs::read(paths.stamp())
        .ok()
        .and_then(|bytes| serde_json::from_slice(&bytes).ok())
        .unwrap_or_default()
}

fn write_stamp(paths: &Paths, stamp: &Stamp) -> Result<(), String> {
    let json = serde_json::to_vec_pretty(stamp).map_err(|e| e.to_string())?;
    std::fs::write(paths.stamp(), json).map_err(|e| format!("could not record install: {e}"))
}

/// A venv that matches the bundled wheel and lock, and whose interpreter
/// actually imports nurb: a stamp alone lies after a half-finished install.
fn parts_ok(paths: &Paths, res: &Resources, stamp: &Stamp) -> bool {
    stamp.lock == res.lock_hash
        && stamp.wheel == res.wheel_hash
        && Command::new(paths.venv_python())
            .args(["-c", "import nurb"])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .map(|status| status.success())
            .unwrap_or(false)
}

fn chat_ok(paths: &Paths, res: &Resources, stamp: &Stamp) -> bool {
    if stamp.node != NODE_VERSION
        || stamp.adapters != adapter_pins()
        || stamp.adapter_lock != res.adapter_lock_hash
    {
        return false;
    }

    chat_runtime_ok(paths)
}

fn chat_runtime_ok(paths: &Paths) -> bool {
    if chat_runtime_check(paths).is_ok() {
        return true;
    }
    // Retry once: the first provisioning of adapter images hits a
    // transient race where npm's postinstall hasn't finished writing
    // the adapter binaries yet.
    std::thread::sleep(Duration::from_secs(2));
    chat_runtime_check(paths).is_ok()
}

/// Says which component failed and why, so a broken install surfaces as an
/// actionable message on the setup screen instead of a dead end (issue #157).
fn chat_runtime_check(paths: &Paths) -> Result<(), String> {
    let mut node = Command::new(paths.node_bin());
    node.arg("--version");
    probe_version(node, paths.data(), NODE_VERSION, HEALTH_TIMEOUT)
        .map_err(|why| format!("the chat runtime check failed: {why}"))?;

    // Only the adapter-hosted agents; Cursor and Grok are not provisioned.
    for kind in &agents::ALL {
        let Some(adapter_pin) = kind.adapter() else {
            continue;
        };
        let script = paths.adapter_script(*kind);
        if !script.is_file() {
            return Err(format!("the {} adapter is missing", kind.label()));
        }
        let mut adapter = Command::new(paths.node_bin());
        adapter.arg(script).arg("--version");
        let version = adapter_pin.rsplit_once('@').unwrap().1;
        probe_version(adapter, paths.data(), version, HEALTH_TIMEOUT)
            .map_err(|why| format!("the {} adapter check failed: {why}", kind.label()))?;
    }

    // Adapter --version never loads the native CLIs supplied as optional npm
    // packages. Exercise the two platform-specific binaries so a skipped package
    // cannot be stamped healthy and surface later as a misleading auth error.
    let mut claude = Command::new(paths.node_bin());
    claude
        .arg(paths.adapter_script(crate::agents::AgentKind::Claude))
        .args(["--cli", "--version"]);
    probe_output(claude, paths.data(), NATIVE_CLI_HEALTH_TIMEOUT)
        .map_err(|why| format!("the Claude CLI check failed: {why}"))?;

// On Windows the bundled CLI is a native .exe; on Unix it is the JS entry
    // npm symlinks into .bin, which runs through the provisioned node.
    #[cfg(windows)]
    {
        let mut codex = Command::new(paths.codex_cli());
        codex.arg("--version");
        if probe_success(codex, paths.data(), NATIVE_CLI_HEALTH_TIMEOUT) {
            Ok(())
        } else {
            Err("the Codex CLI check failed".into())
        }
    }
    #[cfg(not(windows))]
    {
        let mut codex = Command::new(paths.node_bin());
        codex.arg(paths.codex_cli()).arg("--version");
        if probe_success(codex, paths.data(), NATIVE_CLI_HEALTH_TIMEOUT) {
            Ok(())
        } else {
            Err("the Codex CLI check failed".into())
        }
    }
}

/// The health check with one retry. A freshly extracted binary can fail its
/// very first spawn on Windows: the real-time scanner is still holding the
/// image, so the process dies once and runs cleanly forever after. Without the
/// retry that single hiccup reads as "the install is missing a CLI" and sends
/// the user back through a few hundred megabytes of re-download.


/// Run a tiny version command without trusting that a corrupt executable will
/// return. Output goes to a file, not a pipe that a noisy or forked process can
/// hold open forever; the last token is the version emitted by both adapters.
fn probe_version(
    command: Command,
    output_dir: &std::path::Path,
    expected: &str,
    timeout: Duration,
) -> Result<(), String> {
    let text = probe_output(command, output_dir, timeout)?;
    match text.split_whitespace().last() {
        Some(version) if version == expected => Ok(()),
        Some(version) => Err(format!("it reported {version} instead of {expected}")),
        None => Err("it reported nothing".into()),
    }
}

/// Check that a command runs and produces output, without caring about the
/// exact version string.
fn probe_success(command: Command, output_dir: &std::path::Path, timeout: Duration) -> bool {
    probe_output(command, output_dir, timeout).is_ok()
}

fn probe_output(
    mut command: Command,
    output_dir: &std::path::Path,
    timeout: Duration,
) -> Result<String, String> {
    let base = output_dir.join(format!(
        ".health-{}-{}",
        std::process::id(),
        PROBE_ID.fetch_add(1, Ordering::Relaxed)
    ));
let output_path = base.with_extension("out");
    // stderr goes to its own file: it is only quoted in failure messages, so
    // a stray warning can never corrupt the version parsed from stdout.
    let errors_path = base.with_extension("err");
    let open = |path: &std::path::Path| {
        std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
            .map_err(|e| format!("could not capture its output: {e}"))
    };
    let output = open(&output_path)?;
    let errors = match open(&errors_path) {
        Ok(errors) => errors,
        Err(e) => {
            let _ = std::fs::remove_file(&output_path);
            return Err(e);
        }
    };
    command
        .stdin(Stdio::null())
        .stdout(Stdio::from(output))
        .stderr(Stdio::from(errors));
    process::own_group(&mut command);
    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(e) => {
            let _ = std::fs::remove_file(&output_path);
            let _ = std::fs::remove_file(&errors_path);
            return Err(format!("it did not start: {e}"));
        }
    };
    let pid = child.id();
    let deadline = Instant::now() + timeout;
    // Ok(()) ran clean, Err(Some(status)) exited badly, Err(None) timed out.
    let result: Result<(), Option<std::process::ExitStatus>> = loop {
        match child.try_wait() {
            Ok(Some(status)) if status.success() => break Ok(()),
            Ok(Some(status)) => break Err(Some(status)),
            Ok(None) if Instant::now() < deadline => {
                std::thread::sleep(Duration::from_millis(25));
            }
            Ok(None) | Err(_) => {
                process::kill_tree_force(pid);
                let _ = child.wait();
                break Err(None);
            }
        }
    };
    let text = std::fs::read_to_string(&output_path).unwrap_or_default();
    let errors = std::fs::read_to_string(&errors_path).unwrap_or_default();
    let _ = std::fs::remove_file(output_path);
    let _ = std::fs::remove_file(errors_path);
    match result {
        Ok(()) => Ok(text),
        Err(None) => Err(format!("it did not finish within {}s", timeout.as_secs())),
        Err(Some(status)) => {
            // The last few lines, because loader errors like dyld's spread the
            // useful part (library, referenced from, reason) across lines.
            // stderr first: that is where CLIs put the failure.
            let tail = |stream: &str| {
                let mut lines: Vec<&str> = stream
                    .lines()
                    .map(str::trim)
                    .filter(|line| !line.is_empty())
                    .rev()
                    .take(3)
                    .collect();
                lines.reverse();
                lines.join(" / ")
            };
            let said = Some(tail(&errors))
                .filter(|t| !t.is_empty())
                .or_else(|| Some(tail(&text)).filter(|t| !t.is_empty()))
                .map(|t| format!(" saying {t:?}"))
                .unwrap_or_default();
            match status.code() {
                Some(code) => Err(format!("it exited with status {code}{said}")),
                None => Err(format!("it was killed{said}")),
            }
        }
    }
}

fn adapter_pins() -> Vec<String> {
    agents::ALL
        .iter()
        .filter_map(|kind| kind.adapter().map(String::from))
        .collect()
}

/// The operating system, for the About box: `sw_vers -productVersion` on
/// macOS, `cmd /c ver` on Windows ("Microsoft Windows [Version 10.0.22631.0]"),
/// parsed down to the version string.
fn os_version() -> String {
    let output = if cfg!(windows) {
        std::process::Command::new("cmd")
            .args(["/c", "ver"])
            .output()
    } else {
        std::process::Command::new("sw_vers")
            .arg("-productVersion")
            .output()
    };
    let text = output
        .ok()
        .filter(|out| out.status.success())
        .and_then(|out| String::from_utf8(out.stdout).ok())
        .unwrap_or_default();
    #[cfg(windows)]
    {
        // "Microsoft Windows [Version 10.0.22631.4037]" -> "10.0.22631.4037"
        text.split("[Version ").nth(1).and_then(|rest| rest.split(']').next())
            .map(|v| format!("Windows {v}"))
            .unwrap_or_else(|| "Windows".into())
    }
    #[cfg(not(windows))]
    {
        let version = text.trim();
        if version.is_empty() {
            "macOS".into()
        } else {
            format!("macOS {version}")
        }
    }
}

/// The wheel filename is the one place the bundled nurb version is written
/// down (`nurb-0.10.0-py3-none-any.whl`); the stamp only stores hashes.
fn wheel_version(name: &str) -> Option<&str> {
    name.strip_prefix("nurb-")?
        .strip_suffix(".whl")?
        .split('-')
        .next()
}

/// The newest bundled wheel, never the first the filesystem yields. An
/// in-place upgrade leaves the previous release's wheel behind (NSIS does not
/// clean resources on install-over), so without a deterministic version-ordered
/// choice a stale wheel could shadow the new one: the app would provision the
/// old engine (or show the old version in the About box) while calling itself
/// the new version.
fn newest_wheel(dir: &std::path::Path) -> Result<PathBuf, String> {
    std::fs::read_dir(dir)
        .map_err(|e| format!("cannot read {}: {e}", dir.display()))?
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| {
            path.file_name()
                .and_then(|name| name.to_str())
                .is_some_and(|name| name.starts_with("nurb-") && name.ends_with(".whl"))
        })
        .max_by_key(|path| wheel_version_key(path))
        .ok_or_else(|| format!("no nurb wheel bundled in {}", dir.display()))
}

/// A sortable version key for a wheel path: numeric components, so 0.10.0
/// sorts after 0.9.0 (lexicographic string order would get that wrong).
fn wheel_version_key(path: &std::path::Path) -> Option<(u64, u64, u64)> {
    let version = wheel_version(path.file_name()?.to_str()?)?;
    let mut parts = version.split('.');
    let major = parts.next()?.parse().ok()?;
    let minor = parts.next()?.parse().ok()?;
    let patch = parts.next()?.parse().ok()?;
    Some((major, minor, patch))
}

/// The OCCT version behind the pinned OCP wheels: `cadquery-ocp-novtk==7.9.3.1.1`
/// in the lock means OCCT 7.9.3, which the notices screen turns into a pointer
/// at the exact sources.
fn occt_version(lock: &str) -> Option<String> {
    let pin = lock
        .lines()
        .find_map(|line| line.trim().strip_prefix("cadquery-ocp"))?;
    let version = pin.split("==").nth(1)?.split_whitespace().next()?;
    let parts: Vec<&str> = version.split('.').take(3).collect();
    (parts.len() == 3).then(|| parts.join("."))
}

#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AboutInfo {
    pub app_version: String,
    pub nurb_version: String,
    pub occt_version: Option<String>,
    pub os_version: String,
    pub arch: String,
}

#[tauri::command]
pub fn about_info(app: tauri::AppHandle) -> Result<AboutInfo, String> {
    let app_version = app.package_info().version.to_string();
    let dir = app
        .path()
        .resource_dir()
        .map_err(|e| format!("no resource dir: {e}"))?
        .join("resources");
    let wheel = newest_wheel(&dir)?;
    let nurb_version = wheel
        .file_name()
        .and_then(|name| name.to_str())
        .and_then(wheel_version)
        .ok_or_else(|| format!("no nurb wheel bundled in {}", dir.display()))?
        .to_string();
    let occt_version = std::fs::read_to_string(dir.join("requirements.lock"))
        .ok()
        .and_then(|lock| occt_version(&lock));
    let os_version = os_version();
    Ok(AboutInfo {
        app_version,
        nurb_version,
        occt_version,
        os_version,
        arch: std::env::consts::ARCH.into(),
    })
}

#[tauri::command]
pub async fn provision_status(app: tauri::AppHandle) -> Result<bool, String> {
    let launcher = app.state::<Launcher>().inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let Some(paths) = launcher.paths() else {
            return Ok(true);
        };
        let res = resources(&app)?;
        let stamp = read_stamp(paths);
        Ok(parts_ok(paths, &res, &stamp) && chat_ok(paths, &res, &stamp))
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub async fn provision(
    app: tauri::AppHandle,
    on_event: Channel<ProvisionEvent>,
) -> Result<(), String> {
    let launcher = app.state::<Launcher>().inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let Some(paths) = launcher.paths() else {
            return Ok(());
        };
        run(&app, paths, &on_event)
    })
    .await
    .map_err(|e| e.to_string())?
}

fn run(
    app: &tauri::AppHandle,
    paths: &Paths,
    channel: &Channel<ProvisionEvent>,
) -> Result<(), String> {
    let provisioner = app.state::<Provisioner>();
    let _guard = provisioner.run.lock().unwrap();
    let res = resources(app)?;
    std::fs::create_dir_all(paths.data()).map_err(|e| format!("could not create app data: {e}"))?;
    let mut stamp = read_stamp(paths);
    if !parts_ok(paths, &res, &stamp) {
        provision_parts(&provisioner, paths, &res, channel)?;
        stamp.lock = res.lock_hash.clone();
        stamp.wheel = res.wheel_hash.clone();
        write_stamp(paths, &stamp)?;
    }
    if !chat_ok(paths, &res, &stamp) {
        provision_chat(&provisioner, paths, &res, channel)?;
        stamp.node = NODE_VERSION.into();
        stamp.adapters = adapter_pins();
        stamp.adapter_lock = res.adapter_lock_hash.clone();
        write_stamp(paths, &stamp)?;
    }
    Ok(())
}

/// uv, contained: managed Python installs, the cache, and all discovery kept
/// inside app data (cwd included, so uv never finds a stray pyproject).
fn uv(paths: &Paths) -> Result<Command, String> {
    let mut command = Command::new(uv_sidecar()?);
    command
        .env("UV_PYTHON_INSTALL_DIR", paths.python_dir())
        .env("UV_CACHE_DIR", paths.uv_cache())
        .env("UV_NO_CONFIG", "1")
        .env("UV_NO_PROGRESS", "1")
        .current_dir(paths.data());
    Ok(command)
}

fn provision_parts(
    provisioner: &Provisioner,
    paths: &Paths,
    res: &Resources,
    channel: &Channel<ProvisionEvent>,
) -> Result<(), String> {
    stage(channel, "python");
    let mut install = uv(paths)?;
    install.args(["python", "install", PYTHON_VERSION]);
    run_step(provisioner, channel, install, "the Python download")?;

    // Always rebuilt from scratch: a stale or half-installed venv repairs by
    // deletion, never by patching.
    if paths.venv().exists() {
        std::fs::remove_dir_all(paths.venv())
            .map_err(|e| format!("could not clear the old environment: {e}"))?;
    }
    let mut venv = uv(paths)?;
    venv.arg("venv")
        .arg(paths.venv())
        .args(["--python", PYTHON_VERSION, "--managed-python"]);
    run_step(provisioner, channel, venv, "the environment setup")?;

    stage(channel, "deps");
    let mut sync = uv(paths)?;
    sync.args(["pip", "sync", "--python"])
        .arg(paths.venv_python())
        .arg(&res.lock);
    run_step(provisioner, channel, sync, "the CAD engine download")?;

    let mut wheel = uv(paths)?;
    wheel
        .args(["pip", "install", "--no-deps", "--python"])
        .arg(paths.venv_python())
        .arg(&res.wheel);
    run_step(provisioner, channel, wheel, "the nurb install")?;

    stage(channel, "warmup");
    let mut warmup = Command::new(paths.venv_python());
    // The first OCCT import is the slow one; do it here, never on the first
    // project open.
    warmup.args(["-c", "import build123d, nurb"]);
    run_step(provisioner, channel, warmup, "the CAD engine warmup")?;
    // Same tradeoff as the npm cache below: ~480 MB that only speeds up a
    // reinstall, on a machine that just proved it can download the wheels.
    let _ = std::fs::remove_dir_all(paths.uv_cache());
    Ok(())
}

fn provision_chat(
    provisioner: &Provisioner,
    paths: &Paths,
    res: &Resources,
    channel: &Channel<ProvisionEvent>,
) -> Result<(), String> {
    stage(channel, "chat");
    let (archive_name, sha) = node_archive();
    let archive = paths.data().join(archive_name);
    let mut download = curl();
    download
        .args(["-fSL", "--retry", "3", "-o"])
        .arg(&archive)
        .arg(format!("https://nodejs.org/dist/{NODE_VERSION}/{archive_name}"));
    run_step(provisioner, channel, download, "the chat runtime download")?;
    let bytes = std::fs::read(&archive)
        .map_err(|e| format!("could not read {archive_name}: {e}"))?;
    if format!("{:x}", Sha256::digest(&bytes)) != sha {
        let _ = std::fs::remove_file(&archive);
        return Err("the chat runtime download did not match its checksum".into());
    }
    if paths.node_dir().exists() {
        std::fs::remove_dir_all(paths.node_dir())
            .map_err(|e| format!("could not clear the old runtime: {e}"))?;
    }
    std::fs::create_dir_all(paths.node_dir()).map_err(|e| e.to_string())?;
    let mut extract = tar();
    // The Windows zip and the Unix xz both extract with strip-components,
    // dropping the archive's single top-level directory.
    extract
        .arg("-xf")
        .arg(&archive)
        .arg("-C")
        .arg(paths.node_dir())
        .args(["--strip-components", "1"]);
    run_step(provisioner, channel, extract, "the chat runtime unpack")?;
    let _ = std::fs::remove_file(&archive);

    if paths.adapters().exists() {
        std::fs::remove_dir_all(paths.adapters())
            .map_err(|e| format!("could not clear the old agents: {e}"))?;
    }
    std::fs::create_dir_all(paths.adapters())
        .map_err(|e| format!("could not create the agent environment: {e}"))?;
    std::fs::copy(&res.adapter_package, paths.adapters().join("package.json"))
        .map_err(|e| format!("could not stage the agent manifest: {e}"))?;
    std::fs::copy(
        &res.adapter_lock,
        paths.adapters().join("package-lock.json"),
    )
    .map_err(|e| format!("could not stage the agent lock: {e}"))?;

    let mut install = Command::new(paths.node_bin());
    install
        .arg(paths.npm_cli())
        // A user's npm config may omit optional dependencies, but both agent
        // SDKs ship their macOS binaries as platform-specific optionals.
        .args(NPM_CI_ARGS)
        .arg("--cache")
        .arg(paths.adapters().join("npm-cache"))
        .current_dir(paths.adapters());
    run_step(provisioner, channel, install, "the agent install")?;
    // The npm cache is ~250 MB that only helps a reinstall, and adapter pins
    // change with app updates, not day to day.
    let _ = std::fs::remove_dir_all(paths.adapters().join("npm-cache"));
chat_runtime_check(paths).map_err(|why| format!("the agent install finished, but {why}"))
}

/// curl, from wherever this platform keeps it. Windows 10 ships curl.exe in
/// System32; a missing one is an actionable failure at the first download.
fn curl() -> Command {
    #[cfg(windows)]
    {
        let system32 = std::env::var_os("SystemRoot")
            .map(PathBuf::from)
            .map(|root| root.join("System32").join("curl.exe"));
        match system32.filter(|path| path.is_file()) {
            Some(path) => Command::new(path),
            None => Command::new("curl"),
        }
    }
    #[cfg(not(windows))]
    {
        Command::new("/usr/bin/curl")
    }
}

/// tar, from wherever this platform keeps it. Windows ships bsdtar in
/// System32, which reads both the xz tarballs and the Windows zips.
fn tar() -> Command {
    #[cfg(windows)]
    {
        let system32 = std::env::var_os("SystemRoot")
            .map(PathBuf::from)
            .map(|root| root.join("System32").join("tar.exe"));
        match system32.filter(|path| path.is_file()) {
            Some(path) => Command::new(path),
            None => Command::new("tar"),
        }
    }
    #[cfg(not(windows))]
    {
        Command::new("/usr/bin/tar")
    }
}

fn stage(channel: &Channel<ProvisionEvent>, stage: &'static str) {
    let _ = channel.send(ProvisionEvent::Stage { stage });
}

/// Spawns one provisioning child in its own process group (killed on app
/// exit like every other child), streaming its output lines to the setup
/// screen and keeping a short tail for the error message.
fn run_step(
    provisioner: &Provisioner,
    channel: &Channel<ProvisionEvent>,
    mut command: Command,
    what: &str,
) -> Result<(), String> {
    if provisioner.shutting_down.load(Ordering::SeqCst) {
        return Err("app is shutting down".into());
    }
    process::own_group(&mut command);
    command
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = command
        .spawn()
        .map_err(|e| format!("could not start {what}: {e}"))?;
    let pid = child.id();
    *provisioner.pid.lock().unwrap() = Some(pid);
    // A shutdown can land between the check above and the spawn; now that the
    // pid is published, re-check so that window cannot leak the child.
    if provisioner.shutting_down.load(Ordering::SeqCst) {
        process::kill_tree(pid);
    }
    let tail = Arc::new(Mutex::new(VecDeque::<String>::new()));
    let readers = [
        child.stdout.take().map(|out| {
            stream_lines(
                Box::new(out) as Box<dyn std::io::Read + Send>,
                channel.clone(),
                tail.clone(),
            )
        }),
        child.stderr.take().map(|err| {
            stream_lines(
                Box::new(err) as Box<dyn std::io::Read + Send>,
                channel.clone(),
                tail.clone(),
            )
        }),
    ];
    let status = child.wait();
    *provisioner.pid.lock().unwrap() = None;
    for reader in readers.into_iter().flatten() {
        let _ = reader.join();
    }
    let status = status.map_err(|e| format!("{what} failed: {e}"))?;
    if status.success() {
        Ok(())
    } else if provisioner.shutting_down.load(Ordering::SeqCst) {
        Err("app is shutting down".into())
    } else {
        let lines: Vec<String> = tail.lock().unwrap().iter().cloned().collect();
        Err(format!("{what} failed: {}", lines.join(" / ")))
    }
}

fn stream_lines(
    reader: Box<dyn std::io::Read + Send>,
    channel: Channel<ProvisionEvent>,
    tail: Arc<Mutex<VecDeque<String>>>,
) -> std::thread::JoinHandle<()> {
    std::thread::spawn(move || {
        for line in BufReader::new(reader).lines() {
            let Ok(line) = line else { break };
            // Not eprintln!, which panics on a broken stderr pipe.
            let _ = writeln!(std::io::stderr(), "[provision] {line}");
            if line.trim().is_empty() {
                continue;
            }
            let mut tail = tail.lock().unwrap();
            if tail.len() >= 4 {
                tail.pop_front();
            }
            tail.push_back(line.clone());
            drop(tail);
            let _ = channel.send(ProvisionEvent::Detail { line });
        }
    })
}

#[cfg(test)]
mod tests {
    use std::process::Command;
    use std::time::Duration;

    use super::{
chat_runtime_check, chat_runtime_ok, file_hash, occt_version, probe_version, wheel_version,
        NPM_CI_ARGS, PROBE_ID,
    };
    use crate::env::Paths;

    /// A command that prints `text`, on any platform.
    fn echo(text: &str) -> Command {
        #[cfg(windows)]
        {
            let mut command = Command::new("cmd");
            command.args(["/C", &format!("echo {text}")]);
            command
        }
        #[cfg(not(windows))]
        {
            let mut command = Command::new("/bin/sh");
            command.args(["-c", &format!("printf '%s\\n' '{text}'")]);
            command
        }
    }

    /// A command that sleeps `secs` seconds, on any platform.
    fn sleep(secs: u64) -> Command {
        #[cfg(windows)]
        {
            let mut command = Command::new("cmd");
            // ping's 1s interval with n=secs+1 gives roughly secs seconds, and
            // its output is discarded by the probe.
            command.args(["/C", &format!("ping -n {} 127.0.0.1 >nul", secs + 1)]);
            command
        }
        #[cfg(not(windows))]
        {
            let mut command = Command::new("/bin/sh");
            command.args(["-c", &format!("sleep {secs}")]);
            command
        }
    }

    #[test]
    fn wheel_filename_yields_the_bundled_version() {
        assert_eq!(
            wheel_version("nurb-0.10.0-py3-none-any.whl"),
            Some("0.10.0")
        );
        assert_eq!(wheel_version("requirements.lock"), None);
        assert_eq!(wheel_version("nurb-0.10.0.tar.gz"), None);
    }

    #[test]
    fn newest_wheel_wins_after_an_in_place_upgrade() {
        // An upgrade leaves the old release's wheel in resources (NSIS does
        // not clean it), and read_dir order is not defined. The pick must be
        // deterministic and version-ordered, or a stale wheel shadows the new
        // one and the app keeps its old engine (or the About box its old
        // version). 0.10.0 vs 0.9.0 also guards against a lexicographic
        // comparison, which would get that wrong.
        let dir = std::env::temp_dir().join(format!("nurb-wheel-pick-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        for name in [
            "nurb-0.9.0-py3-none-any.whl",
            "nurb-0.10.0-py3-none-any.whl",
        ] {
            std::fs::write(dir.join(name), b"wheel").unwrap();
        }
        let picked = super::newest_wheel(&dir).unwrap();
        assert_eq!(
            picked.file_name().unwrap().to_str().unwrap(),
            "nurb-0.10.0-py3-none-any.whl"
        );
        // An empty dir is an error, not a silent fallback.
        std::fs::remove_dir_all(&dir).unwrap();
        std::fs::create_dir_all(&dir).unwrap();
        assert!(super::newest_wheel(&dir).is_err());
        std::fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn occt_version_comes_from_the_ocp_pin() {
        let lock = "build123d==0.10.0 \\\n    --hash=sha256:aa\ncadquery-ocp-novtk==7.9.3.1.1 \\\n    --hash=sha256:bb\n";
        assert_eq!(occt_version(lock), Some("7.9.3".into()));
        assert_eq!(occt_version("trimesh==4.0.0"), None);
    }

    #[test]
    fn resource_hash_changes_with_same_named_wheel_contents() {
        let dir = std::env::temp_dir().join(format!("nurb-wheel-hash-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let wheel = dir.join("nurb-0.10.0-py3-none-any.whl");
        std::fs::write(&wheel, b"first build").unwrap();
        let first = file_hash(&wheel, "wheel").unwrap();
        std::fs::write(&wheel, b"changed build").unwrap();
        let second = file_hash(&wheel, "wheel").unwrap();

        assert_ne!(first, second);
        std::fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn health_probe_requires_the_expected_version_and_cannot_hang() {
        let dir = std::env::temp_dir();
        // Three seconds, not one: a `cmd /C echo` on a busy CI box (or this
        // machine mid-build) can exceed a tight budget even though the probe
        // itself is healthy. The cannot-hang half below still uses a tiny
        // timeout, so the guard is what this test actually proves.
        let budget = Duration::from_secs(3);
        assert!(probe_version(echo("adapter 1.2.3"), &dir, "1.2.3", budget).is_ok());
        assert!(probe_version(echo("9.9.9"), &dir, "1.2.3", budget).is_err());
        assert!(probe_version(
            sleep(5),
            &dir,
            "1.2.3",
            Duration::from_millis(50)
        ).is_err());
    }
    #[test]
    fn npm_install_forces_platform_optional_dependencies() {
        assert!(NPM_CI_ARGS
            .windows(2)
            .any(|args| args == ["ci", "--include=optional"]));
    }

    #[cfg(not(windows))]
    #[test]
    fn chat_health_exercises_the_native_agent_clis() {
        use super::chat_runtime_ok;
        use crate::env::NODE_VERSION;
        use std::os::unix::fs::PermissionsExt;

        let dir = std::env::temp_dir().join(format!(
            "nurb-chat-health-{}-{}",
            std::process::id(),
            PROBE_ID.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
        ));
        let paths = Paths::new(dir.clone());
        std::fs::create_dir_all(paths.node_dir().join("bin")).unwrap();
        std::fs::create_dir_all(paths.adapters().join("node_modules/.bin")).unwrap();

        let node = paths.node_bin();
        std::fs::write(
            &node,
            format!(
                r#"#!/bin/sh
case "$*" in
  "--version") echo "{NODE_VERSION}" ;;
  *"claude-agent-acp --cli --version"*)
    [ ! -f "$0.missing-claude" ] || exit 1
    [ ! -f "$0.slow-claude" ] || sleep 3
    echo "2.1.220 (Claude Code)"
    ;;
  *"claude-agent-acp --version"*) echo "claude-agent-acp 0.64.2" ;;
  *"codex-acp --version"*) echo "codex-acp 1.1.9" ;;
    *"gemini --version"*) echo "0.55.1" ;;
  *"/codex --version"*)
    [ ! -f "$0.missing-codex" ] || exit 1
    echo "codex-cli 0.145.0"
    ;;
  *) exit 1 ;;
esac
"#
            ),
        )
        .unwrap();
        std::fs::set_permissions(&node, std::fs::Permissions::from_mode(0o755)).unwrap();
        for agent in ["claude-agent-acp", "codex-acp", "gemini", "codex"] {
            std::fs::write(paths.adapters().join("node_modules/.bin").join(agent), b"").unwrap();
        }

        assert!(chat_runtime_ok(&paths));
        let slow_claude = format!("{}.slow-claude", node.display());
        std::fs::write(&slow_claude, b"").unwrap();
        assert!(chat_runtime_ok(&paths));
        std::fs::remove_file(slow_claude).unwrap();
        let missing_claude = format!("{}.missing-claude", node.display());
        std::fs::write(&missing_claude, b"").unwrap();
        let why = chat_runtime_check(&paths).unwrap_err();
        assert!(why.starts_with("the Claude CLI check failed:"), "{why}");
        std::fs::remove_file(missing_claude).unwrap();
        std::fs::write(format!("{}.missing-codex", node.display()), b"").unwrap();
        let why = chat_runtime_check(&paths).unwrap_err();
        assert!(why.starts_with("the Codex CLI check failed:"), "{why}");

        std::fs::remove_dir_all(dir).unwrap();
    }

    /// The Windows-only path resolution: adapter scripts come out of the
    /// package's own bin field (the .bin shims are shell scripts node cannot
    /// run), and CODEX_PATH points at the native binary the platform package
    /// vendors.
    #[cfg(windows)]
    #[test]
    fn windows_adapter_layout_resolves_js_entries_and_the_native_codex() {
        use crate::agents::AgentKind;

        let dir = std::env::temp_dir().join(format!(
            "nurb-win-adapters-{}-{}",
            std::process::id(),
            PROBE_ID.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
        ));
        let paths = Paths::new(dir.clone());
        let pkg = paths.adapters().join("node_modules/@agentclientprotocol");
        std::fs::create_dir_all(&pkg).unwrap();
        for (name, bin) in [
            ("claude-agent-acp", "dist/index.js"),
            ("codex-acp", "dist/index.js"),
        ] {
            let dir = pkg.join(name);
            std::fs::create_dir_all(dir.join("dist")).unwrap();
            std::fs::write(dir.join("dist/index.js"), b"").unwrap();
            std::fs::write(
                dir.join("package.json"),
                format!(r#"{{"name":"@{name}","bin":{{"{name}":"{bin}"}}}}"#),
            )
            .unwrap();
        }
        // The platform package vendoring the native codex.exe.
        let vendor = paths
            .adapters()
            .join("node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin");
        std::fs::create_dir_all(&vendor).unwrap();
        std::fs::write(vendor.join("codex.exe"), b"").unwrap();

        assert!(paths
            .adapter_script(AgentKind::Claude)
            .ends_with("dist/index.js"));
        assert!(paths
            .adapter_script(AgentKind::Codex)
            .ends_with("dist/index.js"));
        assert!(paths.codex_cli().ends_with("bin\\codex.exe"));

        std::fs::remove_dir_all(dir).unwrap();
    }
}
