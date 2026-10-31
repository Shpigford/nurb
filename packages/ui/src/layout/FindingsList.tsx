import { motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import Icon from "../Icon"
import { duration, ease } from "../motion/tokens"
import { useValueFlash } from "../motion/ValueFlash"
import type { Finding } from "../types"

const OUT = ease.out as [number, number, number, number]

export type Verdict = "pass" | "warn" | "fail" | "none"

export interface FindingsListProps {
  findings: Finding[]
  verdict: Verdict
  highlight?: number | null
  onHighlight?: (index: number | null) => void
}

// The findings the checks flagged, and the rail end of the viewer's two-way highlight.
export default function FindingsList({ findings, verdict, highlight, onHighlight }: FindingsListProps) {
  const reduced = useReducedMotion()
  const count = findings.length
  // The count moves on its own after a rebuild, with no click behind it, so the line
  // that carries it says which way it went. Fewer is always the good direction.
  const { direction, flashing } = useValueFlash(count)
  const lit = flashing && !reduced
  const worse = direction === "up"

  // An empty list is not a pass: a part that never built, and one whose build
  // broke, both arrive here with nothing to list.
  const summary =
    count > 0
      ? `${count} ${count === 1 ? "finding" : "findings"} to fix.`
      : verdict === "none"
        ? "Nothing checked yet"
        : verdict === "fail"
          ? "The build stopped before the checks ran"
          : "Nothing to fix. Checks pass at these numbers."

  const line = (
    <p
      aria-live="polite"
      className={clsx(
        "mono-caption py-1 text-center transition-colors duration-(--duration-settle) ease-out-strong",
        lit ? (worse ? "bg-fail-wash text-fail" : "bg-pass-wash text-pass") : "text-muted",
      )}
    >
      {summary}
    </p>
  )

  if (count === 0) return line

  return (
    <>
      {line}
      <ul className="flex flex-col">
        {findings.map((finding, index) => (
          // Keyed by what the finding says, not by where it sits, so a rebuild that
          // changes nothing leaves the rows alone instead of replaying the entrance.
          <motion.li
            key={`${finding.rule}:${finding.message}`}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: reduced ? 0 : duration.settle, ease: OUT, delay: reduced ? 0 : index * 0.06 }}
          >
            {/* Leaving the row keeps the highlight, because the point of picking one is to
                look at the geometry it names. Clicking the picked row lets it go. */}
            <button
              type="button"
              aria-pressed={highlight === index}
              onMouseEnter={() => onHighlight?.(index)}
              onClick={() => onHighlight?.(highlight === index ? null : index)}
              className={clsx(
                "flex w-full items-start gap-2 px-4 py-2 text-left hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent",
                highlight === index && "bg-raised"
              )}
            >
              <span className={clsx("mt-0.5 shrink-0", finding.severity === "fail" ? "text-fail" : "text-warn")}>
                <Icon name={finding.severity === "fail" ? "xmark" : "warning"} />
              </span>
              <span className="flex min-w-0 flex-col gap-1">
                <span className="mono-label text-ink">{finding.label || finding.rule}</span>
                <span className="text-chat text-ink-soft">{finding.message}</span>
              </span>
            </button>
          </motion.li>
        ))}
      </ul>
    </>
  )
}
