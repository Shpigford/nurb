import type { ReactNode } from "react"
import clsx from "clsx"
import Icon, { type IconName } from "../Icon"

export type DisclosureTone = "warn" | "fail" | "pass" | "none"

export interface RailDisclosureProps {
  label: string
  summary?: ReactNode
  tone?: DisclosureTone
  open: boolean
  onToggle: () => void
  children: ReactNode
}

const GLYPH: Record<DisclosureTone, IconName | null> = {
  warn: "warning",
  fail: "xmark",
  pass: "check",
  none: null,
}

const TINT: Record<DisclosureTone, string> = {
  warn: "text-warn",
  fail: "text-fail",
  pass: "text-pass",
  none: "text-muted",
}

// One row of the rail's footer: checks, slice. Closed it is a count; open it is the detail.
export default function RailDisclosure({ label, summary, tone = "none", open, onToggle, children }: RailDisclosureProps) {
  const glyph = GLYPH[tone]
  return (
    <div className="flex flex-col">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="chrome flex h-8 w-full items-center gap-2 px-4 text-left hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent"
      >
        {glyph ? (
          <span className={clsx("shrink-0", TINT[tone])}>
            <Icon name={glyph} />
          </span>
        ) : null}
        <span className="mono-label text-ink">{label}</span>
        <span className="flex-1" />
        {summary ? <span className="mono-caption text-muted">{summary}</span> : null}
        <span className={clsx("shrink-0 text-muted transition-transform", open && "rotate-180")}>
          <Icon name="chevron-down" />
        </span>
      </button>
      {/* Hidden rather than unmounted: a slice that is still running
          survives the user collapsing the row it reports into. */}
      <div hidden={!open} className="max-h-48 overflow-y-auto border-t border-line-soft">
        {children}
      </div>
    </div>
  )
}
