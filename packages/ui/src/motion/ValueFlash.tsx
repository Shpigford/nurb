import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import { duration, ease } from "./tokens"

// Ported from interior.dev's Value Flash (MIT). A number that moved on its own,
// with no click behind it, has to say so: a tint, a triangle, and the new figure
// rolling in from the side it came. Up is pass, down is fail.

const OUT = ease.out as [number, number, number, number]

export type FlashDirection = "up" | "down"

export interface ValueFlashState {
  direction: FlashDirection | null
  from: number
  changeId: number
  flashing: boolean
}

/** Watches a number and reports which way it moved, for a caller drawing its own cell. */
export function useValueFlash(value: number, hold = 900): ValueFlashState {
  const [state, setState] = useState<ValueFlashState>({ direction: null, from: value, changeId: 0, flashing: false })
  // Seeded at mount, so a table that has just loaded does not light every row.
  const previous = useRef(value)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const prior = previous.current
    if (Object.is(prior, value)) return
    previous.current = value
    // A blink with no direction is the one nobody can read.
    if (value - prior === 0) return

    setState((prev) => ({
      direction: value > prior ? "up" : "down",
      from: prior,
      changeId: prev.changeId + 1,
      flashing: true,
    }))

    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      timer.current = null
      setState((prev) => (prev.flashing ? { ...prev, flashing: false } : prev))
    }, hold)
  }, [value, hold])

  useEffect(() => () => (timer.current ? clearTimeout(timer.current) : undefined), [])

  return state
}

export interface ValueFlashProps {
  value: number
  /** Formats the figure. Tabular by construction, so equal-length values never jitter. */
  format?: (value: number) => string
  /** Prefixes the announcement, so a screen reader hears which figure moved. */
  label?: string
  /** Milliseconds the tint and the mark stay lit. */
  hold?: number
  className?: string
}

export default function ValueFlash({ value, format, label, hold = 900, className }: ValueFlashProps) {
  const { direction, flashing, changeId } = useValueFlash(value, hold)
  const reduced = useReducedMotion()
  const text = format ? format(value) : String(value)

  // One announcement per settled figure: each tick restarts the quiet period, so a
  // fast feed does not read sixty numbers a second into the live region.
  const [settled, setSettled] = useState(text)
  useEffect(() => {
    const id = setTimeout(() => setSettled(text), 700)
    return () => clearTimeout(id)
  }, [text])

  const fade = { duration: reduced ? 0 : duration.settle, ease: OUT }
  const roll = { duration: reduced ? 0 : duration.tick * 2, ease: OUT }

  return (
    <span
      data-direction={flashing ? direction : undefined}
      className={clsx(
        "mono-value relative inline-grid grid-flow-col items-center gap-1 rounded-[3px] px-1 py-px transition-colors",
        flashing ? (direction === "up" ? "text-pass" : "text-fail") : "text-ink",
        className,
      )}
    >
      {direction ? (
        <motion.span
          aria-hidden
          initial={{ opacity: 0 }}
          animate={{ opacity: flashing ? 1 : 0 }}
          transition={fade}
          className={clsx(
            "pointer-events-none absolute inset-0 rounded-[3px]",
            direction === "up" ? "bg-pass-wash" : "bg-fail-wash",
          )}
        />
      ) : null}

      <span aria-hidden className="relative inline-grid overflow-hidden">
        <AnimatePresence initial={false} mode="popLayout">
          <motion.span
            key={changeId}
            initial={reduced ? { opacity: 0 } : { opacity: 0, y: direction === "down" ? "-0.85em" : "0.85em" }}
            animate={{ opacity: 1, y: "0em" }}
            exit={{ opacity: 0, y: direction === "down" ? "0.7em" : "-0.7em", transition: roll }}
            transition={roll}
            className="col-start-1 row-start-1"
          >
            {text}
          </motion.span>
        </AnimatePresence>
      </span>

      {/* The cell is always there, so a flash never reflows the row. */}
      <span aria-hidden className="relative grid size-[1em] place-items-center">
        <AnimatePresence initial={false}>
          {flashing && direction ? (
            <motion.svg
              key={`${changeId}-${direction}`}
              viewBox="0 0 256 256"
              fill="currentColor"
              initial={reduced ? { opacity: 0 } : { opacity: 0, scale: 0.4 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, transition: fade }}
              transition={fade}
              className="col-start-1 row-start-1 block size-[0.68em]"
            >
              {direction === "up" ? <path d="M128 68 L210 180 H46 Z" /> : <path d="M128 188 L46 76 H210 Z" />}
            </motion.svg>
          ) : null}
        </AnimatePresence>
      </span>

      <span className="sr-only" aria-live="polite">
        {label ? `${label}: ${settled}` : settled}
      </span>
    </span>
  )
}
