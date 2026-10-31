import { useEffect, useRef, useState, type ReactNode } from "react"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import { duration, ease } from "./tokens"

// Ported from interior.dev (MIT), restyled onto the nurb tokens.
// The box is sized before the data lands and never resized after it, so the row under a card
// cannot jump at the moment the answer arrives.

const OUT = ease.out as [number, number, number, number]

const WIDTHS = [100, 93, 97, 88, 95, 91] as const

// The last bar reads as the end of a paragraph, the rest vary so the block is not a grid.
function widthFor(index: number, total: number) {
  if (total > 1 && index === total - 1) return 62
  return WIDTHS[(index * 7 + 3) % WIDTHS.length]
}

export interface UseSkeletonSwapOptions {
  loading: boolean
  /** Milliseconds of silence before the skeleton may paint. A faster answer shows none. */
  delay?: number
  /** Once painted, the skeleton stays this long, so it cannot blink. */
  minVisible?: number
}

export function useSkeletonSwap({ loading, delay = 120, minVisible = 380 }: UseSkeletonSwapOptions) {
  const [visible, setVisible] = useState(false)
  const shownAt = useRef(0)

  useEffect(() => {
    if (loading) {
      if (visible) return
      const t = setTimeout(() => {
        shownAt.current = performance.now()
        setVisible(true)
      }, delay)
      return () => clearTimeout(t)
    }
    if (!visible) return
    const rest = Math.max(0, minVisible - (performance.now() - shownAt.current))
    const t = setTimeout(() => setVisible(false), rest)
    return () => clearTimeout(t)
  }, [loading, visible, delay, minVisible])

  return { showSkeleton: visible }
}

export interface SkeletonSwapProps extends UseSkeletonSwapOptions {
  children: ReactNode
  /** How many bars the skeleton draws, and how much height it reserves. */
  lines?: number
  /** Leading of the content this stands in for; match it and the reserve is exact. */
  lineHeight?: number
  /** Explicit box height in pixels, for content that is not text: a chart, a thumbnail, a card. */
  reserve?: number
  /** Names the region and announces "<label> loaded" once. */
  label?: string
  className?: string
}

export default function SkeletonSwap({
  loading,
  children,
  lines = 3,
  lineHeight = 21,
  reserve,
  delay = 120,
  minVisible = 380,
  label,
  className,
}: SkeletonSwapProps) {
  const { showSkeleton } = useSkeletonSwap({ loading, delay, minVisible })
  const reduced = useReducedMotion()
  const shell = useRef<HTMLDivElement>(null)
  const body = useRef<HTMLDivElement>(null)
  const [scrollable, setScrollable] = useState(false)
  const box = reserve ?? lines * lineHeight
  const settle = { duration: reduced ? 0 : duration.settle, ease: OUT }

  // Content that overruns the reserve scrolls instead of growing the page, and the box takes a
  // tab stop only while it is actually scrollable, so nobody tabs into a dead one.
  useEffect(() => {
    const el = shell.current
    if (!el || typeof ResizeObserver === "undefined") return
    const check = () => setScrollable(el.scrollHeight - el.clientHeight > 1)
    check()
    const ro = new ResizeObserver(check)
    ro.observe(el)
    if (body.current) ro.observe(body.current)
    return () => ro.disconnect()
  }, [])

  return (
    <div
      ref={shell}
      aria-busy={loading}
      aria-label={label}
      tabIndex={scrollable ? 0 : undefined}
      style={{ height: box }}
      className={clsx("relative grid overflow-y-auto overscroll-contain text-ink-soft", className)}
    >
      <motion.div
        ref={body}
        className="col-start-1 row-start-1 min-w-0"
        initial={false}
        animate={{ opacity: showSkeleton ? 0 : 1 }}
        transition={settle}
        style={{ pointerEvents: showSkeleton ? "none" : undefined }}
      >
        {children}
      </motion.div>

      <AnimatePresence initial={false}>
        {showSkeleton ? (
          <motion.div
            key="skeleton"
            aria-hidden
            data-skeleton
            className="pointer-events-none col-start-1 row-start-1 w-full self-start"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={settle}
          >
            {Array.from({ length: lines }, (_, i) => (
              <div key={i} className="flex items-center" style={{ height: lineHeight }}>
                <div className="h-[8px] rounded-[3px] bg-raised" style={{ width: `${widthFor(i, lines)}%` }} />
              </div>
            ))}
          </motion.div>
        ) : null}
      </AnimatePresence>

      {label ? (
        <span role="status" className="sr-only">
          {loading ? "" : `${label} loaded`}
        </span>
      ) : null}
    </div>
  )
}
