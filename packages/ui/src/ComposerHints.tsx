import { useEffect, useState } from "react"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import { duration, ease } from "./motion/tokens"

// The two things that float over the composer: what a drag is about to do, and
// what a first-time visitor could say. Both are overlays because a textarea
// cannot style or animate its own placeholder.

const OUT = ease.out as [number, number, number, number]

/** The composer's drop target, lit while a photo is over it. The parent is the positioned box. */
export function DropHint({ active, label = "Drop the photo here" }: { active: boolean; label?: string }) {
  const reduced = useReducedMotion() === true
  return (
    <AnimatePresence initial={false}>
      {active ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduced ? 0 : duration.tick, ease: OUT }}
          className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center rounded-[6px] border border-dashed border-accent bg-accent-wash"
        >
          <span className="btn-label text-accent-ink">{label}</span>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}

/**
 * A placeholder that cycles, for the first conversation only. It crossfades, so
 * both phrases are on screen together for a moment; reduced motion still cycles,
 * because the point is the examples rather than the movement.
 */
export function CyclingPlaceholder({
  lines,
  active,
  everyMs = 4000,
  className,
}: {
  lines: string[]
  active: boolean
  everyMs?: number
  className?: string
}) {
  const [index, setIndex] = useState(0)
  const reduced = useReducedMotion() === true

  useEffect(() => {
    if (!active || lines.length < 2) return
    const timer = setInterval(() => setIndex((n) => (n + 1) % lines.length), everyMs)
    return () => clearInterval(timer)
  }, [active, lines.length, everyMs])

  if (!active || lines.length === 0) return null

  return (
    <span aria-hidden="true" className={clsx("pointer-events-none absolute inset-0 block", className)}>
      <AnimatePresence initial={false}>
        <motion.span
          key={index % lines.length}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduced ? 0 : duration.settle, ease: OUT }}
          className="absolute inset-x-0 top-0 block"
        >
          {lines[index % lines.length]}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}
