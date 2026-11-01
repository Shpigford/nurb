import { useMemo, useState } from "react"
import clsx from "clsx"
import {
  AssistantMarkdown,
  BuildCard,
  ExportMenu,
  Icon,
  MeasurementCard,
  ParamsPanel,
  SpecCard,
  ToolStepGroup,
  ViewerIsland,
  rev,
  type ExportFormat,
  type Param,
  type Params,
} from "../src/index"
import {
  buildPassed,
  flaggedFindings,
  groupSteps,
  markdownFixture,
  measurementRecorded,
  panelParams,
  panelStats,
  specFixture,
} from "./fixtures"

const REVISION = 27
// The header dot is the verdict of the same findings the rail lists.
const WORST = flaggedFindings.some((f) => f.severity === "fail") ? "fail" : flaggedFindings.length ? "warn" : "pass"

// The export is fixture-driven: nothing is built, and the delay is only there so
// the menu's preparing row is reachable.
const fakeExport = (_format: ExportFormat): Promise<void> => new Promise((resolve) => setTimeout(resolve, 1500))

function severityText(severity: string) {
  return severity === "fail" ? "text-fail" : "text-warn"
}

function Findings({
  highlight,
  onHighlight,
}: {
  highlight: number | null
  onHighlight: (index: number | null) => void
}) {
  const counts = useMemo(() => {
    const fail = flaggedFindings.filter((f) => f.severity === "fail").length
    return { fail, warn: flaggedFindings.length - fail }
  }, [])
  const [open, setOpen] = useState(counts.fail > 0)

  if (flaggedFindings.length === 0) {
    return (
      <p className="mono-caption py-1 text-center text-muted">Nothing to fix. Checks pass at these numbers.</p>
    )
  }

  const worst = counts.fail > 0 ? "fail" : "warn"
  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="chrome flex items-center justify-between gap-2 text-left"
      >
        <span className="flex items-center gap-2">
          <span className={severityText(worst)}>
            <Icon name={counts.fail > 0 ? "xmark" : "warning"} />
          </span>
          <span className="mono-id uppercase text-ink-soft [letter-spacing:0.08em]">
            {counts.fail} fail · {counts.warn} warn
          </span>
        </span>
        <span className={clsx("text-muted", !open && "-rotate-90")}>
          <Icon name="chevron-down" />
        </span>
      </button>

      {open ? (
        <ul className="flex max-h-64 flex-col gap-1.5 overflow-y-auto">
          {flaggedFindings.map((f, i) => (
            <li key={i}>
              <button
                type="button"
                aria-pressed={i === highlight}
                onClick={() => onHighlight(i === highlight ? null : i)}
                className={clsx(
                  "flex w-full items-baseline gap-2 rounded-control px-2 py-1 text-left transition-colors",
                  i === highlight ? "bg-accent-wash" : "hover:bg-raised"
                )}
              >
                <span className={clsx("mono-id shrink-0 uppercase [letter-spacing:0.06em]", severityText(f.severity))}>
                  {f.label || f.rule}
                </span>
                <span className="text-xs leading-4 text-muted">{f.message}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}

function Transcript() {
  return (
    <div className="flex w-[372px] shrink-0 flex-col gap-3 overflow-y-auto p-4 panel min-h-0 max-lg:order-last max-lg:w-full">
      <p className="text-chat ml-8 rounded-content bg-raised px-3 py-2 text-ink">
        I need a shelf that clips onto the rail and holds four gridfinity bins.
      </p>
      <SpecCard spec={specFixture} model="claude-fable-5" effort="low" />
      <div className="text-chat text-ink-soft">
        <AssistantMarkdown content={markdownFixture} />
      </div>
      <ToolStepGroup steps={groupSteps} />
      <MeasurementCard measurement={measurementRecorded} />
      <BuildCard build={buildPassed} />
    </div>
  )
}

// The reference layout the local workbench page and the desktop app both copy: transcript,
// stage, rail. Every side is fixture-driven, so Apply and Download are local state.
export default function Workbench() {
  const [params, setParams] = useState<Param[]>(panelParams)
  const [values, setValues] = useState<Params>({})
  const [highlight, setHighlight] = useState<number | null>(null)
  const [applied, setApplied] = useState<string | null>(null)

  return (
    <section data-section="Workbench" className="mt-10 px-8">
      <h2 className="mono-label chrome mb-2 text-muted">Workbench</h2>
      <div className="mx-auto flex h-[760px] w-full max-w-[1320px] flex-col gap-4 max-lg:h-auto">
        <header className="panel chrome flex h-[52px] shrink-0 items-center gap-3 px-4">
          <span className={clsx("size-2 shrink-0 rounded-full", WORST === "fail" ? "bg-fail" : WORST === "warn" ? "bg-warn" : "bg-pass")} />
          <span className="mono-value text-ink">shelf_gridfinity</span>
          <span className="mono-caption text-muted">
            {WORST === "fail" ? "Checks found something to fix" : "Checks ran at these numbers"}
          </span>
          <span className="mono-caption ml-auto text-muted">{rev(REVISION)}</span>
        </header>

        <div className="flex min-h-0 flex-1 gap-4 max-lg:flex-col">
          <Transcript />

          <div className="min-w-0 flex-1 max-lg:order-first max-lg:h-[420px]">
            <ViewerIsland
              glbUrl="/flagged.glb"
              findings={flaggedFindings}
              highlight={highlight}
              onHighlight={setHighlight}
              bed={[256, 256]}
              className="h-full"
            />
          </div>

          <div className="panel flex w-[288px] shrink-0 flex-col overflow-hidden max-lg:w-full">
            <h3 className="mono-label chrome px-4 pt-3.5 text-muted">Parameters</h3>
            <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
              <ParamsPanel
                params={params}
                values={values}
                onChange={(next) => {
                  setValues(next)
                  setApplied(null)
                }}
                onApply={(edited) => {
                  // What a host does: the edited values become the declared defaults,
                  // so nothing is dirty any more.
                  setParams((prior) => prior.map((p) => (p.name in edited ? { ...p, default: edited[p.name] } : p)))
                  setValues({})
                  setApplied(`Saved ${Object.keys(edited).join(", ")} as the part's defaults.`)
                }}
                stats={panelStats}
                note={applied}
              />
            </div>
            <div className="flex shrink-0 flex-col gap-3 border-t border-line bg-ground px-4 pt-3.5 pb-4">
              <Findings highlight={highlight} onHighlight={setHighlight} />
              <div className="flex gap-2">
                <ExportMenu
                  partId="shelf-bracket"
                  export={fakeExport}
                  status={{ state: "succeeded", grams: 42.4, seconds: 5400 }}
                  revision={REVISION}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
