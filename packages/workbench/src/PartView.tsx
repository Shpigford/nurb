import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react"
import {
  BuildFailedBanner,
  Button,
  EmptyProject,
  ExportMenu,
  FindingsList,
  FloatingHeader,
  HeaderDivider,
  HeaderIcons,
  HeaderStack,
  HeaderStatus,
  Icon,
  Lockup,
  Menu,
  ParamRail,
  ParamsPanel,
  RailDisclosure,
  Stage,
  StageColumn,
  StageNotice,
  ViewerIsland,
  cue,
  elapsedLabel,
  rev,
  type BuildStats,
  type CameraState,
  type ExportFormat,
  type ExportStatus,
  type HeaderTone,
  type Param,
  type Params,
  type PinnedParam,
} from "@nurb/ui"
import {
  absolute,
  applyParams,
  buildWithParams,
  exportPart,
  type ApplyResult,
  type PartBuild,
  type Project,
  type SliceResult,
} from "./api"
import { activity } from "./activity"
import { loadCamera, saveCamera } from "./camera"
import Slice from "./Slice"
import { verdictOf, type Verdict } from "./verdict"

// A drag lands many values a second; one rebuild per quarter second is the most a
// real part can keep up with.
const DEBOUNCE_MS = 250

// Board 10's purge line greets the first part anyone ever builds on this machine,
// and only that one. Reading and claiming the key in one step means two builds
// landing together cannot both think they were first.
const FIRST_BUILD_KEY = "nurb-first-build"

function claimFirstBuild(): boolean {
  try {
    if (localStorage.getItem(FIRST_BUILD_KEY) !== null) return false
    localStorage.setItem(FIRST_BUILD_KEY, new Date().toISOString())
    return true
  } catch {
    // A locked-down webview just never gets the greeting.
    return false
  }
}

// The header says the state in two words. The sentence belongs in the rail, where
// there is room for it.
const STATUS_LABEL: Record<Verdict, string> = {
  pass: "CHECKS PASS",
  warn: "NEEDS A LOOK",
  fail: "FAILED",
  none: "NOT BUILT",
}

function bedOf(project: Project | null): [number, number] | null {
  const bed = project?.printer?.bed
  return Array.isArray(bed) && bed.length >= 2 ? [Number(bed[0]), Number(bed[1])] : null
}

function lastLine(text: string): string {
  const lines = text.trim().split("\n")
  return lines[lines.length - 1] || text
}

// How long the run on screen took, so the header's detail is about this geometry.
function buildSeconds(build: PartBuild | null): number | null {
  if (!build?.started_at || !build.finished_at) return null
  const seconds = (new Date(build.finished_at).getTime() - new Date(build.started_at).getTime()) / 1000
  return Number.isFinite(seconds) && seconds >= 0 ? seconds : null
}

// The footer's g/hr readouts and the SLICE row are the same two numbers, so the
// cached price on the part seeds both. Without this the row read them off the part
// payload and the readouts above it reverted to dashes on every load.
function seedStatus(slice: SliceResult | null | undefined): ExportStatus | null {
  if (slice?.kind !== "slice") return null
  return { state: "succeeded", grams: slice.grams, seconds: slice.seconds }
}

// One change is worth naming, because the user wants to see it landed where they put
// it. Several are worth counting, because the list would be longer than the rail.
function applyNote(result: ApplyResult, params: Param[], diff: Params): string {
  const written = result.written
  let note: string
  if (written.length === 0) {
    note = "Nothing to save."
  } else if (written.length === 1) {
    const name = written[0]
    const before = params.find((p) => p.name === name)?.default
    note = `Saved as rev ${result.revision}. ${name} ${before} → ${diff[name]}`
  } else {
    note = `Saved as rev ${result.revision}. ${written.length} changes.`
  }
  if (result.skipped.length > 0) note += ` ${result.skipped[0].why}`
  return note
}

export default function PartView({
  project,
  partName,
  onSelectPart,
  header,
  chat,
  topInset,
  dragRegion,
  onManagePrinters,
}: {
  project: Project | null
  partName: string | null
  /** The header's part switcher changes parts, and whoever owns the selection is told. */
  onSelectPart?: (name: string) => void
  /** What the host adds to the floating header: the project picker, its own icons.
   * `before` sits ahead of the lockup (the desktop's traffic lights), `nav` between
   * the lockup and the part name (the way back), `start` after it (the served page's
   * project picker). */
  header?: {
    before?: ReactNode
    nav?: ReactNode
    start?: ReactNode
    end?: ReactNode
  }
  /** The conversation column, 372 wide, left of the stage. */
  chat?: ReactNode
  /** Room for a window titlebar above the header. */
  topInset?: number
  /** The desktop drags its window by the stage and the header bar. */
  dragRegion?: boolean
  /** Opens the app's Settings screen, where the bench is managed. The served page has none. */
  onManagePrinters?: () => void
}) {
  const projectId = project?.id ?? null
  const [highlight, setHighlight] = useState<number | null>(null)
  const [camera, setCamera] = useState<CameraState | null>(null)

  const [values, setValues] = useState<Params>({})
  const [building, setBuilding] = useState(false)
  const [applying, setApplying] = useState(false)
  const [note, setNote] = useState<string | null>(null)
  const [buildError, setBuildError] = useState<string | null>(null)
  const [sliceStatus, setSliceStatus] = useState<ExportStatus | null>(null)
  const [settleKey, setSettleKey] = useState(0)
  const [purge, setPurge] = useState(false)

  const [checksOpen, setChecksOpen] = useState(false)
  const [sliceOpen, setSliceOpen] = useState(false)
  const [measurementsOpen, setMeasurementsOpen] = useState(false)
  // Once the user has opened or closed a row themselves, the part's own answer stops
  // overruling them.
  const touched = useRef({ checks: false, slice: false })

  const paramsSeq = useRef(0)
  const paramsTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const paramsAbort = useRef<AbortController | null>(null)
  const objectUrl = useRef<string | null>(null)

  const parts = project?.parts ?? []
  const part = parts.find((p) => p.name === partName) ?? parts[0] ?? null
  const build = part?.build ?? null
  const verdict = verdictOf(build)
  const glbUrl = build?.glb_url ?? null
  const runId = build?.id ?? null
  const findings = build?.findings ?? []
  const failedBuild = build?.status === "error"

  const hasFindings = findings.length > 0

  // The two cues a build is allowed to make, and the one flourish on a pass. Both
  // fire only when the build happened while the user was watching: opening a part
  // that was already built is not news, and a warn is not worth a sound either.
  const wasBuilding = useRef(false)
  useEffect(() => {
    const was = wasBuilding.current
    wasBuilding.current = building
    if (!was || building) return
    if (verdict === "fail") {
      cue("error")
      return
    }
    if (verdict !== "pass") return
    cue("ready")
    setSettleKey((n) => n + 1)
    if (claimFirstBuild()) setPurge(true)
  }, [building, verdict])
  const hasSlice = Boolean(build?.slice)

  // Another part is another question, so the rows go back to answering it themselves.
  useEffect(() => {
    touched.current = { checks: false, slice: false }
  }, [part?.id])

  // A row opens on the part that has something to say there: findings, a price. The row
  // itself is always in the rail, so a closed one is still one click away.
  useEffect(() => {
    if (!touched.current.checks) setChecksOpen(hasFindings)
    if (!touched.current.slice) setSliceOpen(hasSlice)
  }, [part?.id, hasFindings, hasSlice])

  // The stored view is the proof a rebuild did not move the camera.
  useEffect(() => {
    if (!projectId || !part) {
      setCamera(null)
      return
    }
    setCamera(loadCamera(projectId, part.name))
    setHighlight(null)
  }, [projectId, part?.name])

  // A part carries the overrides its newest run was built at, so the sliders open
  // where they were left rather than back at the declared defaults.
  useEffect(() => {
    paramsSeq.current += 1
    paramsAbort.current?.abort()
    if (paramsTimer.current) clearTimeout(paramsTimer.current)
    setValues(part?.overrides ?? {})
    setNote(null)
    setBuildError(null)
    setBuilding(false)
    // The child's own effect runs before this one, so clearing here would wipe the
    // price it just reported and leave the readouts disagreeing with the row.
    setSliceStatus(seedStatus(part?.build?.slice))
  }, [projectId, part?.name])

  // A rebuild queued by the last drag is about a part nobody is looking at any more,
  // so the timer and the request leave with the view.
  useEffect(() => {
    return () => {
      if (paramsTimer.current) clearTimeout(paramsTimer.current)
      paramsAbort.current?.abort()
    }
  }, [])

  // A prepared download is about the geometry it came from, so it goes when that
  // does, and when the page does.
  useEffect(() => {
    return () => {
      if (objectUrl.current) {
        URL.revokeObjectURL(objectUrl.current)
        objectUrl.current = null
      }
    }
  }, [part?.id, runId])

  const sendParams = useCallback(async (partId: string, next: Params) => {
    const seq = ++paramsSeq.current
    paramsAbort.current?.abort()
    const controller = new AbortController()
    paramsAbort.current = controller
    setBuilding(true)
    try {
      const { build: answer } = await buildWithParams(partId, next, controller.signal)
      if (seq !== paramsSeq.current) return
      setBuildError(answer.status === "error" && answer.error ? lastLine(answer.error) : null)
    } catch (failure) {
      // A superseded drag cancels its own request; that is not a failure to report.
      if ((failure as Error | null)?.name === "AbortError" || seq !== paramsSeq.current) return
      setBuildError(failure instanceof Error ? failure.message : "The rebuild did not finish.")
    } finally {
      if (seq === paramsSeq.current) setBuilding(false)
    }
  }, [])

  const onParamsChange = useCallback(
    (next: Params) => {
      setValues(next)
      setNote(null)
      const partId = part?.id
      if (!partId) return
      if (paramsTimer.current) clearTimeout(paramsTimer.current)
      paramsTimer.current = setTimeout(() => void sendParams(partId, next), DEBOUNCE_MS)
    },
    [part?.id, sendParams]
  )

  const onApply = useCallback(
    async (diff: Params) => {
      if (!part) return
      setApplying(true)
      setNote(null)
      try {
        const result = await applyParams(part.id, diff)
        // The refetch brings the new defaults, so nothing is dirty any more.
        setValues({})
        setNote(applyNote(result, part.params, diff))
      } catch (failure) {
        setNote(failure instanceof Error ? failure.message : "The values did not save.")
      } finally {
        setApplying(false)
      }
    },
    [part?.id, part?.params]
  )

  const runExport = useCallback(
    async (format: ExportFormat) => {
      if (!part) throw new Error("There is no part to download yet.")
      const filename = `${part.name}.${format}`
      const id = `export-${part.id}-${format}-${Date.now()}`
      activity({ id, title: `Exporting ${filename}`, tone: "working" })
      try {
        const blob = await exportPart(part.id, format, values)
        if (objectUrl.current) URL.revokeObjectURL(objectUrl.current)
        objectUrl.current = URL.createObjectURL(blob)
        activity({ id, title: `Exporting ${filename}`, detail: "Saved", tone: "done" })
        return { url: objectUrl.current, filename }
      } catch (failure) {
        activity({
          id,
          title: `Exporting ${filename}`,
          detail: failure instanceof Error ? failure.message : "The export did not finish.",
          tone: "fail",
        })
        throw failure
      }
    },
    [part?.id, part?.name, values]
  )

  const onCamera = useCallback(
    (state: CameraState) => {
      if (projectId && part) saveCamera(projectId, part.name, state)
      setCamera(state)
    },
    [projectId, part?.name]
  )

  // The build records its bounding box; the panel's footer reads a size.
  const stats = useMemo<BuildStats | null>(() => {
    const raw = build?.stats
    if (!raw) return null
    return { ...raw, size_mm: (raw.size_mm as BuildStats["size_mm"]) ?? raw.bbox }
  }, [build?.stats])

  // A dimension the spec fixed and the part named is not the user's to drag, so the
  // rail shows it locked instead of as a slider.
  const locked = useMemo(() => {
    const names = new Set((part?.params ?? []).map((p) => p.name))
    return new Set((project?.spec?.dimensions ?? []).map((d) => d.name).filter((name) => names.has(name)))
  }, [project?.spec, part?.params])

  // The spec fixed the name; the part holds the number, so the row reads the part.
  const pinned = useMemo<PinnedParam[]>(
    () =>
      (part?.params ?? [])
        .filter((p) => locked.has(p.name))
        .map((p) => ({ name: p.name, value: `${values[p.name] ?? p.default} mm` })),
    [part?.params, locked, values]
  )

  // Instead of, not as well as: a pinned dimension listed above and offered as a
  // slider below would be the same number twice, and only one of them locked.
  const draggable = useMemo<Param[]>(
    () => (part?.params ?? []).filter((p) => !locked.has(p.name)),
    [part?.params, locked]
  )

  const counts = useMemo(() => {
    const fail = findings.filter((f) => f.severity === "fail").length
    return { fail, warn: findings.length - fail }
  }, [findings])

  const heightMm = stats?.size_mm?.[2] ?? null
  const seconds = buildSeconds(build)
  const detail = [rev(part?.revision ?? 0), seconds == null ? null : elapsedLabel(seconds)]
    .filter(Boolean)
    .join(" · ")
  const tone: HeaderTone = building ? "building" : verdict

  const headerEl = (
    <FloatingHeader
      dragRegion={dragRegion}
      start={
        <>
          {header?.before}
          <div className="flex h-full items-center px-4">
            <Lockup />
          </div>
          <HeaderDivider />
        </>
      }
      cells={
        <>
          {header?.nav ? (
            <>
              {header.nav}
              <HeaderDivider />
            </>
          ) : null}
          {/* The part is the unit, so it is what the header names. A part that has
           * no source yet wears its container's placeholder name until it has one. */}
          <HeaderStack
            label="PART"
            value={part?.name ?? (project && !project.folder ? project.name : "No part yet")}
          />
          <HeaderDivider />
          {header?.start ? (
            <>
              {header.start}
              <HeaderDivider />
            </>
          ) : null}
          <HeaderStatus tone={tone} label={building ? "BUILDING" : STATUS_LABEL[verdict]} detail={detail} />
        </>
      }
      end={
        <>
          {/* One cell names the project and opens its parts, because a row of tabs
           * runs off the header once a project holds a dozen. */}
          {project && parts.length > 1 ? (
            <Menu
              label={`Parts in ${project.name}`}
              portal
              filter={parts.length > 8 ? "Find a part" : undefined}
              menuClassName="w-[260px] max-h-[min(420px,70vh)] overflow-y-auto!"
              triggerClassName="h-[50px] rounded-none border-l border-line"
              trigger={(open) => (
                <span
                  className={
                    open
                      ? "flex h-full items-center gap-2 bg-raised px-3.5 text-ink"
                      : "flex h-full items-center gap-2 px-3.5 text-muted transition-colors hover:text-ink"
                  }
                >
                  <Icon name="folder" />
                  <span className="mono-label">In {project.name}</span>
                  <Icon name="chevron-down" />
                </span>
              )}
              items={parts.map((p) => ({
                label: p.name,
                checked: p.name === part?.name,
                onSelect: () => onSelectPart?.(p.name),
              }))}
            />
          ) : null}
          {header?.end ? <HeaderIcons>{header.end}</HeaderIcons> : null}
        </>
      }
    />
  )

  return (
    <Stage header={headerEl} topInset={topInset} dragRegion={dragRegion}>
      {chat}

      <StageColumn>
        {/* The column is the package's; the geometry on it is what the tests read. */}
        <div
          data-testid="stage"
          data-glb-url={glbUrl ?? ""}
          className="relative flex min-h-0 min-w-0 flex-1 flex-col"
        >
        {glbUrl ? (
          <ViewerIsland
            key={part?.id}
            glbUrl={absolute(glbUrl)}
            findings={findings}
            highlight={highlight}
            onHighlight={setHighlight}
            bed={bedOf(project)}
            camera={camera}
            settleKey={settleKey}
            purge={purge}
            onCamera={onCamera}
            className="min-h-0 flex-1"
          />
        ) : (
          <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-4">
            <EmptyProject
              title={part ? (failedBuild ? `${part.name} did not build` : `${part.name} is not built yet`) : "No part yet"}
              caption={
                !part
                  ? "It builds here, live, the moment the spec is pinned."
                  : failedBuild
                    ? "The rail says what went wrong. Change a value or ask for a fix, and it rebuilds."
                    : "Build it once and it appears here. Dragging a parameter rebuilds it from then on."
              }
            />
            {part && !build ? (
              <>
                <Button
                  variant="accent"
                  size="md"
                  disabled={building}
                  onClick={() => void sendParams(part.id, {})}
                >
                  {building ? "Building…" : `Build ${part.name}`}
                </Button>
                {buildError ? <p className="mono-caption max-w-sm text-center text-fail">{buildError}</p> : null}
              </>
            ) : null}
          </div>
        )}
        {failedBuild ? (
          <StageNotice>
            {build?.shown_revision != null ? `Showing ${rev(build.shown_revision)} · ` : ""}
            {rev(part?.revision ?? 0)} did not build
          </StageNotice>
        ) : null}
        </div>
      </StageColumn>

      {/* Sheet 30: an empty project has no rail; the stage runs to the edge. */}
      {part ? (
        <ParamRail
          count={part?.params?.length ?? 0}
          pinned={pinned}
          params={
            <>
              <BuildFailedBanner
                open={failedBuild}
                revision={part?.revision ?? 0}
                shownRevision={build?.shown_revision ?? null}
              />
              <ParamsPanel
                params={draggable}
                values={values}
                onChange={onParamsChange}
                onApply={(diff) => void onApply(diff)}
                building={building}
                applying={applying}
                stats={stats}
                measurements={project?.measurements}
                error={buildError ?? (failedBuild && build?.error ? lastLine(build.error) : null)}
                note={note}
              />
            </>
          }
          readouts={{
            grams: sliceStatus?.state === "succeeded" ? (sliceStatus.grams ?? null) : null,
            seconds: sliceStatus?.state === "succeeded" ? (sliceStatus.seconds ?? null) : null,
            heightMm,
          }}
          warnCount={counts.warn}
          failCount={counts.fail}
          disclosures={
            <>
              <RailDisclosure
                label="CHECKS"
                tone={verdict}
                summary={findings.length === 0 ? undefined : `${counts.fail} fail · ${counts.warn} warn`}
                open={checksOpen}
                onToggle={() => {
                  touched.current.checks = true
                  setChecksOpen((v) => !v)
                }}
              >
                <FindingsList
                  findings={findings}
                  verdict={verdict}
                  highlight={highlight}
                  onHighlight={setHighlight}
                />
              </RailDisclosure>

              <RailDisclosure
                label="SLICE"
                summary={(project?.printers ?? []).length === 0 ? "NO PRINTER" : undefined}
                open={sliceOpen}
                onToggle={() => {
                  touched.current.slice = true
                  setSliceOpen((v) => !v)
                }}
              >
                <div className="px-4 py-2">
                  {part && projectId ? (
                    <Slice
                      key={`slice-${part.id}`}
                      partId={part.id}
                      projectId={projectId}
                      printer={project?.printer?.name ?? null}
                      runId={runId}
                      seed={build?.slice ?? null}
                      onStatus={setSliceStatus}
                      onManagePrinters={onManagePrinters}
                    />
                  ) : (
                    <p className="mono-caption text-muted">Build the part first.</p>
                  )}
                </div>
              </RailDisclosure>
              {/* The numbers someone measured are standing reference, so they keep a surface in the rail. */}
              {project && project.measurements.length > 0 ? (
                <RailDisclosure
                  label="MEASUREMENTS"
                  summary={String(project.measurements.length)}
                  open={measurementsOpen}
                  onToggle={() => setMeasurementsOpen((v) => !v)}
                >
                  <ul className="flex flex-col gap-1 px-4 py-2">
                    {project.measurements.map((m) => (
                      <li key={m.name} className="flex items-baseline gap-2">
                        <span className="mono-label truncate text-muted">{m.name}</span>
                        <span className="flex-1" />
                        <span className="mono-value text-ink">
                          {m.provisional ? "~" : ""}
                          {m.value_mm} {m.unit ?? "mm"}
                        </span>
                        <span className="mono-caption w-16 truncate text-right text-faint" title={m.how}>
                          {m.how}
                        </span>
                      </li>
                    ))}
                  </ul>
                </RailDisclosure>
              ) : null}
            </>
          }
          actions={
            <div className="flex w-full gap-2">
              {part ? (
                <ExportMenu
                  key={`export-${part.id}`}
                  partId={part.id}
                  export={runExport}
                  status={sliceStatus}
                  revision={part.revision}
                  runId={runId}
                />
              ) : null}
            </div>
          }
        />
      ) : null}
    </Stage>
  )
}
