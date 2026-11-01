import { useEffect, useState } from "react"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import { elapsedLabel } from "../format"
import { duration, ease } from "../motion/tokens"

const OUT = ease.out as [number, number, number, number]

// While a change rebuilds, the model on the stage is the old one. The pill says so where
// the eye already is, counts the wait, and fills a bar over the last build's time so the
// wait has a length. The bar stops short of full: the new model arriving is what ends it.
// It owns its presence, like the failure banner, so the caller flips `open`.
export function StageBuilding({ open, expected }: { open: boolean; expected?: number | null }) {
  return <AnimatePresence>{open ? <Pill key="building" expected={expected ?? null} /> : null}</AnimatePresence>
}

function Pill({ expected }: { expected: number | null }) {
  const reduced = useReducedMotion()
  const [started] = useState(() => performance.now())
  const [seconds, setSeconds] = useState(0)
  const [filling, setFilling] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => setSeconds((performance.now() - started) / 1000), 100)
    const frame = requestAnimationFrame(() => setFilling(true))
    return () => {
      clearInterval(timer)
      cancelAnimationFrame(frame)
    }
  }, [started])

  return (
    <motion.div
      role="status"
      initial={{ opacity: 0, y: reduced ? 0 : -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: reduced ? 0 : -6 }}
      transition={{ duration: duration.settle, ease: OUT }}
      className="panel chrome pointer-events-none absolute top-4 left-1/2 z-10 flex h-8 -translate-x-1/2 items-center gap-2.5 overflow-hidden rounded-full pr-3.5 pl-3"
    >
      <span
        aria-hidden
        className="size-3 shrink-0 rounded-full border-[1.5px] border-accent/25 border-t-accent motion-safe:animate-spin"
      />
      <span className="mono-label whitespace-nowrap text-ink">Rebuilding</span>
      <span className="mono-label w-9 text-right whitespace-nowrap text-muted tabular-nums">{elapsedLabel(seconds)}</span>
      {expected ? (
        <span aria-hidden className="absolute inset-x-0 bottom-0 h-0.5 bg-accent/15">
          <span
            className="block h-full origin-left bg-accent ease-out"
            style={{
              transform: `scaleX(${filling ? 0.92 : 0})`,
              transitionProperty: "transform",
              transitionDuration: reduced ? "0ms" : `${Math.max(0.3, expected) * 1000}ms`,
            }}
          />
        </span>
      ) : null}
    </motion.div>
  )
}
