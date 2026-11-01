import clsx from "clsx"
import { rev } from "@nurb/ui"
import type { Part } from "./api"
import { verdictDot, verdictOf } from "./verdict"

export default function PartList({
  parts,
  selected,
  onSelect,
}: {
  parts: Part[]
  selected: Part | null
  onSelect: (name: string) => void
}) {
  if (parts.length === 0) return null
  return (
    <ul className="flex shrink-0 flex-col border-b border-line p-2">
      {parts.map((part) => {
        const verdict = verdictOf(part.build)
        return (
          <li key={part.id}>
            <button
              type="button"
              aria-pressed={part.id === selected?.id}
              onClick={() => onSelect(part.name)}
              className={clsx(
                "flex w-full items-center gap-2 rounded-control px-2 py-1.5 text-left transition-colors",
                "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
                part.id === selected?.id ? "bg-accent-wash" : "hover:bg-raised"
              )}
            >
              <span className={clsx("size-2 shrink-0 rounded-full", verdictDot(verdict))} />
              <span className="mono-value truncate text-ink">{part.name}</span>
              <span className="mono-caption ml-auto shrink-0 text-muted">{rev(part.revision)}</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
