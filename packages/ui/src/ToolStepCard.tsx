import { useEffect, useId, useState, type ReactNode } from "react"
import { motion, useReducedMotion } from "motion/react"
import clsx from "clsx"
import Icon from "./Icon"
import { elapsedLabel } from "./format"
import { useAutoHeight } from "./motion/useAutoHeight"
import { duration, ease } from "./motion/tokens"
import type { ToolStep } from "./types"

// One tool call as a row: verb, object, elapsed. Liveness is the counter, never a
// spinner, so a stalled run reads as stalled rather than busy.

const ICON_FOR: Record<ToolStep["status"], "check" | "warning" | "ruler"> = {
  done: "check",
  failed: "warning",
  running: "ruler",
}

// A landed step with no recorded time (an interrupted run) reads 0.0s rather than
// the wall clock since it started, which would grow on every render.
function seconds(step: ToolStep, now: number): number {
  if (step.status !== "running") return step.elapsed_s ?? 0
  return Math.max(0, (now - new Date(step.started_at).getTime()) / 1000)
}

/** The only part of a running row that re-renders, so the tick stays cheap. */
function Elapsed({ startedAt, className }: { startedAt: string; className?: string }) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 100)
    return () => clearInterval(timer)
  }, [])
  const s = Math.max(0, (now - new Date(startedAt).getTime()) / 1000)
  return <span aria-hidden="true" className={className}>{elapsedLabel(s)}</span>
}

/** The disclosure arrow. It turns at the tick, the shortest step we have. */
function Chevron({ open }: { open: boolean }) {
  const reduced = useReducedMotion() === true
  return (
    <motion.span
      aria-hidden="true"
      className="flex shrink-0 items-center text-faint"
      animate={{ rotate: open ? 0 : -90 }}
      transition={{ duration: reduced ? 0 : duration.tick, ease: ease.out as [number, number, number, number] }}
    >
      <Icon name="chevron-down" />
    </motion.span>
  )
}

/**
 * The detail travels to a measured height and then settles back to auto. The
 * children stay unmounted while it is shut, so a closed row holds no text: the
 * wrapper is what is measured, and it is empty until the row opens.
 */
function Expand({ open, id, className, children }: { open: boolean; id: string; className?: string; children: ReactNode }) {
  const h = useAutoHeight(open)
  return (
    <motion.div id={id} style={h.style} animate={h.animate} transition={h.transition} onAnimationComplete={h.onAnimationComplete}>
      <div ref={h.ref} className={className}>
        {open ? children : null}
      </div>
    </motion.div>
  )
}

function describe(step: ToolStep): string {
  const head = `${step.verb.charAt(0).toUpperCase()}${step.verb.slice(1)} ${step.object}`
  if (step.status === "running") {
    return `${head}, running for ${Math.round(seconds(step, Date.now()))} seconds`
  }
  const s = seconds(step, Date.now()).toFixed(1)
  return `${head}, ${step.status === "failed" ? "failed after" : "finished in"} ${s} seconds`
}

export function ToolStepCard({ step, defaultOpen }: { step: ToolStep; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen ?? step.status === "failed")
  // A live step arrives running and flips to failed later; the failure must open then.
  useEffect(() => {
    if (step.status === "failed") setOpen(true)
  }, [step.status])
  const bodyId = useId()
  const running = step.status === "running"
  const failed = step.status === "failed"
  const input = step.input == null ? null : JSON.stringify(step.input, null, 2)
  const output = step.output?.trim() ? step.output : null
  const expandable = input != null || output != null

  return (
    <div className="flex flex-col">
      <button
        type="button"
        onClick={expandable ? () => setOpen((v) => !v) : undefined}
        aria-expanded={expandable ? open : undefined}
        aria-controls={expandable ? bodyId : undefined}
        className={clsx(
          "flex min-h-[28px] w-full items-center gap-2 rounded-[3px] px-2 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
          failed ? "bg-fail-wash" : running ? "bg-accent-wash" : "bg-transparent",
          expandable && !failed && !running && "hover:bg-raised",
          !expandable && "cursor-default"
        )}
      >
        <span aria-hidden="true" className={clsx("flex shrink-0 items-center", failed ? "text-fail" : "text-ink-soft")}>
          <Icon name={ICON_FOR[step.status]} />
        </span>
        <span aria-hidden="true" className={clsx("mono-label shrink-0", failed ? "text-fail" : "text-muted")}>
          {step.verb.toUpperCase()}
        </span>
        <span aria-hidden="true" className="min-w-0 flex-1 truncate text-[13px] leading-[19px] text-ink-soft">
          {step.object}
        </span>
        {running ? (
          <Elapsed startedAt={step.started_at} className="mono-value min-w-[44px] shrink-0 text-right tabular-nums text-accent-ink" />
        ) : (
          <span aria-hidden="true" className="mono-value min-w-[44px] shrink-0 text-right tabular-nums text-faint">
            {elapsedLabel(seconds(step, Date.now()))}
          </span>
        )}
        {expandable ? <Chevron open={open} /> : null}
        <span className="sr-only">{describe(step)}</span>
      </button>

      <Expand open={open && expandable} id={bodyId} className="relative flex flex-col gap-1.5 pt-1.5 pr-2 pb-2.5 pl-7">
        <span aria-hidden="true" className="absolute top-0 bottom-0 left-[13px] w-px bg-line-soft" />
        {input ? (
          <div className="flex flex-col gap-1">
            <span className="mono-label text-muted">INPUT</span>
            <pre className="max-h-[216px] overflow-y-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap text-ink-soft">
              {input}
            </pre>
          </div>
        ) : null}
        {output ? (
          <div className="flex flex-col gap-1">
            <span className="mono-label text-muted">OUTPUT</span>
            <pre className="max-h-[216px] overflow-y-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] break-words whitespace-pre-wrap text-ink-soft">
              {output}
            </pre>
          </div>
        ) : null}
      </Expand>
    </div>
  )
}

type Run = { kind: "group"; steps: ToolStep[] } | { kind: "step"; step: ToolStep }

// Three consecutive finished steps are a paragraph, not three sentences. Two are
// still worth reading one by one, so the threshold is three.
function runs(steps: ToolStep[]): Run[] {
  const out: Run[] = []
  let done: ToolStep[] = []
  const flush = () => {
    if (done.length >= 3) out.push({ kind: "group", steps: done })
    else done.forEach((step) => out.push({ kind: "step", step }))
    done = []
  }
  for (const step of steps) {
    if (step.status === "done") {
      done.push(step)
      continue
    }
    flush()
    out.push({ kind: "step", step })
  }
  flush()
  return out
}

function Group({ steps, defaultCollapsed }: { steps: ToolStep[]; defaultCollapsed: boolean }) {
  const [open, setOpen] = useState(!defaultCollapsed)
  const bodyId = useId()
  useEffect(() => {
    if (defaultCollapsed) setOpen(false)
  }, [defaultCollapsed])
  const total = steps.reduce((sum, step) => sum + seconds(step, Date.now()), 0)

  return (
    <div className="flex flex-col">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={bodyId}
        className="flex min-h-[28px] items-center gap-2 self-start rounded-[3px] px-2 hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
      >
        <span aria-hidden="true" className="flex shrink-0 items-center text-ink-soft">
          <Icon name="dots" />
        </span>
        <span className="mono-label text-muted">{steps.length} STEPS</span>
        <span className="mono-value text-faint">
          <span aria-hidden="true">· </span>
          {elapsedLabel(total)}
        </span>
        <span aria-hidden="true" className="ml-1.5 flex items-center">
          <Chevron open={open} />
        </span>
      </button>
      <Expand open={open} id={bodyId} className="flex flex-col gap-[2px]">
        {steps.map((step) => (
          <ToolStepCard key={step.id} step={step} />
        ))}
      </Expand>
    </div>
  )
}

export function ToolStepGroup({ steps, defaultCollapsed = true }: { steps: ToolStep[]; defaultCollapsed?: boolean }) {
  return (
    <div className="flex flex-col gap-[2px]">
      {runs(steps).map((run) =>
        run.kind === "group" ? (
          <Group key={run.steps[0].id} steps={run.steps} defaultCollapsed={defaultCollapsed} />
        ) : (
          <ToolStepCard key={run.step.id} step={run.step} />
        )
      )}
    </div>
  )
}

export default ToolStepCard
