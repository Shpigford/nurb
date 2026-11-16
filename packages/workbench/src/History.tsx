import clsx from "clsx"
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type Ref } from "react"
import { createPortal } from "react-dom"
import { Button, Icon, relativeTime, rev, useIsDark } from "@nurb/ui"
import {
  absolute,
  fetchRevision,
  fetchRevisions,
  restoreRevision,
  type Part,
  type RevisionEntry,
  type RevisionView,
} from "./api"

const STATUS_WORD: Record<RevisionEntry["status"], string> = {
  ok: "Built",
  error: "Did not build",
  unbuilt: "Never built",
}

const STATUS_DOT: Record<RevisionEntry["status"], string> = {
  ok: "bg-pass",
  error: "bg-fail",
  unbuilt: "bg-line",
}

// "Applied width from the sliders" says what changed; a revision an agent wrote says
// nothing, and the number and the time are then the whole row.
function noteOf(entry: { note: string | null; current?: boolean }): string | null {
  return entry.note?.trim() || null
}

/**
 * Looking back at one earlier revision of a part, and bringing it back.
 *
 * One operation number covers opening, restoring, going back and a change of part:
 * each takes a new one, so an answer that arrives for an older one is dropped instead
 * of landing on whatever is on screen now. A new revision of the part ends the look
 * back, except the one a restore in flight is writing, which ends it when it answers.
 */
export function useRevisionHistory(
  part: Pick<Part, "id" | "name" | "revision_id"> | null,
  on: {
    /** The stage is about to show an older shape: stop anything acting on the current one. */
    enter: () => void
    /** The restore landed as a new revision. */
    restored: (from: number, to: number) => void
    /** A revision did not open. */
    failed: (message: string) => void
  }
) {
  const [viewing, setViewing] = useState<RevisionView | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [restoring, setRestoring] = useState(false)
  const op = useRef(0)
  const inFlight = useRef(false)
  const banner = useRef<HTMLDivElement>(null)
  const handlers = useRef(on)
  handlers.current = on

  const back = useCallback(() => {
    op.current += 1
    inFlight.current = false
    setViewing(null)
    setError(null)
    setRestoring(false)
  }, [])

  // Another part is another history, and a rename that writes no revision still moves
  // the URLs the old run is served at.
  useEffect(() => back(), [part?.id, part?.name, back])
  useEffect(() => {
    if (!inFlight.current) back()
  }, [part?.revision_id, back])

  const open = useCallback(
    async (entry: RevisionEntry) => {
      // A restore in flight decides what comes next; Back is the way out of it.
      if (!part || inFlight.current) return
      if (entry.current) return back()
      handlers.current.enter()
      const mine = ++op.current
      setError(null)
      try {
        const view = await fetchRevision(part.id, entry.id)
        if (mine === op.current) setViewing(view)
      } catch (failure) {
        if (mine === op.current) handlers.current.failed(failure instanceof Error ? failure.message : "That revision did not open.")
      }
    },
    [part?.id, back]
  )

  const restore = useCallback(async () => {
    if (!part || !viewing || inFlight.current) return
    const mine = ++op.current
    inFlight.current = true
    setRestoring(true)
    setError(null)
    try {
      const result = await restoreRevision(part.id, viewing.id, part.revision_id)
      if (mine !== op.current) return
      back()
      handlers.current.restored(viewing.revision, result.revision)
    } catch (failure) {
      if (mine !== op.current) return
      inFlight.current = false
      setRestoring(false)
      setError(failure instanceof Error ? failure.message : "The restore did not finish.")
    }
  }, [part?.id, part?.revision_id, viewing, back])

  return { viewing, error, restoring, banner, open, back, restore }
}

interface Group {
  /** Newest first, as the list comes. */
  steps: RevisionEntry[]
  /** The step the row stands for: where the message ended up, the newest one that built if any did. */
  shown: RevisionEntry
}

/** Consecutive revisions that share a group, in list order. */
export function groupsOf(rows: RevisionEntry[]): Group[] {
  const groups: Group[] = []
  for (const row of rows) {
    const last = groups[groups.length - 1]
    if (last && last.steps[0].group === row.group) last.steps.push(row)
    else groups.push({ steps: [row], shown: row })
  }
  for (const group of groups) group.shown = group.steps.find((step) => step.status === "ok") ?? group.steps[0]
  return groups
}

function Dot({ status }: { status: RevisionEntry["status"] }) {
  return <span className={clsx("size-1.5 shrink-0 rounded-full", STATUS_DOT[status])} />
}

/** One message's worth of revisions: the message, where it ended up, and its steps behind a chevron. */
function HistoryGroup({
  group,
  viewing,
  dark,
  expanded,
  onToggle,
  onView,
}: {
  group: Group
  viewing: RevisionView | null
  dark: boolean
  expanded: boolean
  onToggle: () => void
  onView: (entry: RevisionEntry) => void
}) {
  const { steps, shown } = group
  const isOn = (row: RevisionEntry) => (viewing ? viewing.id === row.id : row.current)
  const on = steps.some(isOn)
  const current = steps.some((step) => step.current)
  const title = steps[0].prompt ?? null
  const note = noteOf(shown)
  const url = shown.thumbnail_url ? absolute(shown.thumbnail_url) : null
  return (
    <div className={clsx(on && !expanded ? "bg-accent-wash" : null)}>
      <div className="flex items-center">
        <button
          type="button"
          aria-current={on ? "true" : undefined}
          onClick={() => onView(shown)}
          className={clsx(
            "flex min-w-0 flex-1 items-center gap-2.5 py-1.5 pl-2 text-left transition-colors focus-visible:bg-raised focus-visible:outline-none",
            on && !expanded ? null : "hover:bg-raised"
          )}
        >
          <span className="flex h-[36px] w-12 shrink-0 items-center justify-center overflow-hidden rounded-[3px] bg-raised">
            {url ? <img src={dark ? `${url}&theme=dark` : url} alt="" loading="lazy" className="size-full object-contain p-0.5" /> : null}
          </span>
          <span className="flex min-w-0 flex-1 flex-col gap-0.5">
            <span className="flex items-center gap-2">
              {title ? (
                <span className="truncate text-[13px] leading-[18px] font-medium text-ink" title={title}>
                  {title}
                </span>
              ) : (
                <span className="mono-label text-ink">{rev(shown.revision)}</span>
              )}
              <span className="mono-caption ml-auto shrink-0 text-muted">{relativeTime(shown.created_at)}</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Dot status={shown.status} />
              {title || steps.length > 1 ? (
                <span className="mono-caption truncate text-ink-soft">
                  {title ? rev(shown.revision) : null}
                  {title && steps.length > 1 ? " · " : null}
                  {steps.length > 1 ? `${steps.length} edits` : null}
                </span>
              ) : (
                <span className="truncate text-[12px] leading-4 text-ink-soft">{note ?? STATUS_WORD[shown.status]}</span>
              )}
              {current ? <span className="mono-caption text-accent-ink">CURRENT</span> : null}
            </span>
          </span>
        </button>
        {steps.length > 1 ? (
          <button
            type="button"
            aria-expanded={expanded}
            aria-label={expanded ? "Hide each edit" : `Show each of the ${steps.length} edits`}
            onClick={onToggle}
            className="flex h-[48px] w-[30px] shrink-0 items-center justify-center text-muted transition-colors hover:text-ink focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
          >
            <span className={clsx("transition-transform", expanded ? null : "-rotate-90")}>
              <Icon name="chevron-down" />
            </span>
          </button>
        ) : (
          <span className="w-[30px] shrink-0" />
        )}
      </div>
      {expanded ? (
        <ul className="pr-[30px] pb-1 pl-[66px]">
          {steps.map((step) => (
            <li key={step.id} className="border-l border-line">
              <button
                type="button"
                aria-current={isOn(step) ? "true" : undefined}
                onClick={() => onView(step)}
                className={clsx(
                  "flex h-6 w-full items-center gap-1.5 pl-2.5 text-left transition-colors focus-visible:bg-raised focus-visible:outline-none",
                  isOn(step) ? "bg-accent-wash" : "hover:bg-raised"
                )}
              >
                <Dot status={step.status} />
                <span className="mono-caption w-11 shrink-0 text-ink">{rev(step.revision)}</span>
                <span className="truncate text-[12px] leading-4 text-ink-soft">{noteOf(step) ?? STATUS_WORD[step.status]}</span>
                <span className="mono-caption ml-auto shrink-0 text-muted">{relativeTime(step.created_at)}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}

/**
 * The header cell that opens the part's history. The list is read fresh on every
 * open, because any build since the last one may have changed what each row says.
 */
export function HistoryMenu({
  partId,
  revision,
  viewing,
  onView,
}: {
  partId: string
  /** The part's current revision number, which the trigger names. */
  revision: number
  /** The revision on stage instead of the current one, if any. */
  viewing: RevisionView | null
  onView: (entry: RevisionEntry) => void
}) {
  const [open, setOpen] = useState(false)
  const [rows, setRows] = useState<RevisionEntry[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [anchor, setAnchor] = useState<CSSProperties>()
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const trigger = useRef<HTMLButtonElement>(null)
  const panel = useRef<HTMLDivElement>(null)
  const dark = useIsDark()

  useEffect(() => {
    if (!open) return
    let live = true
    setError(null)
    fetchRevisions(partId)
      .then((answer) => live && setRows(answer.revisions))
      .catch((failure: unknown) => live && setError(failure instanceof Error ? failure.message : "The history did not load."))
    return () => {
      live = false
    }
  }, [open, partId])

  // Another part's history is another list.
  useEffect(() => {
    setOpen(false)
    setRows(null)
    setExpanded(new Set())
  }, [partId])

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
      // The stage's own Escape leaves the old revision; this one only closes the list.
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

  const label = viewing ? `Viewing ${rev(viewing.revision).toLowerCase()}` : "History"
  return (
    <>
      <button
        ref={trigger}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        title={`Earlier versions of this part. It is on ${rev(revision).toLowerCase()} now.`}
        onClick={() => setOpen((v) => !v)}
        className={clsx(
          "chrome flex h-[50px] items-center gap-2 border-l border-line px-3.5 transition-colors focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent",
          viewing ? "bg-accent-wash text-accent-ink" : open ? "bg-raised text-ink" : "text-muted hover:text-ink"
        )}
      >
        <span className="mono-label">{label}</span>
        <Icon name="chevron-down" />
      </button>
      {open
        ? createPortal(
            <div
              ref={panel}
              role="dialog"
              aria-label="Part history"
              style={anchor}
              className="z-30 flex max-h-[min(480px,70vh)] w-[320px] flex-col overflow-hidden rounded-[6px] border border-panel-edge bg-ground shadow-[var(--shadow-panel)]"
            >
              <div className="flex h-8 shrink-0 items-center border-b border-line-soft px-3 font-mono text-[9.5px] leading-3 font-medium tracking-[0.12em] text-faint uppercase">
                History
              </div>
              <div className="min-h-0 flex-1 overflow-y-auto py-1">
                {error ? <p className="mono-caption px-3 py-2 text-fail">{error}</p> : null}
                {!rows && !error ? <p className="mono-caption px-3 py-2 text-muted">Reading the history…</p> : null}
                {rows
                  ? groupsOf(rows).map((group) => (
                      <HistoryGroup
                        key={group.steps[group.steps.length - 1].id}
                        group={group}
                        viewing={viewing}
                        dark={dark}
                        expanded={expanded.has(group.shown.group)}
                        onToggle={() =>
                          setExpanded((was) => {
                            const next = new Set(was)
                            if (!next.delete(group.shown.group)) next.add(group.shown.group)
                            return next
                          })
                        }
                        onView={(entry) => {
                          setOpen(false)
                          onView(entry)
                        }}
                      />
                    ))
                  : null}
              </div>
            </div>,
            document.body
          )
        : null}
    </>
  )
}

/** The pill over the stage while an earlier revision is on it: which one, and the two ways out. */
export function RevisionBanner({
  ref,
  view,
  current,
  restoring,
  error,
  onBack,
  onRestore,
}: {
  ref?: Ref<HTMLDivElement>
  view: RevisionView
  current: number
  restoring: boolean
  error: string | null
  onBack: () => void
  onRestore: () => void
}) {
  const when = relativeTime(view.created_at)
  return (
    <div
      ref={ref}
      role="status"
      aria-label="Earlier revision on stage"
      className="panel chrome absolute inset-x-0 top-4 z-20 mx-auto flex w-fit max-w-[calc(100%-2rem)] flex-col gap-1 rounded-[6px] py-1.5 pr-1.5 pl-3"
    >
      <div className="flex items-center gap-3">
        <span className="size-1.5 shrink-0 rounded-full bg-accent" />
        <span className="flex min-w-[160px] flex-col">
          <span className="mono-label whitespace-nowrap text-ink">
            Viewing {rev(view.revision).toLowerCase()}
            {when ? ` · ${when}` : ""}
          </span>
          <span className="mono-caption truncate text-muted">
            {noteOf(view) ?? `The part is on ${rev(current).toLowerCase()} now`}
          </span>
        </span>
        <span className="ml-2 flex shrink-0 gap-1.5">
          <Button variant="outline" size="sm" onClick={onBack}>
            Back to {rev(current).toLowerCase()}
          </Button>
          <Button variant="accent" size="sm" disabled={restoring} onClick={onRestore}>
            {restoring ? "Restoring…" : `Restore ${rev(view.revision).toLowerCase()}`}
          </Button>
        </span>
      </div>
      {error ? <p className="mono-caption pb-0.5 text-fail">{error}</p> : null}
    </div>
  )
}

function shown(value: unknown, kind: string | null): string {
  if (typeof value === "boolean") return value ? "On" : "Off"
  if (typeof value === "number") return kind === "int" ? String(Math.round(value)) : String(Math.round(value * 1000) / 1000)
  return value == null ? "-" : String(value)
}

/** The rail while an earlier revision is on stage: what it was built at, and nothing to drag. */
export function RevisionParams({ view, current }: { view: RevisionView; current: number }) {
  const params = view.params
  return (
    <div className="flex flex-col">
      <div className="flex items-start gap-2 bg-accent-wash px-4 py-2.5">
        <span className="flex flex-col gap-1">
          <span className="mono-label text-accent-ink">{rev(view.revision)} · read only</span>
          <span className="text-chat text-ink-soft">
            These are the values it was built at. Restore it to change them, or go back to {rev(current).toLowerCase()}.
          </span>
        </span>
      </div>
      {params.length === 0 ? (
        <p className="mono-caption px-4 py-3 text-muted">
          {view.status === "ok" ? "This revision has no parameters." : "Nothing built, so there are no values to show."}
        </p>
      ) : (
        <ul className="flex flex-col py-2">
          {params.map((param) => {
            const moved = param.value !== param.default
            return (
              <li key={param.name} className="flex h-8 items-center gap-2 px-4">
                <span className="truncate text-[13px] text-ink-soft">{param.name.replace(/_/g, " ")}</span>
                <span className="ml-auto mono-value text-ink">{shown(param.value, param.kind)}</span>
                {moved ? (
                  <span className="mono-caption text-muted" title={`The saved default was ${shown(param.default, param.kind)}`}>
                    dragged
                  </span>
                ) : null}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
