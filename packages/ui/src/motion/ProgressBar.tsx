import { useEffect, useId, useState, type AriaAttributes } from "react"
import { motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import { duration, ease } from "./tokens"

// Ported from interior.dev (MIT), restyled onto the nurb tokens.
// A build starts before anyone knows how long it takes, so the bar crawls toward a low ceiling
// and hands over to the measured value the moment one arrives. The crawl is the floor, which is
// why the handover can never snap backwards.

const OUT = ease.out as [number, number, number, number]

/** The fraction the crawl converges on. Low, so a real value rarely lands behind it. */
const CEILING = 0.35
/** Time constant of the crawl in milliseconds: ~63% of the ceiling after this long, then flat. */
const CRAWL = 2200

export interface ProgressBarProps {
  /** The measured amount. null means the total is unknown and the bar crawls. */
  value: number | null
  max?: number
  /** Divide the track into cells. Progress quantizes to them, so bar and readout always agree. */
  segments?: number
  label?: string
  /** Readout while the total is unknown, in the same cell as the percentage. */
  pendingLabel?: string
  /** Announced once through the live region when the bar fills. */
  completeLabel?: string
  className?: string
}

export default function ProgressBar({
  value,
  max = 100,
  segments,
  label = "Progress",
  pendingLabel = "Working",
  completeLabel = "Complete",
  className,
}: ProgressBarProps) {
  const reduced = useReducedMotion()
  const labelId = useId()
  const [crawled, setCrawled] = useState(0)
  const indeterminate = value === null

  // Not an idle loop: an exponential approach that converges, cancels its own frames and leaves
  // nothing running. Under reduced motion it is skipped rather than faked.
  useEffect(() => {
    if (!indeterminate || reduced) return
    const start = performance.now()
    let frame = requestAnimationFrame(function step() {
      const reached = CEILING * (1 - Math.exp(-(performance.now() - start) / CRAWL))
      setCrawled((prev) => Math.max(prev, reached))
      if (CEILING - reached > 0.002) frame = requestAnimationFrame(step)
    })
    return () => cancelAnimationFrame(frame)
  }, [indeterminate, reduced])

  const measured = value === null || max <= 0 ? 0 : Math.min(1, Math.max(0, value / max))
  const raw = Math.max(indeterminate ? crawled : 0, measured)
  const fraction = segments ? Math.round(raw * segments) / segments : raw
  const percent = Math.round(fraction * 100)
  const complete = !indeterminate && fraction >= 1

  const aria: AriaAttributes = indeterminate
    ? {}
    : { "aria-valuenow": Math.round(measured * max * 100) / 100, "aria-valuetext": `${percent}%` }

  const fill = { duration: reduced ? 0 : duration.settle, ease: OUT }

  return (
    <div className={clsx("w-full", className)}>
      <div className="flex items-baseline justify-between gap-3">
        <span id={labelId} className="mono-label truncate text-ink-soft">
          {label}
        </span>
        <span aria-hidden className="grid shrink-0 justify-items-end">
          <motion.span
            className="mono-label col-start-1 row-start-1 whitespace-nowrap text-muted"
            initial={false}
            animate={{ opacity: indeterminate ? 1 : 0 }}
            transition={fill}
          >
            {pendingLabel}
          </motion.span>
          <motion.span
            className="mono-value col-start-1 row-start-1 whitespace-nowrap text-ink"
            initial={false}
            animate={{ opacity: indeterminate ? 0 : 1 }}
            transition={fill}
          >
            {percent}%
          </motion.span>
        </span>
      </div>

      <div
        role="progressbar"
        aria-labelledby={labelId}
        aria-valuemin={0}
        aria-valuemax={max}
        {...aria}
        className="mt-2 h-[8px] overflow-hidden rounded-[3px] bg-raised"
      >
        {segments ? (
          <div className="flex h-full gap-px" data-cells={segments}>
            {Array.from({ length: segments }, (_, i) => (
              <motion.span
                key={i}
                data-lit={i < Math.round(fraction * segments) ? "" : undefined}
                className="h-full flex-1 bg-accent first:rounded-l-[3px] last:rounded-r-[3px]"
                initial={false}
                animate={{ opacity: i < Math.round(fraction * segments) ? 1 : 0.12 }}
                transition={{ duration: reduced ? 0 : duration.tick, ease: OUT }}
              />
            ))}
          </div>
        ) : (
          <motion.span
            className="block h-full origin-left rounded-[3px] bg-accent"
            initial={false}
            animate={{ scaleX: fraction }}
            transition={fill}
          />
        )}
      </div>

      <span aria-live="polite" className="sr-only">
        {complete ? completeLabel : indeterminate ? pendingLabel : ""}
      </span>
    </div>
  )
}
