import clsx from "clsx"
import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from "react"
import { createPortal } from "react-dom"
import { Button, Icon, relativeTime, type Params } from "@nurb/ui"
import { sharePart, unsharePart, type PartShare } from "./api"

/**
 * The header's Share cell: a public link to the part on nurb.app, no account. The link
 * shows the part at the numbers on the sliders, and anyone with it can download the
 * files or open a copy in nurb. A part that has built again since keeps its link and
 * offers to bring it up to date, because the link may already be in someone's inbox.
 */
export function ShareMenu({
  partId,
  share,
  values,
  onCopy,
  onOpenLink,
}: {
  partId: string
  share: PartShare | null
  /** The slider values on screen, which is what the link will show. */
  values: Params
  /** The desktop copies through its own clipboard; a browser uses the page's. */
  onCopy?: (text: string) => Promise<void>
  onOpenLink?: (url: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState<"share" | "stop" | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [anchor, setAnchor] = useState<CSSProperties>()
  const trigger = useRef<HTMLButtonElement>(null)
  const panel = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setOpen(false)
    setError(null)
  }, [partId])

  useEffect(() => {
    if (!open) {
      setConfirming(false)
      setCopied(false)
    }
  }, [open])

  useLayoutEffect(() => {
    if (!open) return
    const rect = trigger.current?.getBoundingClientRect()
    if (!rect) return
    setAnchor({ position: "fixed", top: rect.bottom + 4, right: Math.max(8, window.innerWidth - rect.right) })
  }, [open])

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node
      if (!trigger.current?.contains(target) && !panel.current?.contains(target)) setOpen(false)
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return
      event.preventDefault()
      setOpen(false)
      trigger.current?.focus()
    }
    document.addEventListener("pointerdown", onPointerDown)
    document.addEventListener("keydown", onKeyDown)
    return () => {
      document.removeEventListener("pointerdown", onPointerDown)
      document.removeEventListener("keydown", onKeyDown)
    }
  }, [open])

  const run = (kind: "share" | "stop", work: () => Promise<unknown>) => {
    setBusy(kind)
    setError(null)
    work()
      .catch((failure: unknown) => setError(failure instanceof Error ? failure.message : "That did not work. Try again."))
      .finally(() => setBusy(null))
  }

  const copy = (url: string) => {
    const write = onCopy ?? ((text: string) => navigator.clipboard.writeText(text))
    write(url)
      .then(() => setCopied(true))
      .catch(() => setError("Could not copy. Select the link and copy it yourself."))
  }

  const open_ = onOpenLink ?? ((url: string) => void window.open(url, "_blank", "noopener"))

  return (
    <>
      <button
        ref={trigger}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        title={share ? "This part has a public link" : "Make a public link to this part"}
        onClick={() => setOpen((v) => !v)}
        className={clsx(
          "chrome flex h-[50px] items-center gap-2 border-l border-line px-3.5 transition-colors focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent",
          open ? "bg-raised text-ink" : "text-muted hover:text-ink"
        )}
      >
        <Icon name="share" className={share ? "text-accent" : undefined} />
        <span className="mono-label">{share ? "Shared" : "Share"}</span>
      </button>
      {open
        ? createPortal(
            <div
              ref={panel}
              role="dialog"
              aria-label="Share this part"
              style={anchor}
              className="z-30 flex w-[340px] flex-col overflow-hidden rounded-[6px] border border-panel-edge bg-ground shadow-[var(--shadow-panel)]"
            >
              <div className="flex h-8 shrink-0 items-center justify-between border-b border-line-soft px-3">
                <span className="font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase">
                  {share ? "Public link" : "Share"}
                </span>
                {share ? (
                  <span className="text-[12px] leading-4 text-muted">Shared {relativeTime(share.shared_at)}</span>
                ) : null}
              </div>
              <div className="flex flex-col gap-3 p-3">
                {share ? (
                  <>
                    <div className="flex gap-2">
                      <input
                        readOnly
                        aria-label="Link to this part"
                        value={share.url}
                        onFocus={(e) => e.currentTarget.select()}
                        className="mono-value h-7 min-w-0 flex-1 rounded-[3px] border border-line bg-raised px-2 text-ink focus:border-accent focus:outline-none"
                      />
                      <Button variant="accent" size="sm" onClick={() => copy(share.url)}>
                        {copied ? "Copied" : "Copy link"}
                      </Button>
                    </div>
                    {share.current ? null : (
                      <div className="flex items-center justify-between gap-2 rounded-[4px] bg-raised py-1.5 pr-1.5 pl-2.5">
                        <p className="text-[13px] leading-[19px] text-ink-soft">Changed since you shared it.</p>
                        <Button
                          variant="ink"
                          size="sm"
                          disabled={busy !== null}
                          onClick={() => run("share", () => sharePart(partId, values))}
                        >
                          {busy === "share" ? "Updating…" : "Update link"}
                        </Button>
                      </div>
                    )}
                    {confirming ? (
                      <div className="flex items-center justify-between gap-2 border-t border-line-soft pt-3">
                        <p className="text-[13px] leading-[19px] text-ink-soft">Turn the link off?</p>
                        <div className="flex shrink-0 gap-2">
                          <Button variant="ghost" size="sm" onClick={() => setConfirming(false)}>
                            Keep it
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            disabled={busy !== null}
                            onClick={() => run("stop", () => unsharePart(partId).then(() => setOpen(false)))}
                          >
                            {busy === "stop" ? "Stopping…" : "Stop sharing"}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between border-t border-line-soft pt-3">
                        <Button variant="outline" size="sm" icon="eye" onClick={() => open_(share.url)}>
                          Open page
                        </Button>
                        <Button variant="ghost" size="sm" icon="stop" onClick={() => setConfirming(true)}>
                          Stop sharing
                        </Button>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <p className="text-[13px] leading-[19px] text-ink-soft">
                      Anyone with the link can download this part or open a copy in nurb. The link includes its source and the project's supporting files.
                    </p>
                    <Button
                      variant="accent"
                      size="md"
                      disabled={busy !== null}
                      onClick={() => run("share", () => sharePart(partId, values))}
                    >
                      {busy === "share" ? "Making the link…" : "Create link"}
                    </Button>
                  </>
                )}
                {error ? <p className="text-[13px] leading-[19px] text-fail">{error}</p> : null}
              </div>
            </div>,
            document.body
          )
        : null}
    </>
  )
}
