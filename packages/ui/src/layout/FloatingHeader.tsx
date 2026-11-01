import type { ReactNode } from "react"
import clsx from "clsx"

export interface FloatingHeaderProps {
  /** The lockup end. */
  start?: ReactNode
  /** The identity and status cells between the lockup and the tabs. */
  cells?: ReactNode
  /** Tabs, icons and the avatar, pushed right. */
  end?: ReactNode
  children?: ReactNode
  /** The desktop drags its window by the header bar itself, not by its cells. */
  dragRegion?: boolean
}

// The 52px floating header. One row of cells divided by hairlines, never an edge-to-edge bar.
export default function FloatingHeader({ start, cells, end, children, dragRegion }: FloatingHeaderProps) {
  return (
    <header
      className="panel chrome flex h-[52px] shrink-0 items-center overflow-hidden"
      {...(dragRegion ? { "data-tauri-drag-region": true } : {})}
    >
      {start}
      {cells}
      {children}
      {end ? (
        <>
          <div className="flex-1" />
          {end}
        </>
      ) : null}
    </header>
  )
}

export function HeaderDivider() {
  return <div className="h-full w-px bg-line" />
}

export function HeaderCell({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("flex h-full items-center px-4", className)}>{children}</div>
}

// The Asimov stacked pair: a 9px mono label over the value it names.
export function HeaderStack({ label, value, className }: { label: string; value: ReactNode; className?: string }) {
  return (
    <HeaderCell className={className}>
      <div className="flex flex-col gap-[3px]">
        <span className="mono-label text-[9px] leading-[10px] text-faint">{label}</span>
        <span className="mono-value text-ink">{value}</span>
      </div>
    </HeaderCell>
  )
}

export type HeaderTone = "pass" | "warn" | "fail" | "none" | "building"

const DOT: Record<HeaderTone, string> = {
  pass: "bg-pass",
  warn: "bg-warn",
  fail: "bg-fail",
  none: "bg-line",
  building: "bg-accent motion-safe:animate-pulse",
}

// A 6px dot is too small to carry the state on its own, so the cell takes a wash of
// the same tone. Nothing has been checked yet is the one state with no colour to show.
const WASH: Record<HeaderTone, string> = {
  pass: "border-line bg-pass-wash",
  warn: "border-line bg-warn-wash",
  fail: "border-line bg-fail-wash",
  none: "border-transparent bg-transparent",
  building: "border-line bg-accent-wash",
}

// A tone swap reads as one move only if the wash, the hairline and the dot travel
// together. 150ms is the browser default, not a decision.
const TONE_SHIFT = "transition-colors duration-(--duration-settle) ease-out-strong"

export function HeaderStatus({
  tone,
  label,
  detail,
  className,
}: {
  tone: HeaderTone
  label: string
  detail?: string
  className?: string
}) {
  return (
    <HeaderCell className={className}>
      {/* Radius 3, the same as a header tab, so the two rounded things in the row agree. */}
      <span className={clsx("flex h-7 items-center gap-2 rounded-[3px] border px-2.5 whitespace-nowrap", TONE_SHIFT, WASH[tone])}>
        <span className={clsx("size-1.5 shrink-0 rounded-full", TONE_SHIFT, DOT[tone])} />
        <span className="mono-label text-ink">{label}</span>
        {detail ? <span className="mono-caption text-muted">{detail}</span> : null}
      </span>
    </HeaderCell>
  )
}

// The icon cluster. The consumer drops IconButtons in; the cell only spaces them.
export function HeaderIcons({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("flex h-full items-center gap-1 px-3", className)}>{children}</div>
}
