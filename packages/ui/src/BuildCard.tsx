import { useEffect, useState } from "react"
import clsx from "clsx"
import Icon from "./Icon"
import { ToolStepGroup } from "./ToolStepCard"
import { clock, elapsedLabel, rev } from "./format"
import type { BuildEvent, Finding } from "./types"

// One card per build: a mono strip with the verdict, the steps that got there,
// and the check results once it lands. Every value comes from the persisted
// BuildEvent, so a reload rebuilds the exact same card.

// The engine reports only what is wrong (fail and warn), so a passing build has
// nothing to list beyond the verdict, and a failed one leads with the count.
function ChecksSection({ findings, passed }: { findings: Finding[]; passed: boolean }) {
  const failed = findings.filter((f) => f.severity === "fail")
  const warned = findings.filter((f) => f.severity === "warn")
  const visible = passed ? warned : [...failed, ...warned]
  return (
    <ul className="flex flex-col gap-[5px]" role="list">
      {passed ? (
        <li className="flex items-center gap-2">
          <span className="text-pass"><Icon name="check" /></span>
          <span className="mono-id text-ink-soft uppercase [letter-spacing:0.06em]">Checks pass</span>
        </li>
      ) : failed.length > 0 ? (
        <li className="flex items-center gap-2">
          <span className="text-fail"><Icon name="xmark" /></span>
          <span className="mono-id text-ink-soft uppercase [letter-spacing:0.06em]">
            {failed.length} check{failed.length === 1 ? "" : "s"} failed
          </span>
        </li>
      ) : null}
      {visible.map((finding, index) => (
        <li key={`${finding.rule}-${index}`} className="flex items-baseline gap-2">
          <span className={clsx("flex h-[14px] items-center", finding.severity === "fail" ? "text-fail" : "text-warn")}>
            <Icon name="warning" />
          </span>
          <span className="mono-id shrink-0 text-ink-soft uppercase [letter-spacing:0.06em]">{finding.label || finding.rule}</span>
          <span className="min-w-0 text-xs leading-[14px] text-muted">{finding.message}</span>
        </li>
      ))}
    </ul>
  )
}

/** Live while building, frozen into the record after. */
function LiveClock({ startedAt }: { startedAt: string }) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 100)
    return () => clearInterval(timer)
  }, [])
  return <>{elapsedLabel(Math.max(0, (now - new Date(startedAt).getTime()) / 1000))}</>
}

export default function BuildCard({ build, collapsed }: { build: BuildEvent; collapsed?: boolean }) {
  const running = build.status === "running"
  const passed = build.status === "passed"
  const word = running ? "Building" : passed ? "Built" : "Failed"
  // A crash has no findings to explain it, so the traceback's last line speaks.
  const errorLine = build.status === "error" ? build.error?.trim().split("\n").pop() || "Something broke on my end." : null
  const strip = [
    build.revision != null ? rev(build.revision) : null,
    running ? <LiveClock key="clock" startedAt={build.started_at} /> : build.elapsed_s != null ? clock(build.elapsed_s) : null,
  ].filter((part) => part != null)

  return (
    <div className="flex flex-col overflow-hidden rounded-[6px] border border-line">
      <div className="chrome flex h-[30px] items-center justify-between border-b border-line-soft bg-raised px-3">
        <span className="mono-label flex items-center gap-2 text-ink">
          {passed ? (
            <span className="text-pass"><Icon name="check" /></span>
          ) : running ? null : (
            <span className="text-fail"><Icon name="xmark" /></span>
          )}
          {word}
        </span>
        <span className="mono-caption text-muted [letter-spacing:0.06em]">
          {strip.map((part, index) => (
            <span key={index}>{index > 0 ? " · " : ""}{part}</span>
          ))}
        </span>
      </div>

      <div className="flex flex-col gap-[9px] px-3 pt-2.5 pb-3">
        {build.steps.length > 0 ? <ToolStepGroup steps={build.steps} defaultCollapsed={collapsed ?? passed} /> : null}

        {/* The four views the engine drew, so the transcript shows what the build made. */}
        {!running && build.render_url ? (
          <img
            src={build.render_url}
            alt={`${build.part_name} from four sides`}
            className="w-full rounded-[4px] border border-line-soft bg-raised"
          />
        ) : null}

        {!running && build.findings.length > 0 ? (
          <ChecksSection findings={build.findings} passed={passed} />
        ) : null}

        {errorLine ? <p className="text-[13px] leading-[19px] text-ink-soft">{errorLine}</p> : null}
      </div>
    </div>
  )
}
