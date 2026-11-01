import type { CSSProperties, ReactNode } from "react"
import clsx from "clsx"

export interface StageProps {
  header?: ReactNode
  children: ReactNode
  className?: string
  style?: CSSProperties
  /** Pad the top for a window titlebar. The design's 16 comes from `p-4`, so this only ever grows it. */
  topInset?: number
  /** The desktop drags its window by the bare ground. Tauri reads the attribute
   * off the element under the pointer only, so a panel on the stage is unaffected. */
  dragRegion?: boolean
}

// The page frame: flat stage ground, 16 of air on every side, the floating header
// above a single row of columns. Nothing here is a panel, so nothing touches an edge.
export default function Stage({ header, children, className, style, topInset, dragRegion }: StageProps) {
  return (
    <div
      className={clsx("isolate flex h-dvh flex-col gap-4 bg-stage p-4 antialiased", className)}
      style={topInset == null ? style : { ...style, paddingTop: topInset }}
      {...(dragRegion ? { "data-tauri-drag-region": true } : {})}
    >
      {header}
      <div className="flex min-h-0 flex-1 gap-4">{children}</div>
    </div>
  )
}

// The viewer column. It fills whatever the chat panel and the rail leave and is
// never a panel itself: the viewer paints the plate and the part straight onto the stage.
export function StageColumn({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={clsx("relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden", className)}>{children}</div>
  )
}

// Centring for the stage's empty states, which are ordinary content on the ground.
export function StageEmpty({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <StageColumn className={clsx("items-center justify-center", className)}>{children}</StageColumn>
  )
}
