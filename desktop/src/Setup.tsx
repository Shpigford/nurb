import { useEffect, useRef, useState } from "react";
import { Channel, invoke } from "@tauri-apps/api/core";
import { openUrl } from "@tauri-apps/plugin-opener";
import Logo from "./Logo";
import { osLabel } from "./platform";
import { setupReportUrl } from "./setupReport";

type ProvisionEvent =
  | { kind: "stage"; stage: string }
  | { kind: "detail"; line: string };

// Stage ids arrive from provision.rs; the copy lives here. Hobbyist words
// only: no Python, no venv, no npm.
const STAGE_COPY: Record<string, string> = {
  python: "Getting things ready",
  deps: "Downloading the CAD engine",
  warmup: "Preparing the CAD engine",
  chat: "Setting up the AI assistant",
};

/// First-launch provisioning screen. Mounts once, starts the install, and
/// hands the window back the moment the environment is healthy.
export default function Setup({ onDone }: { onDone: () => void }) {
  const [stage, setStage] = useState<string | null>(null);
  const [line, setLine] = useState("");
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  const start = async () => {
    setError(null);
    const channel = new Channel<ProvisionEvent>();
    channel.onmessage = (event) => {
      if (event.kind === "stage") {
        setStage(event.stage);
        setLine("");
      } else {
        setLine(event.line);
      }
    };
    try {
      await invoke("provision", { onEvent: channel });
      onDone();
    } catch (e) {
      setError(String(e));
    }
  };

  // Opens a bug report with the error, app version, OS version, and
  // architecture already filled in, so a failed setup never sends anyone
  // hunting through logs.
  const report = async () => {
    let version = "";
    try {
      const about = await invoke<{
        appVersion: string;
        nurbVersion: string;
        occtVersion: string | null;
        osVersion: string;
        arch: string;
      }>("about_info");
      version = [
        `app ${about.appVersion}`,
        `CAD engine ${about.nurbVersion}`,
        about.occtVersion ? `OCCT ${about.occtVersion}` : null,
        `${osLabel} ${about.osVersion} (${about.arch})`,
      ]
        .filter(Boolean)
        .join("\n");
    } catch {
      // The report is still useful without version info.
    }
    openUrl(setupReportUrl(version, error ?? ""));
  };

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="setup" data-tauri-drag-region>
      <div className="setup-card">
        <div className="setup-logo">
          <Logo size={40} />
        </div>
        <div className="setup-title">nurb</div>
        {error ? (
          <>
            <div className="setup-error">{error}</div>
            <div className="setup-actions">
              <button className="setup-retry" onClick={start}>
                try again
              </button>
              <button className="setup-retry" onClick={report}>
                report this
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="setup-stage">
              {(STAGE_COPY[stage ?? ""] ?? "Checking what's installed") + "…"}
            </div>
            <div className="setup-bar">
              <div className="setup-bar-fill" />
            </div>
            <div className="setup-detail">{line}</div>
            <div className="setup-note">
              First launch downloads the CAD engine and the AI assistant (a few
              hundred megabytes, one time). Your parts will live in ordinary
              folders in Documents.
            </div>
          </>
        )}
      </div>
    </div>
  );
}
