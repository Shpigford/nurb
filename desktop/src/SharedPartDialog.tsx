import { useEffect, useRef } from "react";
import { Button } from "@nurb/ui";
import type { SharedPeek } from "@nurb/workbench/api";

// A link from someone's share page, before anything lands in the library. The part
// is shown so the person knows what they are opening; the one line under it is there
// because opening builds the part, and building runs the code that came with it.
export default function SharedPartDialog({
  peek,
  error,
  busy,
  onOpen,
  onCancel,
}: {
  /** Null while the link is still being read. */
  peek: SharedPeek | null;
  error: string | null;
  busy: boolean;
  onOpen: () => void;
  onCancel: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  const title = peek ? peek.title || peek.name.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase()) : null;

  return (
    <dialog
      ref={ref}
      aria-labelledby="shared-title"
      // Once opening has started it finishes, so the queue behind it stays in order.
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onCancel();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onCancel();
      }}
      className="panel m-auto w-[360px] max-w-[calc(100vw-32px)] overflow-hidden p-0 text-ink backdrop:bg-scrim/30"
    >
      <div className="flex aspect-[1200/630] items-center justify-center bg-stage">
        {peek ? (
          <img src={peek.picture} alt="" className="size-full object-contain" />
        ) : (
          <span className="mono-caption text-muted">{error ? "" : "READING THE LINK…"}</span>
        )}
      </div>
      <div className="flex flex-col gap-1 border-t border-line-soft px-4 pt-3.5 pb-3">
        <span className="mono-caption text-muted">SHARED PART</span>
        <h2 id="shared-title" className="font-display text-[18px] leading-6 font-bold tracking-[-0.02em] text-ink">
          {title ?? (error ? "This link did not open" : "Opening a shared part")}
        </h2>
        {error ? (
          <p className="text-[13px] leading-[19px] text-fail" role="alert">
            {error}
          </p>
        ) : (
          <p className="text-[13px] leading-[19px] text-muted">Only open parts from people you trust. Opening runs its code.</p>
        )}
      </div>
      <div className="flex justify-end gap-2 border-t border-line-soft px-4 py-3">
        <Button variant="outline" disabled={busy} onClick={onCancel}>
          {error ? "Close" : "Cancel"}
        </Button>
        {error ? null : (
          <Button variant="accent" disabled={!peek || busy} onClick={onOpen}>
            {busy ? "Opening…" : "Add to my library"}
          </Button>
        )}
      </div>
    </dialog>
  );
}
