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
  StageBuilding,
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
  type ViewerAnchor,
} from "@nurb/ui"
import {
  absolute,
  applyParams,
  buildWithParams,
  deleteLabel,
  exportPart,
  fetchPrinters,
  renameLabel,
  renamePart,
  setLabel,
  slicerName,
  type ApplyResult,
  type PartBuild,
  type Project,
  type SliceResult,
} from "./api"
import { activity } from "./activity"
import { loadCamera, saveCamera } from "./camera"
import { LabelEditor, LabelTag } from "./Labels"
import Slice from "./Slice"
import { spotText } from "./spot"
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


function browserDownload(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob)
  const link = Object.assign(document.createElement("a"), { href: url, download: filename })
  link.click()
  // The click has handed the bytes over by the next task; the URL is not needed after.
  setTimeout(() => URL.revokeObjectURL(url), 0)
}

export default function PartView({
  project,
  opening,
  partName,
  starting,
  designer,
  onSelectPart,
  onPartRenamed,
  onOpenProject,
  onNewPart,
  onAddToProject,
  header,
  chat,
  topInset,
  dragRegion,
  onManagePrinters,
  onSaveFile,
  onPointAt,
  onOpenInSlicer,
}: {
  project: Project | null
  /** A project is chosen and its read has not landed, which a running build can hold up. */
  opening?: boolean
  partName: string | null
  /** A new part is being described, so no sibling stands in for it until it exists. */
  starting?: boolean
  /** Who is designing the part right now ("Claude"), while that turn runs. Only a
   * part with no design yet says so on its stage. */
  designer?: string | null
  /** The header's part switcher changes parts, and whoever owns the selection is told. */
  onSelectPart?: (name: string) => void
  /** A rename from the header. The host moves its selection (and any conversation) along. */
  onPartRenamed?: (was: string, name: string) => void
  /** Opens the project panel; the switcher offers it when the host can show one. */
  onOpenProject?: () => void
  /** Starts another part in this part's folder. The switcher offers it when the host can. */
  onNewPart?: () => void
  /** Puts a part that is in no folder into one. Shown where the folder cell would be. */
  onAddToProject?: () => void
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
  /** Puts a downloaded file somewhere and says where. The desktop writes it to
   * Downloads and shows it in Finder; without one the browser downloads it. */
  onSaveFile?: (filename: string, blob: Blob) => Promise<string | void>
  /** Puts a sentence naming a clicked spot on the part into this part's chat. */
  onPointAt?: (text: string) => void
  /** Saves a file and opens it in the named slicer app. Only the desktop can. */
  onOpenInSlicer?: (filename: string, blob: Blob, app: string) => Promise<void>
}) {
  const projectId = project?.id ?? null
  const [highlight, setHighlight] = useState<number | null>(null)
  // A refused rename or label move says why for a few seconds, then gets out of the way.
  const [stageError, setStageError] = useState<string | null>(null)
  useEffect(() => {
    if (!stageError) return
    const timer = setTimeout(() => setStageError(null), 5000)
    return () => clearTimeout(timer)
  }, [stageError])
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
  // Once the user has opened or closed a row themselves, the part's own answer stops
  // overruling them.
  const touched = useRef({ checks: false, slice: false })

  const paramsSeq = useRef(0)
  const paramsTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const paramsAbort = useRef<AbortController | null>(null)
  // A drag the server has not answered yet. While it is out, a run landing is the
  // drag's own, or older, and must not pull the thumb back under the pointer.
  const paramsPending = useRef(false)

  const parts = project?.parts ?? []
  // Selection is by name and a rename changes the name, so for the round trip the host
  // and the project disagree on it. The part on stage stays put until they agree.
  const shownId = useRef<string | null>(null)
  const part =
    parts.find((p) => p.name === partName) ??
    (partName ? parts.find((p) => p.id === shownId.current) : undefined) ??
    (starting ? null : parts[0] ?? null)
  shownId.current = part?.id ?? null
  const build = part?.build ?? null
  const verdict = verdictOf(build)
  const glbUrl = build?.glb_url ?? null
  const runId = build?.id ?? null
  const findings = build?.findings ?? []
  const failedBuild = build?.status === "error"
  // Described and not written yet: the person's words are all there is.
  const noDesign = part != null && part.source == null

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
    setCamera(loadCamera(part.id, projectId, part.name))
    setHighlight(null)
  }, [part?.id])

  // A part carries the overrides its newest run was built at, so the sliders open
  // where they were left rather than back at the declared defaults.
  useEffect(() => {
    paramsSeq.current += 1
    paramsAbort.current?.abort()
    if (paramsTimer.current) clearTimeout(paramsTimer.current)
    paramsPending.current = false
    setValues(part?.overrides ?? {})
    setNote(null)
    setBuildError(null)
    setBuilding(false)
    // The child's own effect runs before this one, so clearing here would wipe the
    // price it just reported and leave the readouts disagreeing with the row.
    setSliceStatus(seedStatus(part?.build?.slice))
  }, [projectId, part?.name])

  // A chat edit, a shared setting or a measurement rebuilds the part at its own
  // values, so the sliders follow the run on screen. Otherwise a download would
  // send the old numbers onto the new shape, or a parameter that no longer exists.
  useEffect(() => {
    if (!paramsPending.current) setValues(part?.overrides ?? {})
  }, [runId])

  // A rebuild queued by the last drag is about a part nobody is looking at any more,
  // so the timer and the request leave with the view.
  useEffect(() => {
    return () => {
      if (paramsTimer.current) clearTimeout(paramsTimer.current)
      paramsAbort.current?.abort()
    }
  }, [])

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
      if (seq === paramsSeq.current) {
        paramsPending.current = false
        setBuilding(false)
      }
    }
  }, [])

  const onParamsChange = useCallback(
    (next: Params) => {
      setValues(next)
      setNote(null)
      const partId = part?.id
      const changed = Object.keys({ ...values, ...next }).filter((key) => values[key] !== next[key])
      // Nothing moved, so there is nothing to build or slice.
      if (!partId || changed.length === 0) return
      paramsPending.current = true
      if (paramsTimer.current) clearTimeout(paramsTimer.current)
      // The wait is for a drag settling; a switch is one click, so it builds at once.
      const flipped = changed.length > 0 && changed.every((key) => typeof (next[key] ?? values[key]) === "boolean")
      paramsTimer.current = setTimeout(() => void sendParams(partId, next), flipped ? 0 : DEBOUNCE_MS)
    },
    [part?.id, sendParams, values]
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
        const where = onSaveFile ? await onSaveFile(filename, blob) : browserDownload(filename, blob)
        activity({ id, title: `Exporting ${filename}`, detail: where ? `Saved to ${where}` : "Saved", tone: "done" })
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
    [part?.id, part?.name, values, onSaveFile]
  )

  // One click on the part, then back to orbiting: pointing is a single question.
  const [pointing, setPointing] = useState(false)
  // Labelling is the same single click, which opens a name field on the spot.
  const [labelling, setLabelling] = useState(false)
  // The label being named or renamed: `was` is its saved name, missing for a new spot.
  const [draft, setDraft] = useState<{ point: [number, number, number]; was?: string } | null>(null)
  // A label waiting for its new spot: label mode, but the click moves it instead of naming one.
  const [moving, setMoving] = useState<string | null>(null)
  useEffect(() => {
    setPointing(false)
    setLabelling(false)
    setDraft(null)
    setMoving(null)
  }, [part?.id])
  const onPick = useCallback(
    ({ point, normal }: { point: [number, number, number]; normal: [number, number, number] }) => {
      if (labelling) {
        setLabelling(false)
        if (moving && part) {
          setMoving(null)
          void setLabel(part.id, moving, point).catch((failure: unknown) =>
            setStageError(failure instanceof Error ? failure.message : "The label did not move.")
          )
        } else setDraft({ point })
        return
      }
      setPointing(false)
      onPointAt?.(spotText(point, normal))
    },
    [labelling, moving, part, onPointAt]
  )
  const partId = part?.id
  const anchors = useMemo<ViewerAnchor[]>(() => {
    if (!partId) return []
    const shown: ViewerAnchor[] = (part?.labels ?? [])
      .filter((label) => label.name !== draft?.was)
      .map((label) => ({
        key: `label:${label.name}`,
        point: label.point,
        node: <LabelTag label={label} onOpen={() => setDraft({ point: label.point, was: label.name })} />,
      }))
    if (!draft) return shown
    const was = draft.was
    const close = () => setDraft(null)
    const editor = (
      <LabelEditor
        key={was ?? draft.point.join(",")}
        was={was}
        onCancel={close}
        onSave={async (name) => {
          if (was === undefined) {
            // Saving under a taken name would move that label here; Move is the way to do that.
            if (part?.labels?.some((label) => label.name === name)) {
              throw new Error(`This part already has a label called ${name}.`)
            }
            await setLabel(partId, name, draft.point)
          } else if (name !== was) await renameLabel(partId, was, name)
          close()
        }}
        onMove={
          was === undefined
            ? undefined
            : () => {
                close()
                setPointing(false)
                setMoving(was)
                setLabelling(true)
              }
        }
        onRemove={
          was === undefined
            ? undefined
            : async () => {
                await deleteLabel(partId, was)
                close()
              }
        }
      />
    )
    return [...shown, { key: "label-draft", point: draft.point, node: editor }]
  }, [partId, part?.labels, draft])

  // The slicer this part's printer opens in, as the app name macOS opens files with.
  // It follows the printer, so a Prusa opens in PrusaSlicer when it is here. One that
  // came off PATH rather than out of an .app has nothing to open, so no row.
  const printerName = project?.printer?.name ?? null
  const [slicer, setSlicer] = useState<{ name: string; app: string } | null>(null)
  useEffect(() => {
    if (!onOpenInSlicer) return
    let live = true
    fetchPrinters(printerName)
      .then((workshop) => {
        if (!live) return
        const app = workshop.opener?.path.match(/([^/]+)\.app(\/|$)/)?.[1]
        setSlicer(workshop.opener && app ? { name: slicerName(workshop.opener.name), app } : null)
      })
      .catch(() => {})
    return () => {
      live = false
    }
  }, [onOpenInSlicer, printerName])

  const openInSlicer = useCallback(async () => {
    if (!part || !slicer || !onOpenInSlicer) return
    const filename = `${part.name}.3mf`
    const id = `slicer-${part.id}-${Date.now()}`
    activity({ id, title: `Opening ${filename} in ${slicer.name}`, tone: "working" })
    try {
      await onOpenInSlicer(filename, await exportPart(part.id, "3mf", values), slicer.app)
      activity({ id, title: `Opening ${filename} in ${slicer.name}`, detail: "Saved to Downloads", tone: "done" })
    } catch (failure) {
      const detail = failure instanceof Error ? failure.message : `${slicer.name} did not open it.`
      activity({ id, title: `Opening ${filename} in ${slicer.name}`, detail, tone: "fail" })
      throw failure
    }
  }, [part?.id, part?.name, values, slicer, onOpenInSlicer])

  const onCamera = useCallback(
    (state: CameraState) => {
      if (part) saveCamera(part.id, state)
      setCamera(state)
    },
    [part?.id]
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
  const detail = [noDesign ? null : rev(part?.revision ?? 0), seconds == null ? null : elapsedLabel(seconds)]
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
            value={
              part ? (
                <PartName
                  name={part.title ?? part.name}
                  onRename={(name) =>
                    renamePart(part.id, name)
                      .then((renamed) => onPartRenamed?.(renamed.was, renamed.name))
                      .catch((e) => setStageError(e instanceof Error ? e.message : String(e)))
                  }
                />
              ) : project && !project.folder ? (
                project.name
              ) : project ? (
                "New part"
              ) : opening ? (
                "Opening part"
              ) : (
                "No part yet"
              )
            }
          />
          <HeaderDivider />
          {header?.start ? (
            <>
              {header.start}
              <HeaderDivider />
            </>
          ) : null}
          {opening ? null : (
            <HeaderStatus tone={tone} label={building ? "BUILDING" : STATUS_LABEL[verdict]} detail={detail} />
          )}
        </>
      }
      end={
        <>
          {/* One cell names the project and opens its parts, because a row of tabs
           * runs off the header once a project holds a dozen. */}
          {project && (project.folder || parts.length > 1) ? (
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
              items={[
                ...(onNewPart ? [{ label: `New part in ${project.name}`, onSelect: onNewPart }] : []),
                ...parts.map((p, index) => ({
                  separated: Boolean(onNewPart) && index === 0,
                  label: p.title ?? p.name,
                  checked: p.name === part?.name,
                  onSelect: () => onSelectPart?.(p.name),
                })),
                ...(onOpenProject ? [{ label: "Project settings", separated: true, onSelect: onOpenProject }] : []),
              ]}
              footer={sharedLine(project.shared ?? [])}
            />
          ) : part && onAddToProject ? (
            <button
              type="button"
              onClick={onAddToProject}
              className="chrome flex h-[50px] items-center gap-2 border-l border-line px-3.5 text-muted transition-colors hover:text-ink"
            >
              <Icon name="folder" />
              <span className="mono-label">Add to project</span>
            </button>
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
            onPick={pointing || labelling ? onPick : null}
            anchors={anchors}
            bed={bedOf(project)}
            camera={camera}
            settleKey={settleKey}
            purge={purge}
            onCamera={onCamera}
            // The model on screen is the one before the change until the new one lands.
            className={`min-h-0 flex-1 transition-opacity duration-300 ${building ? "opacity-45" : ""}`}
          />
        ) : (
          <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-4">
            <EmptyProject
              title={
                noDesign
                  ? designer
                    ? `${designer} is designing this part`
                    : "No design yet"
                  : part
                  ? failedBuild
                    ? `${part.name} did not build`
                    : `${part.name} is not built yet`
                  : opening
                    ? "Opening part"
                    : "No part yet"
              }
              caption={
                noDesign
                  ? designer
                    ? "It appears here, live, as soon as the first version builds."
                    : "Describe the part in the chat and it appears here."
                  : !part
                  ? opening
                    ? "This can take a moment while another part is building."
                    : "It appears here, live, as soon as the plan is set."
                  : failedBuild
                    ? "The rail says what went wrong. Change a value or ask for a fix, and it rebuilds."
                    : "Build it once and it appears here. Dragging a parameter rebuilds it from then on."
              }
            />
            {part && !build && !noDesign ? (
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
        {glbUrl ? (
          <div className="absolute right-4 bottom-4 z-10 flex gap-2">
            <Button
              variant={labelling ? "accent" : "outline"}
              size="md"
              onClick={() => {
                setPointing(false)
                setDraft(null)
                setMoving(null)
                setLabelling((v) => !v)
              }}
            >
              {!labelling ? "Label a spot" : moving ? `Click the new spot for ${moving}` : "Click a spot to name it"}
            </Button>
            {onPointAt ? (
              <Button
                variant={pointing ? "accent" : "outline"}
                size="md"
                onClick={() => {
                  setLabelling(false)
                  setMoving(null)
                  setPointing((v) => !v)
                }}
              >
                {pointing ? "Click a spot on the part" : "Point at the part"}
              </Button>
            ) : null}
          </div>
        ) : null}
        <StageBuilding open={building && !!glbUrl} expected={seconds} />
        {stageError ? <StageNotice>{stageError}</StageNotice> : null}
        {failedBuild ? (
          <StageNotice>
            {build?.shown_revision != null ? `Showing ${rev(build.shown_revision)} · ` : ""}
            {rev(part?.revision ?? 0)} did not build
          </StageNotice>
        ) : null}
        </div>
      </StageColumn>

      {/* Sheet 30: an empty project has no rail; the stage runs to the edge. So does a
       * part with no design yet, which has nothing to adjust. */}
      {part && !noDesign ? (
        <ParamRail
          count={part?.params?.length ?? 0}
          pinned={pinned}
          params={
            <>
              <BuildFailedBanner
                open={failedBuild}
                revision={part?.revision ?? 0}
                shownRevision={build?.shown_revision ?? null}
                error={failedBuild && build?.error ? lastLine(build.error) : null}
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
                // While the banner is open it carries the reason; this is for a rebuild that never answered.
                error={failedBuild ? null : buildError}
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
                  revision={part.revision ?? 0}
                  runId={runId}
                  openIn={slicer ? { name: slicer.name, open: openInSlicer } : null}
                />
              ) : null}
            </div>
          }
        />
      ) : null}
    </Stage>
  )
}

// The part's name in the header, which is also where it is renamed: click it, type,
// Enter. The engine turns what was typed into a part name, so "Shelf Bracket" works.
function PartName({ name, onRename }: { name: string; onRename: (name: string) => void }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(name)
  const done = useRef(false)
  if (!editing) {
    return (
      <button
        type="button"
        title="Rename this part"
        onClick={() => {
          done.current = false
          setDraft(name)
          setEditing(true)
        }}
        className="chrome rounded-[2px] text-left decoration-line underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        {name}
      </button>
    )
  }
  const finish = (save: boolean) => {
    if (done.current) return
    done.current = true
    setEditing(false)
    const next = draft.trim()
    if (save && next && next !== name) onRename(next)
  }
  return (
    <input
      autoFocus
      aria-label={`Rename ${name}`}
      value={draft}
      onFocus={(e) => e.currentTarget.select()}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => finish(true)}
      onKeyDown={(e) => {
        if (e.key === "Enter") finish(true)
        else if (e.key === "Escape") finish(false)
      }}
      className="mono-value -mx-1 h-[18px] w-[180px] rounded-[2px] border border-accent bg-ground px-1 text-ink focus:outline-none"
    />
  )
}

// "1 shared file · 29 parts use it": the line that says this project is a system, so
// one change to it moves the set. Nothing when the project shares nothing.
function sharedLine(shared: { name: string; used_by: string[] }[]): string | undefined {
  if (shared.length === 0) return undefined
  const users = new Set(shared.flatMap((file) => file.used_by)).size
  const files = shared.length === 1 ? "1 shared file" : `${shared.length} shared files`
  if (users === 0) return `${files} · no part uses ${shared.length === 1 ? "it" : "them"} yet`
  const parts = users === 1 ? "1 part uses" : `${users} parts use`
  return `${files} · ${parts} ${shared.length === 1 ? "it" : "them"}`
}
