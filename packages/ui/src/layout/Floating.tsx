import { forwardRef, useCallback, useEffect, useLayoutEffect, useState, type ReactNode, type RefObject } from "react"
import { createPortal } from "react-dom"

export interface FloatingProps {
  /** The control the panel belongs to. Its box is where the panel is placed. */
  anchor: RefObject<HTMLElement | null>
  /** Fixed width, so the lane the panel sits in never depends on its contents. */
  width: number
  /** Which edge of the anchor the panel lines its own edge up with. */
  align?: "left" | "right"
  /** Clear space between the anchor's top and the panel's bottom. */
  gap?: number
  role?: string
  "aria-label"?: string
  className?: string
  children: ReactNode
}

// The rail's menus open upward from a control that sits inside a scroller inside a
// panel that clips, so an absolutely placed menu is cut to a few pixels. This draws
// the panel on the body instead and places it from the anchor's own box.
const Floating = forwardRef<HTMLDivElement, FloatingProps>(function Floating(
  { anchor, width, align = "right", gap = 6, className, children, ...rest },
  ref
) {
  const [box, setBox] = useState<{ left: number; bottom: number } | null>(null)

  const place = useCallback(() => {
    const rect = anchor.current?.getBoundingClientRect()
    if (!rect) return
    const edge = align === "right" ? rect.right - width : rect.left
    setBox({
      left: Math.max(8, Math.min(edge, window.innerWidth - width - 8)),
      bottom: Math.max(8, window.innerHeight - rect.top + gap),
    })
  }, [anchor, width, align, gap])

  useLayoutEffect(place, [place])

  // The anchor moves when the rail scrolls or the window resizes, and a menu left
  // behind would point at nothing. Capture, so a nested scroller is heard too.
  useEffect(() => {
    window.addEventListener("resize", place)
    window.addEventListener("scroll", place, true)
    return () => {
      window.removeEventListener("resize", place)
      window.removeEventListener("scroll", place, true)
    }
  }, [place])

  if (typeof document === "undefined") return null

  return createPortal(
    <div
      ref={ref}
      style={{ position: "fixed", left: box?.left ?? 0, bottom: box?.bottom ?? 0, width }}
      className={className}
      {...rest}
    >
      {children}
    </div>,
    document.body
  )
})

export default Floating
