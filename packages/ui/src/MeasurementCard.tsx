import Icon from "./Icon"
import { words } from "./format"
import type { Measurement } from "./types"

/** Whether a recorded measurement moved an earlier value, rather than writing a first one. */
export function changedSize(measurement: Measurement): boolean {
  return measurement.previous_value_mm != null && measurement.previous_value_mm !== measurement.value_mm
}

// A measurement the intake recorded mid-conversation. When the value moved
// and parts read it, the card carries the rebuild: no new part, no new spec.
// The payload names the parts that went stale at the time; the strip shows
// only those still stale now (`staleParts`, live from the host), so a rebuilt
// part stops being offered a rebuild.
export default function MeasurementCard({
  measurement,
  staleParts,
  onAccept,
  onEdit,
  onRebuild,
  rebuilding,
}: {
  measurement: Measurement
  staleParts?: string[]
  onAccept?: (name: string) => void
  onEdit?: (name: string) => void
  onRebuild?: (staleParts: string[]) => void
  rebuilding?: boolean
}) {
  const recorded = measurement.stale_parts ?? []
  const stale = staleParts ? recorded.filter((name) => staleParts.includes(name)) : recorded
  const changed = changedSize(measurement)
  const showAccept = measurement.provisional && onAccept

  return (
    <div className="flex flex-col overflow-hidden rounded-[6px] border border-line">
      <div className="chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3">
        <span className="mono-label flex items-center gap-2 text-ink">
          <Icon name="ruler" />
          {changed ? "Measurement changed" : "Measurement recorded"}
        </span>
        {measurement.provisional ? (
          <span className="mono-caption text-warn [letter-spacing:0.1em]">Provisional</span>
        ) : null}
      </div>
      <div className="flex flex-col gap-1.5 px-3 pt-[9px] pb-2.5">
        <div className="flex items-baseline gap-2">
          <span className="min-w-0 flex-1 truncate text-xs leading-4 text-ink-soft">{words(measurement.name)}</span>
          {changed ? (
            <span className="mono-value text-muted line-through">{measurement.previous_value_mm} mm</span>
          ) : null}
          <span className="mono-value text-ink">{measurement.value_mm} mm</span>
        </div>
        <p className="text-xs leading-4 text-muted">{measurement.how}</p>
        {showAccept || onEdit ? (
          <div className="mt-0.5 flex items-center gap-1.5">
            {showAccept ? (
              <button
                type="button"
                onClick={() => onAccept(measurement.name)}
                className="btn-label chrome rounded-control focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent bg-ink px-2 py-1 text-white transition-colors hover:bg-ink-soft"
              >
                Accept
              </button>
            ) : null}
            {onEdit ? (
              <button
                type="button"
                onClick={() => onEdit(measurement.name)}
                className="btn-label chrome rounded-control focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent border border-line px-2 py-1 text-ink-soft transition-colors hover:bg-raised"
              >
                Edit
              </button>
            ) : null}
          </div>
        ) : null}
        {stale.length > 0 ? (
          <div className="mt-1 flex items-center gap-2 rounded-[6px] bg-warn-wash px-2.5 py-1.5">
            <span className="size-1.5 shrink-0 rounded-full bg-warn" />
            <span className="mono-caption min-w-0 flex-1 truncate text-warn [letter-spacing:0.08em]">
              {stale.length === 1 ? `${stale[0]} is stale` : `${stale.length} parts stale · ${stale.join(", ")}`}
            </span>
            {onRebuild ? (
              <button
                type="button"
                onClick={() => onRebuild(stale)}
                disabled={rebuilding}
                className="btn-label chrome rounded-control focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent bg-ink px-2 py-1 text-white transition-colors hover:bg-ink-soft disabled:opacity-60"
              >
                {rebuilding ? "Rebuilding…" : "Rebuild"}
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}
