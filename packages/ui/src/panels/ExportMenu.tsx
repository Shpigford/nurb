import { useEffect, useRef, useState } from "react"
import clsx from "clsx"
import Icon from "../Icon"
import Floating from "../layout/Floating"
import { rev } from "../format"

export type ExportFormat = "3mf" | "stl" | "step"

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
  /** Builds the file and hands it over. The menu shows a pending state until this settles. */
  export: (format: ExportFormat) => Promise<void>
  /** The slicer estimate for the export just handed out. */
  status?: ExportStatus | null
  revision?: number
  /** The build the prepared file came from; a newer one makes that file stale. */
  runId?: string | null
  /** The slicer on this computer, when the host can hand it a file. */
  openIn?: { name: string; open: () => Promise<void> } | null
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

const FORMAT_KEY = "nurb.exportFormat"

// Nearly every download is the same type, so the type is remembered rather than asked.
function rememberedFormat(): ExportFormat {
  try {
    const saved = localStorage.getItem(FORMAT_KEY)
    if (ROWS.some((row) => row.format === saved)) return saved as ExportFormat
  } catch {
    // Storage can be off; the default is the right answer then.
  }
  return "3mf"
}

// One click downloads the remembered type. The chevron beside it is the only way to
// another type, and picking one there downloads it and makes it the new default.
export default function ExportMenu({ partId, export: runExport, status, revision, runId, openIn }: ExportMenuProps) {
  const [format, setFormat] = useState<ExportFormat>(rememberedFormat)
  const [open, setOpen] = useState(false)
  const [preparing, setPreparing] = useState<ExportFormat | "slicer" | null>(null)
  const [error, setError] = useState<string | null>(null)
  const rootRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const popRef = useRef<HTMLDivElement>(null)
  const requestIdRef = useRef(0)
  const previousGeometryRef = useRef({ partId, revision, runId })

  // A download in flight describes one build; a rebuild makes its answer moot.
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

  const run = async (key: ExportFormat | "slicer", task: () => Promise<void>) => {
    const requestId = ++requestIdRef.current
    setPreparing(key)
    setError(null)
    try {
      await task()
      if (requestId === requestIdRef.current) setOpen(false)
    } catch (failure) {
      if (requestId !== requestIdRef.current) return
      // The menu is where the failure can be read in full, so it opens to say it.
      setError(failure instanceof Error ? failure.message : "The export did not finish.")
      setOpen(true)
    } finally {
      if (requestId === requestIdRef.current) setPreparing(null)
    }
  }

  const download = (chosen: ExportFormat) => run(chosen, () => runExport(chosen))

  const choose = (chosen: ExportFormat) => {
    setFormat(chosen)
    try {
      localStorage.setItem(FORMAT_KEY, chosen)
    } catch {
      // Remembered for this session only.
    }
    void download(chosen)
  }

  return (
    <div ref={rootRef} className="relative flex-1">
      <div className="flex h-9 w-full overflow-hidden rounded-control bg-accent text-white">
        <button
          type="button"
          disabled={preparing !== null}
          onClick={() => void download(format)}
          className="chrome btn-label inline-flex flex-1 items-center justify-center gap-2 px-3 transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-white disabled:hover:bg-transparent"
        >
          <Icon name="download" />
          {preparing ? "Preparing…" : `Download ${format.toUpperCase()}`}
        </button>
        <button
          ref={triggerRef}
          type="button"
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label="Choose file type"
          title="Choose file type"
          onClick={() => setOpen((v) => !v)}
          className="inline-flex w-9 shrink-0 items-center justify-center border-l border-white/25 transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-white"
        >
          <Icon name="chevron-down" />
        </button>
      </div>

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
            <span className="mono-label text-muted">File type</span>
            {revision != null ? <span className="mono-caption text-muted">{rev(revision)}</span> : null}
          </div>

          {error ? (
            <div className="border-b border-line-soft bg-fail-wash px-3 py-2 text-[11px] leading-4 text-ink-soft">
              <p className="mono-label text-fail">Download failed</p>
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
              const current = format === row.format
              return (
                <button
                  key={row.format}
                  type="button"
                  role="menuitem"
                  disabled={preparing !== null}
                  aria-current={current || undefined}
                  onClick={() => choose(row.format)}
                  className={clsx(
                    "flex w-full flex-col gap-0.5 px-3 py-2 text-left transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none disabled:opacity-60 disabled:hover:bg-transparent",
                    current && "bg-raised/60"
                  )}
                >
                  <span className="flex w-full items-center">
                    <span className="mono-value uppercase text-ink">{row.format}</span>
                    {current ? <Icon name="check" className="ml-1.5 text-accent-ink" /> : null}
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
            {openIn ? (
              <button
                type="button"
                role="menuitem"
                disabled={preparing !== null}
                onClick={() => void run("slicer", openIn.open)}
                className="mt-1 flex w-full flex-col gap-0.5 border-t border-line-soft px-3 pt-2.5 pb-2 text-left transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none disabled:opacity-60 disabled:hover:bg-transparent"
              >
                <span className="flex w-full items-center">
                  <span className="mono-value uppercase text-ink">Open in {openIn.name}</span>
                  {preparing === "slicer" ? (
                    <span className="mono-caption ml-auto flex items-center gap-1.5 text-muted">
                      <span className="size-1.5 rounded-full bg-accent" />
                      preparing
                    </span>
                  ) : null}
                </span>
                <span className="text-xs leading-4 text-ink-soft">Saves a 3MF and opens it there.</span>
              </button>
            ) : null}
          </div>


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
