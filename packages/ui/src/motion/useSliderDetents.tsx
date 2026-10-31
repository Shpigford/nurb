import { useCallback, useMemo, useRef, type ChangeEvent, type KeyboardEvent } from "react"
import clsx from "clsx"
import { cue } from "../sound"

// Ported from interior.dev's Slider Detents (MIT). Our parameter sliders are native
// input[type=range] so the platform keyboard map and assistive tech stay intact, so
// only the snapping survives the port: the pointer hands the value to a nearby detent,
// and the keyboard never does, or a detent beside 0.95 would make 0.95 unreachable.

export type Detent = { value: number; label?: string }

export interface UseSliderDetentsOptions {
  value: number
  onValueChange: (value: number) => void
  min: number
  max: number
  step: number
  detents: (number | Detent)[]
  /** Capture radius in value units. Inside it the pointer gives way to the detent. */
  pull?: number
}

export interface SliderDetents {
  /** Wire to the input's onChange. Snaps the raw value, then emits it. */
  onChange: (event: ChangeEvent<HTMLInputElement>) => void
  /** Wire to the input's onKeyDown, so arrow keys step past a detent instead of sticking to it. */
  onKeyDown: (event: KeyboardEvent<HTMLInputElement>) => void
  /** Index into `detents` the value is parked on, or -1. */
  activeDetent: number
  detents: Detent[]
  /** The active detent's name, for a readout beside the number. */
  activeLabel?: string
}

function tidy(value: number) {
  return Math.round(value * 1e6) / 1e6
}

export function useSliderDetents({
  value,
  onValueChange,
  min,
  max,
  step,
  detents,
  pull,
}: UseSliderDetentsOptions): SliderDetents {
  const list = useMemo<Detent[]>(() => detents.map((d) => (typeof d === "number" ? { value: d } : d)), [detents])
  const grab = pull ?? (max - min) * 0.045

  const emit = useRef(onValueChange)
  emit.current = onValueChange

  const activeDetent = useMemo(() => list.findIndex((d) => tidy(d.value) === tidy(value)), [list, value])
  const parked = useRef(activeDetent)
  parked.current = activeDetent
  // A held arrow key repeats keydown, so onChange can clear the flag itself.
  const keying = useRef(false)

  const snap = useCallback(
    (raw: number) => {
      let index = -1
      let nearest = grab
      for (let i = 0; i < list.length; i += 1) {
        const distance = Math.abs(raw - list[i].value)
        if (distance <= nearest) {
          nearest = distance
          index = i
        }
      }
      if (index >= 0) return list[index].value
      return min + Math.round((raw - min) / step) * step
    },
    [grab, list, min, step],
  )

  const onChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const raw = Number(event.target.value)
      if (!Number.isFinite(raw)) return
      const free = keying.current
      keying.current = false
      const next = tidy(Math.min(max, Math.max(min, free ? raw : snap(raw))))
      const landed = list.findIndex((d) => tidy(d.value) === next)
      if (landed >= 0 && landed !== parked.current) cue("tick")
      if (next !== tidy(value)) emit.current(next)
    },
    [list, max, min, snap, value],
  )

  const onKeyDown = useCallback((event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key.startsWith("Arrow") || event.key === "PageUp" || event.key === "PageDown") keying.current = true
  }, [])

  return { onChange, onKeyDown, activeDetent, detents: list, activeLabel: list[activeDetent]?.label }
}

/** The tick marks under a slider. Goes inside a `relative` wrapper around the input. */
export function DetentMarks({
  detents,
  min,
  max,
  activeDetent,
  className,
}: {
  detents: Detent[]
  min: number
  max: number
  activeDetent?: number
  className?: string
}) {
  const span = max - min
  return (
    // Inset by half the 12px thumb, because that is the width the thumb's centre actually travels.
    <div aria-hidden className={clsx("pointer-events-none absolute inset-x-[6px] bottom-0", className)}>
      {detents.map((detent, index) => (
        <span
          key={detent.value}
          title={detent.label}
          className={clsx(
            "absolute bottom-0 block h-[3px] w-px -translate-x-1/2",
            index === activeDetent ? "bg-accent" : "bg-line",
          )}
          style={{ left: span > 0 ? `${((detent.value - min) / span) * 100}%` : "0%" }}
        />
      ))}
    </div>
  )
}
