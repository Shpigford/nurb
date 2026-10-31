import { useEffect, useRef, useState } from "react";
import { Channel, invoke } from "@tauri-apps/api/core";
import { openUrl } from "@tauri-apps/plugin-opener";
import { brand, Button, TaskSteps } from "@nurb/ui";
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

// Sheet 23: the four stages as a checklist, in the order provision.rs runs
// them. The short label is what the row shows; STAGE_COPY is the sentence
// under the bar.
const STAGES = [
  { id: "python", label: "Runtime" },
  { id: "deps", label: "Engine" },
  { id: "warmup", label: "Warm-up" },
  { id: "chat", label: "Chat" },
];

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

  // Opens a bug report with the error, app version, macOS version, and
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
        `macOS ${about.osVersion} (${about.arch})`,
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

  // Before the first stage event the first row is the one in flight.
  const current = Math.max(0, STAGES.findIndex((s) => s.id === stage));

  return (
    <div
      className="relative isolate flex h-dvh flex-col items-center justify-center overflow-hidden bg-stage"
      data-tauri-drag-region
    >
      <img
        src={brand.authPlane}
        alt=""
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-1/2 -z-10 h-[900px] w-[1440px] max-w-none -translate-1/2 select-none"
      />
      <div className="panel flex w-[440px] flex-col overflow-hidden">
        <div className="flex h-[30px] shrink-0 items-center border-b border-line-soft px-4">
          <span className="mono-label chrome text-muted">Setting up</span>
        </div>
        <div className="flex flex-col p-7">
          <img src={brand.markSmall} alt="" aria-hidden="true" className="size-10 shrink-0" />
          <h1 className="font-display mt-5 text-[22px] leading-7 tracking-[-0.02em] text-ink">Setting up your workshop</h1>
          <p className="mt-2 text-[14px] leading-[22px] text-ink-soft">Takes a minute the first time. Your parts stay on this Mac.</p>
          <TaskSteps
            className="mt-6"
            label="Setup progress"
            steps={STAGES}
            current={current}
            failed={Boolean(error)}
          />
          {error ? (
            <div className="mt-5 flex flex-col">
              <div className="flex flex-col rounded-content bg-fail-wash p-3">
                <div className="btn-label text-fail">Setup did not finish</div>
                <p className="mt-1.5 text-[13px] leading-5 text-ink-soft">{error}</p>
              </div>
              <div className="mt-5 flex items-center gap-2">
                <Button variant="accent" size="md" className="px-[18px]" onClick={start}>
                  Try again
                </Button>
                <Button variant="outline" size="md" className="px-[18px]" onClick={report}>
                  Report this
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-5 flex flex-col">
              <div className="relative h-[3px] shrink-0 overflow-hidden rounded-full bg-line-soft">
                <div className="animate-slide absolute top-0 left-0 h-[3px] w-24 rounded-full bg-accent" />
              </div>
              <p className="mt-3 font-mono text-[10.5px] leading-[14px] font-medium tracking-[0.04em] text-muted">
                {`${STAGE_COPY[stage ?? ""] ?? "Checking what's installed"}…`}
              </p>
              {/* The installer's own output, under the sentence rather than in
                  place of it, so the hobbyist words are always the ones on top. */}
              {line ? (
                <p className="mt-1 truncate font-mono text-[10.5px] leading-[14px] text-faint">{line}</p>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
