import type { ReactNode } from "react"

// The 30px mono header strip every floating panel opens with: a label on the
// left, a count or status on the right, a soft rule beneath.
export default function PanelStrip({
  label,
  trailing,
  inset = 18,
}: {
  label: ReactNode
  trailing?: ReactNode
  inset?: 16 | 18
}) {
  return (
    <div
      className={`chrome flex h-[30px] shrink-0 items-center justify-between border-b border-line-soft ${
        inset === 16 ? "px-4" : "px-[18px]"
      }`}
    >
      <div className="mono-label shrink-0 text-muted">{label}</div>
      {trailing ? (
        <div className="mono-caption min-w-0 text-muted tabular-nums [letter-spacing:0.1em]">
          {trailing}
        </div>
      ) : null}
    </div>
  )
}
