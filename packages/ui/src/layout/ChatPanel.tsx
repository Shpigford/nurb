import type { ReactNode } from "react"
import PanelStrip from "../PanelStrip"

export interface ChatPanelProps {
  strip: { label: string; trailing?: ReactNode }
  /** The agent picker, which lives in the strip's trailing area on the desktop. */
  picker?: ReactNode
  children: ReactNode
  composer: ReactNode
  /** Kept mounted but out of view, so a background conversation stays alive. */
  hidden?: boolean
  /** The desktop drags its window by the strip. */
  dragRegion?: boolean
}

// The conversation panel: 372 wide, the transcript scrolling between a strip and a pinned composer.
export default function ChatPanel({ strip, picker, children, composer, hidden, dragRegion }: ChatPanelProps) {
  return (
    <section className="panel flex w-[372px] shrink-0 flex-col overflow-hidden" hidden={hidden}>
      <div {...(dragRegion ? { "data-tauri-drag-region": true } : {})}>
        <PanelStrip
          label={strip.label}
          inset={16}
          trailing={
            picker || strip.trailing ? (
              <span className="flex items-center gap-2">
                {strip.trailing}
                {picker}
              </span>
            ) : undefined
          }
        />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      <div className="shrink-0 p-4 pt-0">{composer}</div>
    </section>
  )
}
