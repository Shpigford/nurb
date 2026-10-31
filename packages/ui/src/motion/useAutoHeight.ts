import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type RefObject } from "react"
import { useReducedMotion } from "motion/react"
import { duration, ease } from "./tokens"

// Ported from interior.dev's Accordion (MIT), measurement only. height:auto cannot be
// animated, so the panel travels to a measured pixel height and then settles back to
// auto: a panel left at a number clips whatever lands in it afterwards, and a panel
// that only ever reads the number once animates to a stale target when its text rewraps.

const useIsomorphicLayoutEffect = typeof window === "undefined" ? useEffect : useLayoutEffect

const OUT = ease.out as [number, number, number, number]

export interface AutoHeight {
  /** Goes on the inner content element, the one that is measured. */
  ref: RefObject<HTMLDivElement | null>
  /** The measured content height, in pixels. */
  height: number
  /** Spread onto the outer motion.div along with `style`. */
  animate: { height: number | "auto" }
  transition: { duration: number; ease: [number, number, number, number] }
  onAnimationComplete: () => void
  style: CSSProperties
}

export function useAutoHeight(open: boolean): AutoHeight {
  const ref = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState(0)
  const [ready, setReady] = useState(false)
  // Already open on the first paint means auto straight away, so nothing flashes shut on mount.
  const [settled, setSettled] = useState(open)
  const wasOpen = useRef(open)

  if (wasOpen.current !== open) {
    wasOpen.current = open
    if (settled) setSettled(false)
  }

  useIsomorphicLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const read = () => {
      const next = el.getBoundingClientRect().height
      setHeight((prev) => (Math.abs(prev - next) < 0.5 ? prev : next))
    }
    read()
    setReady(true)
    // jsdom has no ResizeObserver, and a test that only checks the open state should not need one.
    if (typeof ResizeObserver === "undefined") return
    const observer = new ResizeObserver(read)
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const reduced = useReducedMotion()

  return {
    ref,
    height,
    animate: { height: open ? (settled || !ready ? "auto" : height) : 0 },
    transition: { duration: reduced ? 0 : duration.settle, ease: OUT },
    onAnimationComplete: () => {
      if (open) setSettled(true)
    },
    style: { overflow: "hidden" },
  }
}
