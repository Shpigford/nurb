import type { ReactNode } from "react"
import Icon from "../Icon"
import PanelStrip from "../PanelStrip"

export interface PinnedParam {
  name: string
  value: string
}

export interface RailReadouts {
  grams?: number | null
  seconds?: number | null
  heightMm?: number | null
}

export interface ParamRailProps {
  count: number
  /** What the spec fixed. These carry a lock and never get a slider. */
  pinned?: PinnedParam[]
  /** Where the consumer drops <ParamsPanel/>. */
  params: ReactNode
  readouts?: RailReadouts
  warnCount?: number
  failCount?: number
  disclosures?: ReactNode
  actions: ReactNode
}

// Print time reads as h:mm, not the m:ss a build does.
function hoursLabel(seconds: number): string {
  const total = Math.max(0, Math.round(seconds / 60))
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`
}

function Readout({ value, unit }: { value: string; unit: string }) {
  return (
    <span className="flex items-baseline gap-1">
      <span className="mono-value text-ink">{value}</span>
      <span className="mono-caption text-muted">{unit}</span>
    </span>
  )
}

function Rule({ children }: { children: string }) {
  return (
    <div className="chrome flex items-center gap-2 px-4 pt-[11px] pb-2">
      <span className="mono-caption text-faint [letter-spacing:0.12em]">{children}</span>
      <span className="h-px flex-1 bg-line-soft" />
    </div>
  )
}

// The right rail: what the spec pinned, what the user may drag, and a pinned footer
// of readouts, the warning count and the export. Passing checks stay silent until a
// disclosure opens.
export default function ParamRail({
  count,
  pinned,
  params,
  readouts,
  warnCount = 0,
  failCount = 0,
  disclosures,
  actions,
}: ParamRailProps) {
  const flagged = failCount > 0 ? failCount : warnCount
  return (
    <aside className="panel flex w-[288px] shrink-0 flex-col overflow-hidden">
      <PanelStrip label="Parameters" inset={16} trailing={count} />

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
        {pinned && pinned.length > 0 ? (
          <>
            <Rule>Pinned by spec</Rule>
            <ul className="flex flex-col gap-1.5 px-4 pb-1">
              {pinned.map((row) => (
                <li key={row.name} className="flex items-center gap-2">
                  <span className="shrink-0 text-faint">
                    <Icon name="lock" />
                  </span>
                  <span className="mono-label truncate text-muted">{row.name}</span>
                  <span className="flex-1" />
                  <span className="mono-value text-right text-ink">{row.value}</span>
                </li>
              ))}
            </ul>
          </>
        ) : null}
        {params}
      </div>

      <div className="min-h-0 overflow-y-auto border-t border-line bg-ground">
        {readouts ? (
          <div className="chrome flex items-center justify-between px-4 py-2.5">
            <Readout value={readouts.grams == null ? "-" : String(Math.round(readouts.grams))} unit="g" />
            <Readout value={readouts.seconds == null ? "-" : hoursLabel(readouts.seconds)} unit="hr" />
            <Readout value={readouts.heightMm == null ? "-" : String(Math.round(readouts.heightMm))} unit="mm" />
          </div>
        ) : null}
        <div className="h-px bg-line-soft" />
        {/* The CHECKS disclosure carries the count when disclosures are present; the chip is for rails without them. */}
        {flagged > 0 && !disclosures ? (
          <div className="flex items-center gap-2 px-4 py-2">
            <span className={failCount > 0 ? "text-fail" : "text-warn"}>
              <Icon name={failCount > 0 ? "xmark" : "warning"} />
            </span>
            <span className="mono-label text-ink">
              {flagged} {failCount > 0 ? (flagged === 1 ? "fail" : "fails") : flagged === 1 ? "warn" : "warns"}
            </span>
          </div>
        ) : null}
        {disclosures}
        <div className="flex gap-2 p-4">{actions}</div>
      </div>
    </aside>
  )
}
