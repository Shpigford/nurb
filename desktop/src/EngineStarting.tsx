import { useEffect, useState } from "react";
import { brand, Button } from "@nurb/ui";

/// Sheets 24 and 24b: waiting for the serve, or reporting why it never came up.
/// `log` is the tail of the engine's own output when the serve can hand one
/// over; the excerpt block only appears when there is something to show.
export default function EngineStarting({
  error,
  onRetry,
  log,
}: {
  error: string | null;
  onRetry: () => void;
  log?: string | null;
}) {
  const [seconds, setSeconds] = useState(0);
  const [showLog, setShowLog] = useState(false);
  useEffect(() => {
    if (error) return;
    const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [error]);

  const lines = (log ?? "").split("\n").filter((l) => l.trim().length > 0);

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
          <span className="mono-label chrome text-muted">{error ? "Engine" : "Starting"}</span>
        </div>
        <div className="flex flex-col p-7">
          <img src={brand.markSmall} alt="" aria-hidden="true" className="size-10 shrink-0" />
          {error ? (
            <>
              <h1 className="font-display mt-5 text-[22px] leading-7 tracking-[-0.02em] text-ink">The engine did not start</h1>
              <div className="mt-5 flex flex-col rounded-content bg-fail-wash p-3">
                <div className="btn-label text-fail">Engine stopped</div>
                <p className="mt-1.5 text-[13px] leading-5 text-ink-soft">{error}</p>
              </div>
              {lines.length > 0 && showLog ? (
                <div className="mt-4 flex flex-col gap-1 rounded-content bg-raised p-3">
                  {lines.map((l, i) => (
                    <div key={i} className="font-mono text-[10.5px] leading-[14px] text-muted">
                      {l}
                    </div>
                  ))}
                </div>
              ) : null}
              <div className="mt-5 flex items-center gap-2">
                <Button variant="accent" size="md" className="px-[18px]" onClick={onRetry}>
                  Try again
                </Button>
                {lines.length > 0 ? (
                  <Button variant="outline" size="md" className="px-[18px]" onClick={() => setShowLog((v) => !v)}>
                    {showLog ? "Hide log" : "Show log"}
                  </Button>
                ) : null}
              </div>
            </>
          ) : (
            <>
              <h1 className="font-display mt-5 text-[22px] leading-7 tracking-[-0.02em] text-ink">Starting the engine</h1>
              <div className="mt-[22px] flex items-center gap-2.5">
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" className="shrink-0 animate-spin">
                  <circle cx="8" cy="8" r="6.4" fill="none" stroke="var(--color-line)" strokeWidth="1.6" />
                  <path d="M8 1.6A6.4 6.4 0 0 1 14.4 8" fill="none" stroke="var(--color-accent)" strokeWidth="1.6" strokeLinecap="round" />
                </svg>
                <span className="font-mono text-[11px] leading-[14px] font-medium tracking-[0.04em] text-ink-soft">Waking the kernel</span>
              </div>
              {seconds >= 10 ? (
                <p className="mt-3.5 text-[13px] leading-5 text-muted">{seconds}s · a cold start can take a few minutes when the computer is busy.</p>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
