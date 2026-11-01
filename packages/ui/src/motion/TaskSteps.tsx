import { useEffect, useState } from "react"
import { AnimatePresence, motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import { duration, ease } from "./tokens"

// Ported from interior.dev (MIT), restyled onto the nurb tokens.
// The whole plan mounts on the first paint with the pending rows dimmed, so a step finishing
// changes colours and marks and never geometry. The check draws itself in: the stroke arrives
// the way a pen would, which reads as the system finishing the step rather than stamping it.

const OUT = ease.out as [number, number, number, number]
const STILL = { duration: 0 } as const

export interface TaskStep {
  id: string
  label: string
  /** A right-aligned mono aside, revealed when the step completes: a duration, a count. */
  meta?: string
}

export type TaskStepStatus = "pending" | "active" | "done" | "failed"

export interface UseTaskStepsOptions {
  steps: TaskStep[]
  /** Index of the step running now. Everything before it is done; at steps.length the run is over. */
  current: number
  /** The run stopped at `current`. Nothing after that row pretends to have run. */
  failed?: boolean
}

export function useTaskSteps({ steps, current, failed = false }: UseTaskStepsOptions) {
  const complete = !failed && current >= steps.length
  const rows = steps.map((step, i) => ({
    ...step,
    status: (i < current
      ? "done"
      : i === current && failed
        ? "failed"
        : i === current && !complete
          ? "active"
          : "pending") as TaskStepStatus,
  }))
  const active = rows.find((row) => row.status === "active")
  const sentence = failed
    ? `Failed at ${steps[Math.min(current, steps.length - 1)]?.label ?? "step"}`
    : complete
      ? `All ${steps.length} steps complete`
      : active
        ? `${active.label}, step ${current + 1} of ${steps.length}`
        : ""

  return { rows, complete, failed, sentence }
}

function Check({ reduced }: { reduced: boolean }) {
  return (
    <svg viewBox="0 0 256 256" width="11" height="11" fill="none" aria-hidden>
      <motion.polyline
        points="216 72 104 184 48 128"
        stroke="currentColor"
        strokeWidth="26"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: reduced ? 0 : duration.settle, ease: OUT }}
      />
    </svg>
  )
}

function Cross() {
  return (
    <svg viewBox="0 0 256 256" width="10" height="10" fill="none" aria-hidden>
      <path d="M200 56 56 200 M56 56l144 144" stroke="currentColor" strokeWidth="26" strokeLinecap="round" />
    </svg>
  )
}

function Arc({ reduced }: { reduced: boolean }) {
  return (
    <motion.svg
      viewBox="0 0 16 16"
      className="size-3"
      aria-hidden
      animate={{ rotate: reduced ? 0 : 360 }}
      transition={reduced ? STILL : { duration: duration.coast / 2, ease: "linear", repeat: Infinity }}
    >
      <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeOpacity="0.25" strokeWidth="2" />
      <path d="M8 2 a6 6 0 0 1 6 6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </motion.svg>
  )
}

const TONE: Record<TaskStepStatus, string> = {
  done: "text-ink-soft",
  active: "font-medium text-ink",
  failed: "font-medium text-fail",
  pending: "text-faint",
}

export interface TaskStepsProps extends UseTaskStepsOptions {
  label?: string
  className?: string
}

export default function TaskSteps({
  steps,
  current,
  failed = false,
  label = "Task progress",
  className,
}: TaskStepsProps) {
  const { rows, complete, sentence } = useTaskSteps({ steps, current, failed })
  const reduced = useReducedMotion() === true
  const [spoken, setSpoken] = useState("")

  // One settled sentence per stage: a run that hops through three stages in a second is one
  // announcement, not three.
  useEffect(() => {
    if (!sentence) return
    const t = setTimeout(() => setSpoken(sentence), 500)
    return () => clearTimeout(t)
  }, [sentence])

  const badge = { duration: reduced ? 0 : duration.settle, ease: OUT }

  return (
    <div className={clsx("w-full", className)}>
      <ol aria-label={label} className="space-y-0.5">
        {rows.map((row) => (
          <li
            key={row.id}
            data-status={row.status}
            aria-current={row.status === "active" ? "step" : undefined}
            className="flex h-7 items-center gap-2.5 px-1"
          >
            <span className="relative grid size-4 shrink-0 place-items-center">
              <AnimatePresence initial={false}>
                {row.status === "done" ? (
                  <motion.span
                    key="done"
                    className="col-start-1 row-start-1 grid size-4 place-items-center rounded-[3px] bg-pass-wash text-pass"
                    initial={{ opacity: reduced ? 1 : 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, transition: STILL }}
                    transition={badge}
                  >
                    <Check reduced={reduced} />
                  </motion.span>
                ) : row.status === "failed" ? (
                  <motion.span
                    key="failed"
                    className="col-start-1 row-start-1 grid size-4 place-items-center rounded-[3px] bg-fail-wash text-fail"
                    initial={{ opacity: reduced ? 1 : 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, transition: STILL }}
                    transition={badge}
                  >
                    <Cross />
                  </motion.span>
                ) : row.status === "active" ? (
                  <motion.span
                    key="active"
                    className="col-start-1 row-start-1 text-accent"
                    initial={{ opacity: reduced ? 1 : 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, transition: STILL }}
                    transition={badge}
                  >
                    <Arc reduced={reduced} />
                  </motion.span>
                ) : (
                  <motion.span
                    key="pending"
                    className="col-start-1 row-start-1 size-[5px] rounded-[3px] bg-line"
                    initial={{ opacity: 1 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, transition: STILL }}
                    transition={STILL}
                  />
                )}
              </AnimatePresence>
            </span>

            <span className={clsx("mono-id min-w-0 flex-1 truncate transition-colors", TONE[row.status])}>
              {row.label}
            </span>

            {row.meta ? (
              <span
                aria-hidden={row.status !== "done"}
                className={clsx(
                  "mono-caption shrink-0 text-faint transition-opacity",
                  row.status === "done" ? "opacity-100" : "opacity-0",
                )}
              >
                {row.meta}
              </span>
            ) : null}
          </li>
        ))}
      </ol>
      <span role="status" className="sr-only">
        {spoken}
      </span>
      <span className="sr-only" aria-live={complete || failed ? "polite" : "off"}>
        {complete ? "Run complete" : failed ? "Run failed" : ""}
      </span>
    </div>
  )
}
