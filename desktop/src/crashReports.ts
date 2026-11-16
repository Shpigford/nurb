import * as Sentry from "@sentry/browser";
import { invoke } from "@tauri-apps/api/core";

// The shell owns the DSN and the switch, so the page and the Rust side report
// under one setting. A build without a DSN (every debug and source build) sends
// nothing.
type CrashReports = { dsn: string | null; enabled: boolean; release: string };

let enabled = false;

// Paths under a home folder carry the account name.
export function scrub(text: string): string {
  return text.replace(/\/Users\/[^/"'\s\\]+/g, "~");
}

export async function startCrashReports(): Promise<void> {
  const said = await invoke<CrashReports>("crash_reports").catch(() => null);
  if (!said?.dsn) return;
  enabled = said.enabled;
  Sentry.init({
    dsn: said.dsn,
    release: said.release,
    dataCollection: {
      userInfo: false,
      cookies: false,
      httpHeaders: false,
      httpBodies: [],
      urlQueryParams: false,
    },
    // Breadcrumbs record clicks, console lines and request URLs, which name a
    // person's parts and projects.
    integrations: (defaults) => defaults.filter((integration) => integration.name !== "Breadcrumbs"),
    // A request to an engine that is restarting fails like this, and the shell
    // already reports the engine dying.
    ignoreErrors: [/Load failed/, /Failed to fetch/, /NetworkError/],
    beforeSend: (event) => (enabled ? JSON.parse(scrub(JSON.stringify(event))) : null),
  });
}

export async function readCrashReports(): Promise<boolean> {
  const said = await invoke<CrashReports>("crash_reports");
  return said.enabled;
}

export async function setCrashReports(on: boolean): Promise<void> {
  await invoke("set_crash_reports", { enabled: on });
  enabled = on;
}
