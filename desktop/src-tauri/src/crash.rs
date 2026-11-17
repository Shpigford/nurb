//! Crash reports: Rust panics, the engine dying, and the engine's unhandled
//! errors go to Sentry. The page reports its own errors with the same DSN and
//! the same switch.
//!
//! Only a release build made by `scripts/release.sh` carries a DSN, so a fork,
//! a source build and every debug build send nothing. Errors in a person's own
//! part never get here: the engine catches those and shows them on the part.

use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};

use tauri::State;

#[cfg(not(debug_assertions))]
const DSN: Option<&str> = option_env!("NURB_SENTRY_DSN");
#[cfg(debug_assertions)]
const DSN: Option<&str> = None;

/// Present when the person turned reports off. A file rather than a JSON pref,
/// because the panic hook has to know before anything else has loaded.
const OFF_FILE: &str = "crash-reports-off";

static ENABLED: AtomicBool = AtomicBool::new(false);

pub struct CrashReports {
    dir: PathBuf,
    release: String,
}

fn dsn() -> Option<&'static str> {
    DSN.filter(|dsn| !dsn.is_empty())
}

pub fn init(dir: &Path, version: &str) -> CrashReports {
    ENABLED.store(!dir.join(OFF_FILE).exists(), Ordering::Relaxed);
    let release = format!("nurb@{version}");
    if let Some(dsn) = dsn() {
        // Forgotten on purpose: the client lives as long as the process, and
        // `flush` at exit sends whatever is still queued.
        std::mem::forget(sentry::init(
            sentry::ClientOptions::new()
                .dsn(dsn)
                .release(release.clone())
                .before_send(|event| ENABLED.load(Ordering::Relaxed).then(|| scrub(event))?),
        ));
    }
    CrashReports {
        dir: dir.to_path_buf(),
        release,
    }
}

/// Sends what is queued, so a report raised during shutdown is not lost.
pub fn flush() {
    if let Some(client) = sentry::Hub::current().client() {
        client.flush(Some(std::time::Duration::from_secs(2)));
    }
}

/// The hostname often carries the owner's name, and every path under the home
/// folder carries the account name, so both go before anything is sent.
fn scrub(mut event: sentry::protocol::Event<'static>) -> Option<sentry::protocol::Event<'static>> {
    event.server_name = None;
    let home = std::env::var("HOME").ok().filter(|home| home.len() > 1)?;
    let text = serde_json::to_string(&event).ok()?;
    serde_json::from_str(&scrub_text(&text, &home)).ok()
}

fn scrub_text(text: &str, home: &str) -> String {
    text.replace(home, "~")
}

/// An engine failure the person did not cause: it exited, stopped answering,
/// never started, or raised past its own error handling.
pub fn engine_error(title: &str, log: &str) {
    if dsn().is_none() {
        return;
    }
    sentry::with_scope(
        |scope| {
            scope.set_tag("source", "engine");
            scope.set_extra("engine_log", log.into());
            // An engine killed with no last words was killed from outside, and a
            // low number here says macOS ran out of memory (NURB-DESKTOP-6).
            if let Some(free) = memory_free_percent() {
                scope.set_extra("memory_free_percent", free.into());
            }
        },
        || sentry::capture_message(title, sentry::Level::Error),
    );
}

/// How much memory macOS considers free, 0 to 100: the level its
/// memory-pressure killer acts on.
fn memory_free_percent() -> Option<u32> {
    let mut level: u32 = 0;
    let mut size = std::mem::size_of::<u32>();
    let ok = unsafe {
        libc::sysctlbyname(
            c"kern.memorystatus_level".as_ptr(),
            (&mut level as *mut u32).cast(),
            &mut size,
            std::ptr::null_mut(),
            0,
        )
    } == 0;
    ok.then_some(level)
}

#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CrashReportsInfo {
    dsn: Option<&'static str>,
    enabled: bool,
    release: String,
}

#[tauri::command]
pub fn crash_reports(reports: State<CrashReports>) -> CrashReportsInfo {
    CrashReportsInfo {
        dsn: dsn(),
        enabled: ENABLED.load(Ordering::Relaxed),
        release: reports.release.clone(),
    }
}

#[tauri::command]
pub fn set_crash_reports(reports: State<CrashReports>, enabled: bool) -> Result<(), String> {
    let file = reports.dir.join(OFF_FILE);
    let saved = if enabled {
        std::fs::remove_file(&file).or_else(|e| match e.kind() {
            std::io::ErrorKind::NotFound => Ok(()),
            _ => Err(e),
        })
    } else {
        std::fs::write(&file, b"")
    };
    saved.map_err(|e| format!("could not save the crash report setting: {e}"))?;
    ENABLED.store(enabled, Ordering::Relaxed);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{memory_free_percent, scrub_text};

    #[test]
    fn an_engine_report_can_say_how_much_memory_was_free() {
        let free = memory_free_percent().expect("kern.memorystatus_level");
        assert!(free <= 100, "{free}");
    }

    #[test]
    fn the_home_folder_never_leaves_the_machine() {
        let log = r#"{"extra":{"engine_log":"File \"/Users/ada/Library/nurb/parts/x.py\", line 3"}}"#;
        let scrubbed = scrub_text(log, "/Users/ada");
        assert!(!scrubbed.contains("ada"));
        assert!(scrubbed.contains("~/Library/nurb/parts/x.py"));
    }
}
