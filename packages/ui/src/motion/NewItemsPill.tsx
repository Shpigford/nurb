import { useEffect, useState } from "react"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import Icon from "../Icon"
import { duration, ease } from "./tokens"

// Ported from interior.dev (MIT) and restyled onto the nurb tokens. The pill sits
// over the scroller, so neither its arrival nor a count crossing from one digit
// to three reflows a row underneath it.

const OUT = ease.out as [number, number, number, number]
const INSTANT = { duration: 0 } as const

export type NewItemsAnchor = "top" | "bottom"

const defaultLabel = (n: number) => `${n} new ${n === 1 ? "item" : "items"}`

export default function NewItemsPill({
  count,
  onClick,
  anchor = "bottom",
  label = defaultLabel,
  className,
}: {
  count: number
  onClick: () => void
  anchor?: NewItemsAnchor
  /** Builds the visible text and the accessible name. Pluralise here; nothing downstream guesses at grammar. */
  label?: (count: number) => string
  className?: string
}) {
  const reduced = useReducedMotion() === true
  const [announced, setAnnounced] = useState(0)

  // One settled count after the last arrival, rather than one announcement per item.
  useEffect(() => {
    if (count === 0) {
      setAnnounced(0)
      return
    }
    const t = setTimeout(() => setAnnounced(count), 700)
    return () => clearTimeout(t)
  }, [count])

  const text = label(count)
  const off = anchor === "bottom" ? 10 : -10

  return (
    <div
      className={clsx(
        "pointer-events-none absolute inset-x-0 z-10 flex justify-center",
        anchor === "bottom" ? "bottom-2" : "top-2",
        className
      )}
    >
      <AnimatePresence initial={false}>
        {count > 0 ? (
          <motion.button
            type="button"
            onClick={onClick}
            aria-label={text}
            initial={reduced ? { opacity: 0 } : { opacity: 0, scale: 0.94, y: off }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={reduced ? { opacity: 0, transition: INSTANT } : { opacity: 0, scale: 0.96, y: off * 0.5 }}
            transition={reduced ? INSTANT : { duration: duration.settle, ease: OUT }}
            className="chrome btn-label pointer-events-auto inline-flex h-7 items-center gap-1.5 rounded-[3px] border border-line bg-ground pr-3 pl-2.5 text-ink-soft shadow-[var(--shadow-panel)] hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            <span aria-hidden="true" className={clsx("flex text-accent", anchor === "bottom" && "rotate-180")}>
              <Icon name="arrow-up" />
            </span>
            <span className="tabular-nums" aria-hidden="true">
              {text}
            </span>
          </motion.button>
        ) : null}
      </AnimatePresence>
      <span role="status" aria-live="polite" className="sr-only">
        {announced > 0 ? label(announced) : ""}
      </span>
    </div>
  )
}
