import { useEffect, useRef, useState } from "react"
import clsx from "clsx"
import Icon from "../Icon"
import Floating from "../layout/Floating"
import { rev } from "../format"

export type ExportFormat = "3mf" | "stl" | "step"

export interface ExportResult {
  /** Where the finished file lives. The menu hands it to the user as a link. */
  url: string
  filename?: string
}

/** What the slicer said about the last export, once it has answered. */
export interface ExportStatus {
  state: "queued" | "succeeded" | "failed"
  grams?: number | null
  seconds?: number | null
  error?: string | null
}

export interface ExportMenuProps {
  /** Stable identity of the part being exported. */
  partId: string
  /** Builds the file. The menu shows a pending state until this settles. */
  export: (format: ExportFormat) => Promise<ExportResult>
  /** The slicer estimate for the export just handed out. */
  status?: ExportStatus | null
  revision?: number
  /** The build the prepared file came from; a newer one makes that file stale. */
  runId?: string | null
}

const ROWS: { format: ExportFormat; caption: string; recommended?: boolean }[] = [
  { format: "3mf", caption: "Print-ready, keeps units and orientation.", recommended: true },
  { format: "stl", caption: "Print-ready mesh. Works in every slicer." },
  { format: "step", caption: "Solid model, for another CAD tool." },
]

function estimateLine(status: ExportStatus): string {
  if (status.state === "queued") return "Estimate · slicing…"
  if (status.state === "failed") return `Estimate · ${status.error ?? "unavailable"}`
  const parts = [
    status.grams ? `${Math.round(status.grams)} g` : null,
    status.seconds ? `${(status.seconds / 3600).toFixed(1)} hr` : null,
  ].filter(Boolean)
  return `Estimate · ${parts.length ? parts.join(" · ") : "unavailable"}`
}

// The DOWNLOAD button opens a popover above it: one row per format, the file
// built on demand. The finished file arrives as a link rather than an automatic
// save, because the file belongs to the user's click, not to the menu's.
export default function ExportMenu({ partId, export: runExport, status, revision, runId }: ExportMenuProps) {
  const [open, setOpen] = useState(false)
  const [preparing, setPreparing] = useState<ExportFormat | null>(null)
  const [ready, setReady] = useState<{ format: ExportFormat; result: ExportResult } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const rootRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const popRef = useRef<HTMLDivElement>(null)
  const requestIdRef = useRef(0)
  const previousGeometryRef = useRef({ partId, revision, runId })

  // A prepared file describes one build. The menu stays open through a rebuild,
  // because the user opened it; only the file it is offering goes.
  useEffect(() => {
    const previous = previousGeometryRef.current
    if (
      previous.partId === partId &&
      Object.is(previous.revision, revision) &&
      Object.is(previous.runId, runId)
    )
      return
    previousGeometryRef.current = { partId, revision, runId }
    requestIdRef.current += 1
    setPreparing(null)
    setReady(null)
    setError(null)
  }, [partId, revision, runId])

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: PointerEvent) => {
      // The popover is drawn on the body, so it is no longer inside the trigger's box.
      const target = event.target as Node
      if (rootRef.current?.contains(target) || popRef.current?.contains(target)) return
      setOpen(false)
    }
    // Arrows walk the formats, the way any open menu does; without them the only way
    // through the list is Tab, which walks out of the popover as readily as down it.
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false)
        // Escape must hand the keyboard back to the button that opened the menu,
        // or focus falls to the document and the only way back is Tab from the top.
        triggerRef.current?.focus()
        return
      }
      if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return
      const items = Array.from(menuRef.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]') ?? [])
      if (items.length === 0) return
      event.preventDefault()
      const step = event.key === "ArrowDown" ? 1 : -1
      const at = items.indexOf(document.activeElement as HTMLButtonElement)
      const next = at === -1 ? (step === 1 ? 0 : items.length - 1) : (at + step + items.length) % items.length
      items[next].focus()
    }
    document.addEventListener("pointerdown", onPointerDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("pointerdown", onPointerDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [open])

  const download = async (format: ExportFormat) => {
    const requestId = ++requestIdRef.current
    setPreparing(format)
    setError(null)
    setReady(null)
    try {
      const result = await runExport(format)
      if (requestId !== requestIdRef.current) return
      setReady({ format, result })
    } catch (failure) {
      if (requestId !== requestIdRef.current) return
      setError(failure instanceof Error ? failure.message : "The export did not finish.")
    } finally {
      if (requestId === requestIdRef.current) setPreparing(null)
    }
  }

  return (
    <div ref={rootRef} className="relative flex-1">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="chrome btn-label inline-flex h-9 w-full items-center justify-center gap-2 rounded-control bg-accent px-3 text-white transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <Icon name="download" />
        {preparing ? "Preparing…" : "Download"}
        <Icon name="chevron-down" />
      </button>

      {/* Portalled: the rail's footer scroller clips, and the first row was cut at its edge. */}
      {open ? (
        <Floating
          ref={popRef}
          anchor={triggerRef}
          width={254}
          align="left"
          gap={8}
          className="z-30 overflow-hidden rounded-content border border-panel-edge bg-ground shadow-[var(--shadow-panel)]"
        >
          <div className="chrome flex h-[30px] items-center justify-between border-b border-line-soft px-3">
            <span className="mono-label text-muted">Download</span>
            {revision != null ? <span className="mono-caption text-muted">{rev(revision)}</span> : null}
          </div>

          {error ? (
            <div className="border-b border-line-soft bg-fail-wash px-3 py-2 text-[11px] leading-4 text-ink-soft">
              <p className="mono-label text-fail">Export failed</p>
              <p className="mt-0.5">{error}</p>
            </div>
          ) : null}

          <div
            ref={menuRef}
            role="menu"
            aria-label="Download format"
            className="flex flex-col py-1"
          >
            {ROWS.map((row) => {
              const busy = preparing === row.format
              return (
                <button
                  key={row.format}
                  type="button"
                  role="menuitem"
                  disabled={preparing !== null}
                  onClick={() => void download(row.format)}
                  className={clsx(
                    "flex w-full flex-col gap-0.5 px-3 py-2 text-left transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none disabled:opacity-60 disabled:hover:bg-transparent",
                    row.recommended && "bg-raised/60"
                  )}
                >
                  <span className="flex w-full items-center">
                    <span className="mono-value uppercase text-ink">{row.format}</span>
                    {busy ? (
                      <span className="mono-caption ml-auto flex items-center gap-1.5 text-muted">
                        <span className="size-1.5 rounded-full bg-accent" />
                        preparing
                      </span>
                    ) : row.recommended ? (
                      <span className="mono-caption ml-auto text-accent-ink">Recommended</span>
                    ) : null}
                  </span>
                  <span className="text-xs leading-4 text-ink-soft">{row.caption}</span>
                </button>
              )
            })}
          </div>

          {ready ? (
            <a
              href={ready.result.url}
              download={ready.result.filename}
              onClick={() => setOpen(false)}
              className="chrome btn-label flex items-center gap-2 border-t border-line-soft bg-ink px-3 py-2 text-white transition-colors hover:bg-ink-soft"
            >
              <Icon name="download" />
              Save {ready.result.filename ?? `the ${ready.format.toUpperCase()}`}
            </a>
          ) : null}

          {status ? (
            <div className="chrome border-t border-line-soft bg-raised px-3 py-2">
              <span className="mono-caption text-muted">{estimateLine(status)}</span>
            </div>
          ) : null}
        </Floating>
      ) : null}
    </div>
  )
}
