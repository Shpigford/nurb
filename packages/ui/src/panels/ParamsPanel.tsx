import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type CSSProperties,
  type KeyboardEvent,
  type PointerEvent,
} from "react"
import clsx from "clsx"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import Icon from "../Icon"
import LoadingButton from "../motion/LoadingButton"
import { duration, ease } from "../motion/tokens"
import { DetentMarks, useSliderDetents } from "../motion/useSliderDetents"
import { cue } from "../sound"
import type { BuildStats, Param, Params } from "../types"
import { adjustable, decimals, detentsFor, dirtyValues, rangeFor, tidy, type Measurement } from "./paramsState"

// motion wants a tuple; ease.out is a plain number[].
const OUT = ease.out as [number, number, number, number]

// No part declares a unit. Every dimension the engine reports is millimetres.
const UNIT = "mm"

// Horizontal travel that buys one step when scrubbing the number field.
const SCRUB_PX = 4
// Quiet enough that a fast scrub ticks, not buzzes.
const TICK_MS = 60
// How far past the end of the track a drag has to travel before it counts as a
// push rather than a thumb parked on the last stop.
const OVERSHOOT_PX = 6

export interface ParamsPanelProps {
  params: Param[]
  /** Project measurements. Each one inside a float slider's range becomes a stop on it. */
  measurements?: Measurement[]
  /** Nozzle width in mm, which sets where the whole-line stops fall on a wall. */
  nozzle?: number
  /** Session values keyed by parameter name; anything missing reads its default. */
  values: Params
  onChange: (values: Params) => void
  /** The edited values only, keyed by name. An untouched panel never gets here. */
  onApply: (values: Params) => void
  /** A rebuild is in flight for these values. */
  building?: boolean
  /** Apply is writing the values into the part's defaults. */
  applying?: boolean
  /** The last build's numbers, for the footer line. */
  stats?: BuildStats | null
  /** A build that failed at these values; the panel keeps showing the controls. */
  error?: string | null
  /** What Apply said, once it landed. */
  note?: string | null
}

function formatValue(value: number, int: boolean, step: number): string {
  return int ? String(Math.round(value)) : String(tidy(value, step))
}

// A python identifier as a rail label: shelf_width -> shelf width.
function label(name: string) {
  return name.replace(/_/g, " ")
}

function SectionRule({ children }: { children: string }) {
  return (
    <div className="chrome flex items-center gap-2 px-4 pt-[11px] pb-2">
      <span className="mono-caption text-faint [letter-spacing:0.12em]">{children}</span>
      <span className="h-px flex-1 bg-line-soft" />
    </div>
  )
}

// The dirty mark doubles as the way back: one click returns the declared default.
function ResetDot({ param, onReset }: { param: Param; onReset: () => void }) {
  return (
    <button
      type="button"
      title={`Default ${param.default}`}
      onClick={onReset}
      aria-label={`Reset ${param.name} to default`}
      className="size-1.5 shrink-0 rounded-full bg-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    />
  )
}

// Label and value on one baseline, the slider beneath. The value is still a
// field: click it to type an exact number, or drag it sideways to scrub.
function NumberRow({
  id,
  param,
  value,
  dirty,
  measurements,
  nozzle,
  onValue,
}: {
  id: string
  param: Param
  value: number
  dirty: boolean
  measurements?: Measurement[]
  nozzle?: number
  onValue: (value: number) => void
}) {
  const int = param.kind === "int"
  const range = rangeFor(param, int)
  const lo = Math.min(range.lo, value)
  const hi = Math.max(range.hi, value)
  // A typed 9.25 must stay on the grid too, or the thumb parks beside the fill.
  const step = int ? 1 : Math.min(range.step, 10 ** -decimals(value))
  const [text, setText] = useState(() => formatValue(value, int, step))
  const editing = useRef(false)
  if (!editing.current) {
    const shown = formatValue(value, int, step)
    if (shown !== text) setText(shown)
  }

  const reduced = useReducedMotion()
  const detents = useMemo(() => detentsFor(param, measurements, nozzle), [param, measurements, nozzle])
  const slider = useSliderDetents({
    value,
    onValueChange: onValue,
    min: lo,
    max: hi,
    step,
    detents,
    pull: (hi - lo) * 0.045,
  })

  // The end of the track, said once. A native range clamps in silence, so without
  // this the thumb simply stops and never says why it stopped there.
  const [limit, setLimit] = useState<{ end: "min" | "max" } | null>(null)
  const [bump, setBump] = useState(0)
  useEffect(() => {
    if (!limit) return
    setBump(limit.end === "max" ? 3 : -3)
    const spring = setTimeout(() => setBump(0), reduced ? 0 : duration.tick * 1000)
    const hide = setTimeout(() => setLimit(null), 1200)
    return () => {
      clearTimeout(spring)
      clearTimeout(hide)
    }
  }, [limit, reduced])
  // A fresh object every time, so pushing at the end twice replays the nudge.
  const flash = (end: "min" | "max") => setLimit({ end })

  const onSliderChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (int) {
      onValue(Math.round(Number(event.target.value)))
      return
    }
    slider.onChange(event)
  }

  // A range at its bound emits no change event, so a drag that keeps pushing is
  // silent to onChange. The pointer's own position is what says the push happened.
  const dragging = useRef(false)
  const outside = useRef(false)

  const onTrackPointerDown = (event: PointerEvent<HTMLInputElement>) => {
    if (event.button !== 0) return
    dragging.current = true
    outside.current = false
  }

  const onTrackPointerMove = (event: PointerEvent<HTMLInputElement>) => {
    if (!dragging.current) return
    const rect = event.currentTarget.getBoundingClientRect()
    const past =
      event.clientX > rect.right + OVERSHOOT_PX ? "max" : event.clientX < rect.left - OVERSHOOT_PX ? "min" : null
    if (!past) {
      // Back over the track. The next push out earns its own line.
      outside.current = false
      return
    }
    if (outside.current) return
    if (past === "max" && value >= hi) {
      outside.current = true
      flash("max")
    } else if (past === "min" && value <= lo) {
      outside.current = true
      flash("min")
    }
  }

  const endTrackDrag = () => {
    dragging.current = false
    outside.current = false
  }

  const onSliderKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    const up = event.key === "ArrowRight" || event.key === "ArrowUp" || event.key === "PageUp"
    const down = event.key === "ArrowLeft" || event.key === "ArrowDown" || event.key === "PageDown"
    if (up && value >= hi) flash("max")
    else if (down && value <= lo) flash("min")
    slider.onKeyDown(event)
  }

  const commitText = () => {
    editing.current = false
    const parsed = Number(text)
    if (text.trim() === "" || !Number.isFinite(parsed)) {
      setText(formatValue(value, int, step))
      return
    }
    onValue(int ? Math.round(parsed) : parsed)
  }

  // The grid is passed in, never read at the time of the move: a gesture that
  // crosses a decimal boundary would otherwise finish on a step ten times the one
  // it started with, and jump.
  const stepFrom = (from: number, steps: number, grid: number) => {
    const next = int ? Math.round(from + steps * grid) : tidy(from + steps * grid, grid)
    if (next !== value) onValue(next)
    return next
  }

  // Scrubbing the field. Nothing is captured until the pointer actually travels,
  // so a plain click still places the caret and typing works as it always did.
  const drag = useRef<{ x: number; from: number; step: number; scrubbing: boolean } | null>(null)
  const ticked = useRef(0)

  const onFieldPointerDown = (event: PointerEvent<HTMLInputElement>) => {
    if (event.button !== 0) return
    drag.current = { x: event.clientX, from: value, step, scrubbing: false }
  }

  const onFieldPointerMove = (event: PointerEvent<HTMLInputElement>) => {
    const held = drag.current
    if (!held) return
    const dx = event.clientX - held.x
    if (!held.scrubbing) {
      if (Math.abs(dx) < SCRUB_PX) return
      held.scrubbing = true
      event.currentTarget.setPointerCapture?.(event.pointerId)
    }
    const before = value
    const next = stepFrom(held.from, Math.round(dx / SCRUB_PX), held.step)
    if (next === before) return
    const now = Date.now()
    if (now - ticked.current >= TICK_MS) {
      ticked.current = now
      cue("tick")
    }
  }

  const onFieldPointerUp = (event: PointerEvent<HTMLInputElement>) => {
    const held = drag.current
    drag.current = null
    if (held?.scrubbing && event.currentTarget.hasPointerCapture?.(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
  }

  return (
    <div className="flex flex-col gap-1 px-4">
      <div className="flex items-baseline justify-between gap-2">
        <div className="flex min-w-0 items-center gap-1.5">
          <label
            htmlFor={id}
            title={param.description}
            className={clsx("mono-caption min-w-0 truncate", dirty ? "font-medium text-ink" : "text-muted")}
          >
            {label(param.name)}
          </label>
          {dirty ? <ResetDot param={param} onReset={() => onValue(param.default as number)} /> : null}
        </div>
        <div className="flex shrink-0 items-baseline gap-1.5">
          {slider.activeLabel ? <span className="mono-caption text-faint">{slider.activeLabel}</span> : null}
          <input
            value={text}
            onChange={(e) => {
              editing.current = true
              setText(e.target.value)
            }}
            onBlur={commitText}
            onPointerDown={onFieldPointerDown}
            onPointerMove={onFieldPointerMove}
            onPointerUp={onFieldPointerUp}
            onPointerCancel={onFieldPointerUp}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitText()
              if (e.key === "Escape") {
                // Escape mid-scrub puts back the number the drag started from.
                const held = drag.current
                drag.current = null
                editing.current = false
                if (held?.scrubbing) onValue(held.from)
                else setText(formatValue(value, int, step))
              }
              // Up and down step the value. Left and right stay with the caret,
              // because this is still a field someone types into.
              if (e.key === "ArrowUp" || e.key === "ArrowDown") {
                e.preventDefault()
                stepFrom(value, (e.key === "ArrowUp" ? 1 : -1) * (e.shiftKey ? 10 : 1), step)
              }
            }}
            inputMode={int ? "numeric" : "decimal"}
            aria-label={`${param.name} value`}
            className={clsx(
              "mono-value w-16 cursor-ew-resize rounded-control border-0 bg-transparent p-0 text-right focus:bg-raised focus:outline-1 focus:outline-accent",
              dirty ? "text-accent-ink" : "text-ink"
            )}
          />
        </div>
      </div>
      <motion.div
        className="relative"
        animate={{ x: bump }}
        transition={{ duration: reduced ? 0 : duration.tick, ease: OUT }}
      >
        <input
          id={id}
          type="range"
          min={lo}
          max={hi}
          step={step}
          value={value}
          onChange={onSliderChange}
          onKeyDown={onSliderKeyDown}
          onPointerDown={onTrackPointerDown}
          onPointerMove={onTrackPointerMove}
          onPointerUp={endTrackDrag}
          onPointerCancel={endTrackDrag}
          onLostPointerCapture={endTrackDrag}
          aria-label={label(param.name)}
          aria-valuetext={`${value}`}
          className="param-slider w-full"
          style={{ "--pct": hi === lo ? 0 : (value - lo) / (hi - lo) } as CSSProperties}
        />
        <DetentMarks detents={slider.detents} min={lo} max={hi} activeDetent={slider.activeDetent} />
      </motion.div>
      <AnimatePresence>
        {limit ? (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduced ? 0 : duration.settle, ease: OUT }}
            className="mono-caption text-accent-ink"
          >
            {limit.end === "max"
              ? `${formatValue(hi, int, step)} ${UNIT} · widest this will go`
              : `${formatValue(lo, int, step)} ${UNIT} · thinnest this will go`}
          </motion.p>
        ) : null}
      </AnimatePresence>
    </div>
  )
}

function BoolRow({
  id,
  param,
  value,
  dirty,
  onValue,
}: {
  id: string
  param: Param
  value: boolean
  dirty: boolean
  onValue: (value: boolean) => void
}) {
  return (
    <div className="flex items-center gap-2 px-4 py-1">
      <label
        htmlFor={id}
        title={param.description}
        className={clsx("mono-caption min-w-0 truncate", dirty ? "font-medium text-ink" : "text-muted")}
      >
        {label(param.name)}
      </label>
      {dirty ? <ResetDot param={param} onReset={() => onValue(param.default as boolean)} /> : null}
      <span className="flex-1" />
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={value}
        aria-label={label(param.name)}
        onClick={() => onValue(!value)}
        className={clsx(
          "relative h-4 w-7 shrink-0 rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
          value ? "bg-accent" : "bg-line"
        )}
      >
        <span
          className={clsx(
            "absolute top-0.5 size-3 rounded-full bg-ground transition-[left]",
            value ? "left-3.5" : "left-0.5"
          )}
        />
      </button>
    </div>
  )
}

// Live parameter controls. Every change hands the host the whole value map, so
// the host owns the rebuild; Apply hands it only the values that moved, which
// is what gets written into the part's keyword defaults.
export default function ParamsPanel({
  params,
  measurements,
  nozzle,
  values,
  onChange,
  onApply,
  building,
  applying,
  stats,
  error,
  note,
}: ParamsPanelProps) {
  const rows = useMemo(() => params.filter(adjustable), [params])
  const pinned = useMemo(() => params.filter((p) => !adjustable(p)), [params])
  const bools = rows.filter((p) => p.kind === "bool")
  const numbers = rows.filter((p) => p.kind !== "bool")
  const dirty = useMemo(() => dirtyValues(params, values), [params, values])
  const dirtyCount = Object.keys(dirty).length
  // Two panels on one page (a compare view) must not share control ids.
  const prefix = useId()

  const setValue = (name: string, value: number | boolean) => {
    onChange({ ...values, [name]: value })
  }

  if (rows.length === 0) return null

  return (
    <div className="flex min-h-0 flex-1 flex-col" role="group" aria-label="Part parameters">
      {error ? (
        <div className="border-b border-line-soft bg-fail-wash px-4 py-2.5">
          <p className="mono-label flex items-center gap-2 text-fail">
            <Icon name="warning" />
            Build failed at these values
          </p>
          <p className="mt-1 text-xs leading-4 text-ink-soft">{error}</p>
          <p className="mt-0.5 text-xs leading-4 text-muted">Showing the last part that built.</p>
        </div>
      ) : null}
      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto pb-3">
        {pinned.length > 0 ? (
          <>
            <SectionRule>Pinned by spec</SectionRule>
            <dl className="flex flex-col">
              {pinned.map((param) => (
                <div key={param.name} className="flex items-center gap-[9px] px-4 py-1.5" title={param.description}>
                  <span className="text-muted">
                    <Icon name="lock" />
                  </span>
                  <dt className="mono-id min-w-0 flex-1 truncate uppercase text-muted [letter-spacing:0.06em]">
                    {label(param.name)}
                  </dt>
                  <dd className="mono-value text-muted">{String(values[param.name] ?? param.default)}</dd>
                </div>
              ))}
            </dl>
          </>
        ) : null}

        <SectionRule>Yours to drag</SectionRule>
        <div className="flex flex-col gap-3">
          {bools.map((param) => (
            <BoolRow
              key={param.name}
              id={`${prefix}${param.name}`}
              param={param}
              value={(values[param.name] ?? param.default) as boolean}
              dirty={param.name in dirty}
              onValue={(v) => setValue(param.name, v)}
            />
          ))}
          {numbers.map((param) => (
            <NumberRow
              key={param.name}
              id={`${prefix}${param.name}`}
              param={param}
              value={(values[param.name] ?? param.default) as number}
              dirty={param.name in dirty}
              measurements={measurements}
              nozzle={nozzle}
              onValue={(v) => setValue(param.name, v)}
            />
          ))}
        </div>
      </div>

      {stats?.size_mm ? (
        <div className="chrome shrink-0 border-t border-line-soft px-4 py-2">
          <span className="mono-caption text-muted">
            {stats.size_mm.map((n) => Math.round(n * 10) / 10).join(" × ")} mm
            {building ? " · rebuilding" : null}
          </span>
        </div>
      ) : null}

      {/* Always mounted: a live region only announces text that changes inside it. */}
      <p
        role="status"
        className={note ? "mx-4 mb-3 rounded-content bg-raised px-3 py-2 text-xs leading-4 text-ink-soft" : "sr-only"}
      >
        {note}
      </p>

      {dirtyCount > 0 ? (
        <div className="chrome mx-4 mb-3 flex h-9 shrink-0 items-center gap-2 rounded-content bg-accent-wash px-3">
          <span className="size-1.5 shrink-0 rounded-full bg-accent" />
          <span className="mono-id flex-1 uppercase text-accent-ink tabular-nums [letter-spacing:0.08em]">
            {dirtyCount} {dirtyCount === 1 ? "change" : "changes"}
          </span>
          <button
            type="button"
            onClick={() => onChange({})}
            className="mono-label rounded-control px-2 py-1 text-ink-soft transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-accent"
          >
            Reset
          </button>
          <span className="inline-flex" title="Save these values as the part's defaults.">
            <LoadingButton
              label="Apply"
              pendingLabel="Applying"
              successLabel="Applied"
              errorLabel="Try again"
              resetAfter={1400}
              variant="ink"
              disabled={applying}
              onAction={() => onApply(dirty)}
            />
          </span>
        </div>
      ) : null}
    </div>
  )
}
