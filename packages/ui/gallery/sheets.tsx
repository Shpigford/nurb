import { useEffect, useRef, useState, type ReactNode } from "react"
import clsx from "clsx"
import {
  AssistantMarkdown,
  BuildCard,
  Button,
  ChatPanel,
  EmptyProject,
  EmptyShelf,
  ExportMenu,
  FindingsList,
  FloatingHeader,
  HeaderCell,
  HeaderDivider,
  HeaderIcons,
  HeaderStack,
  HeaderStatus,
  Icon,
  IconButton,
  Lockup,
  Menu,
  PanelStrip,
  ParamRail,
  ParamsPanel,
  RailDisclosure,
  PartCard,
  SpecCard,
  Stage,
  StageColumn,
  StageEmpty,
  StageNotice,
  BuildFailedBanner,
  ViewerIsland,
  type BuildEvent,
  type ExportFormat,
  type Param,
  type Params,
  UpdateCard,
} from "../src/index"
import {
  buildFailed,
  buildPassed,
  flaggedFindings,
  libraryParts,
  libraryProjects,
  panelParams,
  specFixture,
} from "./fixtures"

// Every sheet is a fixed 1440x900 frame so a screenshot lines up with the Paper board.
const SHEET_W = 1440
const SHEET_H = 900

export function Sheet({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-hidden bg-stage" style={{ width: SHEET_W, height: SHEET_H }}>
      {children}
    </div>
  )
}

function sheetStage(children: ReactNode, header?: ReactNode) {
  return (
    <Sheet>
      <Stage header={header} style={{ height: SHEET_H }}>
        {children}
      </Stage>
    </Sheet>
  )
}

// The macOS window buttons, as the desktop sheets draw them: 84px cell, 12px dots, 8px apart.
function TrafficLights() {
  return (
    <div className="flex h-full w-[84px] shrink-0 items-center gap-2 pl-[18px]">
      {["#FF5F57", "#FEBC2E", "#28C840"].map((color) => (
        <span key={color} className="size-3 rounded-full" style={{ background: color }} />
      ))}
    </div>
  )
}

function SearchBox() {
  return (
    <label className="flex h-7 w-[230px] items-center gap-2 rounded-[3px] border border-line px-2.5 text-faint">
      <Icon name="search" />
      <span className="mono-id text-faint [letter-spacing:0.06em]">SEARCH PARTS</span>
    </label>
  )
}

function Composer({ placeholder = "Describe the part, or what to change" }: { placeholder?: string }) {
  return (
    <div className="flex items-center gap-2 rounded-content border border-line bg-ground px-3 py-2.5">
      <span className="text-chat flex-1 text-faint">{placeholder}</span>
      <IconButton icon="arrow-up" label="Send" />
    </div>
  )
}

// The spec pinned two of these, so they arrive as str params and the panel locks them.
const railParams: Param[] = [
  { name: "rail_seat", kind: "str", default: "Ø25.0", description: "pinned by the spec" },
  { name: "shelf_slot", kind: "str", default: "18.0", description: "pinned by the spec" },
  ...panelParams.filter((p) => p.kind !== "str"),
]

const noop = () => {}

// Opens the popover inside this element once, so a screenshot catches it. StrictMode
// runs the effect twice on one fiber, and a second click would shut what the first opened.
function useOpenOnce() {
  const ref = useRef<HTMLDivElement>(null)
  const clicked = useRef(false)
  useEffect(() => {
    if (clicked.current) return
    clicked.current = true
    ref.current?.querySelector<HTMLButtonElement>('button[aria-haspopup="menu"]')?.click()
  }, [])
  return ref
}

const fakeExport = (_format: ExportFormat): Promise<void> => new Promise((resolve) => setTimeout(resolve, 1500))

/* 05 · Library ------------------------------------------------------------- */

function ProjectsPanel({ menuOpen = false }: { menuOpen?: boolean }) {
  const rowMenu = [
    { label: "Rename", onSelect: noop },
    { label: "Show in Finder", onSelect: noop },
    { label: "Remove from library", onSelect: noop, tone: "danger" as const },
  ]
  return (
    <aside className="panel flex w-[220px] shrink-0 flex-col overflow-hidden">
      <PanelStrip label="Projects" inset={16} />
      <div className="flex flex-col px-2 pt-2">
        {libraryProjects.map((project, index) => (
          <div
            key={project.id}
            className={clsx(
              "chrome group flex h-8 items-center gap-2 rounded-[3px] px-2",
              index === 0 ? "bg-raised text-ink" : "text-ink-soft"
            )}
          >
            <span className="mono-label min-w-0 flex-1 truncate">{project.name}</span>
            {index === 1 && menuOpen ? (
              <OpenMenu label={`More for ${project.name}`} items={rowMenu} />
            ) : (
              <span className="mono-caption text-muted tabular-nums">{project.count}</span>
            )}
          </div>
        ))}
      </div>
      <div className="mt-auto flex h-10 shrink-0 items-center gap-2 border-t border-line-soft px-3">
        <span className="mono-caption whitespace-nowrap text-muted">nurb 1.0.0</span>
        <span className="mono-caption whitespace-nowrap rounded-full bg-accent-wash px-2 py-0.5 text-accent-ink [letter-spacing:0.08em]">
          UPDATE READY
        </span>
        <span className="ml-auto text-muted">
          <Icon name="gear" />
        </span>
      </div>
    </aside>
  )
}

// A Menu that opens itself on mount, so a screenshot catches the popover.
function OpenMenu({ label, items }: { label: string; items: { label: string; onSelect: () => void; tone?: "default" | "danger" }[] }) {
  const ref = useOpenOnce()
  return (
    <div ref={ref}>
      <Menu label={label} items={items} />
    </div>
  )
}

function LibraryHeader({ desktop = false }: { desktop?: boolean }) {
  return (
    <FloatingHeader
      start={desktop ? <TrafficLights /> : undefined}
      cells={
        <>
          <HeaderCell>
            <Lockup />
          </HeaderCell>
          <HeaderDivider />
          <span className="mono-label flex h-full items-center border-b-2 border-accent px-[15px] text-ink [letter-spacing:0.12em]">
            Library
          </span>
        </>
      }
      end={
        <>
          <HeaderDivider />
          <HeaderCell className="gap-3">
            <SearchBox />
            <Button variant="outline" icon="plus">
              Import folder
            </Button>
            <Button variant="accent" icon="plus">
              New project
            </Button>
          </HeaderCell>
        </>
      }
    />
  )
}

function LibrarySheet({ desktop = false, update = false }: { desktop?: boolean; update?: boolean }) {
  return sheetStage(
    <>
      <ProjectsPanel menuOpen={desktop && !update} />
      {update ? (
        <UpdateCard version="1.1.0" onLater={noop} onInstall={noop} className="absolute bottom-[68px] left-4 z-20" />
      ) : null}
      <main className="flex min-h-0 min-w-0 flex-1 flex-col gap-3">
        <div className="chrome flex h-6 shrink-0 items-center justify-between px-1">
          <p className="mono-label text-on-stage-muted">12 parts · Bench shelf</p>
          <p className="mono-caption text-on-stage-muted [letter-spacing:0.11em]">Sort ▾ last built</p>
        </div>
        <div className="grid min-h-0 grid-cols-4 gap-3 overflow-hidden">
          {libraryParts.map((part) => (
            <PartCard key={part.id} part={part} onOpen={noop} />
          ))}
        </div>
      </main>
    </>,
    <LibraryHeader desktop={desktop} />
  )
}

/* 06 · Library, empty ------------------------------------------------------ */

function LibraryEmptySheet() {
  return sheetStage(
    <>
      <ProjectsPanel />
      <main className="flex min-h-0 min-w-0 flex-1 flex-col">
        <EmptyShelf primary={{ label: "Describe a part", onClick: noop }} />
      </main>
    </>,
    <LibraryHeader />
  )
}

/* 07 · Workspace, first run ------------------------------------------------ */

const SUGGESTIONS = ["A hook for the shop vac hose", "A tray for my hex keys", "A clip that holds the spool end"]

function WorkspaceHeader({
  status,
  tabs,
  desktop = false,
}: {
  status: { tone: "none" | "pass" | "warn" | "fail" | "building"; label: string; detail?: string }
  tabs?: boolean
  desktop?: boolean
}) {
  return (
    <FloatingHeader
      start={desktop ? <TrafficLights /> : undefined}
      cells={
        <>
          <HeaderCell>
            <Lockup />
          </HeaderCell>
          <HeaderDivider />
          <HeaderCell className="gap-[7px] text-muted">
            <Icon name="chevron-left" />
            <span className="mono-value font-normal uppercase [letter-spacing:0.11em]">Library</span>
          </HeaderCell>
          <HeaderDivider />
          <HeaderStack label="Project" value="Bench shelf" />
          <HeaderDivider />
          <HeaderStatus tone={status.tone} label={status.label} detail={status.detail} />
        </>
      }
      end={
        <>
          {tabs ? (
            <>
              <HeaderDivider />
              <Menu
                label="Parts in Bench shelf"
                triggerClassName="h-[50px] rounded-none"
                trigger={() => (
                  <span className="flex h-full items-center gap-2 px-3.5 text-muted">
                    <Icon name="folder" />
                    <span className="mono-label">In Bench shelf</span>
                    <Icon name="chevron-down" />
                  </span>
                )}
                items={["rail_bracket", "shelf_pin", "wall_plate"].map((name) => ({
                  label: name,
                  checked: name === "rail_bracket",
                  onSelect: noop,
                }))}
              />
            </>
          ) : null}
          <HeaderDivider />
          <HeaderIcons>
            <IconButton icon="ruler" label="Measure" />
            <IconButton icon="camera" label="Snapshot" />
            <IconButton icon="expand" label="Fullscreen" />
          </HeaderIcons>
          <HeaderDivider />
          <HeaderCell className="px-3.5">
            {desktop ? (
              <IconButton icon="gear" label="Settings" />
            ) : (
              <span className="mono-id flex size-7 items-center justify-center rounded-full bg-raised text-ink-soft">JP</span>
            )}
          </HeaderCell>
        </>
      }
    />
  )
}

function AgentPicker() {
  return (
    <span className="mono-id flex h-6 items-center gap-1.5 rounded-[3px] border border-line px-2 text-ink-soft">
      Claude Code
      <Icon name="chevron-down" />
    </span>
  )
}

function FirstRunSheet({ desktop = false }: { desktop?: boolean }) {
  return sheetStage(
    <>
      <ChatPanel
        strip={{ label: "Conversation" }}
        picker={desktop ? <AgentPicker /> : undefined}
        composer={<Composer />}
      >
        <div className="flex h-full flex-col items-center justify-center gap-6 px-6 text-center">
          <h2 className="font-display text-[20px] leading-[26px] tracking-[-0.022em] text-balance text-ink">
            What’s rattling around your bench?
          </h2>
          <p className="text-chat max-w-[30ch] text-ink-soft">
            Say what the part has to do and it builds on the plate while you watch.
          </p>
          <div className="flex flex-col items-center gap-2">
            <p className="mono-caption text-faint [letter-spacing:0.12em]">Try one</p>
            {SUGGESTIONS.map((line) => (
              <button
                key={line}
                type="button"
                className="text-chat rounded-full border border-line px-3 py-1.5 text-ink-soft hover:border-panel-edge hover:text-ink"
              >
                {line}
              </button>
            ))}
          </div>
        </div>
      </ChatPanel>
      <StageEmpty>
        <EmptyProject />
        {desktop ? (
          <div className="mt-6">
            <Button variant="outline" icon="plus">
              Import folder
            </Button>
          </div>
        ) : null}
      </StageEmpty>
    </>,
    <WorkspaceHeader status={{ tone: "none", label: "Draft", detail: "no part yet" }} desktop={desktop} />
  )
}

/* 10 to 13, 22, 29 · the built workspace ----------------------------------- */

type BuiltOptions = {
  desktop?: boolean
  dirty?: boolean
  exportOpen?: boolean
  failed?: boolean
  disclosuresOpen?: boolean
}

function AutoOpenExport() {
  const ref = useOpenOnce()
  return (
    <div ref={ref} className="flex flex-1">
      <ExportMenu
        partId="rail-bracket"
        export={fakeExport}
        status={{ state: "succeeded", grams: 42, seconds: 4320 }}
        revision={4}
        openIn={{ name: "Bambu Studio", open: fakeExport.bind(null, "3mf") }}
      />
    </div>
  )
}

function SliceRows() {
  return (
    <div className="flex flex-col gap-1.5 px-4 py-2.5">
      <div className="mono-label flex items-center justify-between text-ink-soft">
        <span>Printer</span>
        <span className="mono-value text-ink">Prusa MK4</span>
      </div>
      <div className="mono-label flex items-center justify-between text-ink-soft">
        <span>Filament</span>
        <span className="mono-value text-ink">42 g · 1:12</span>
      </div>
    </div>
  )
}

function BuiltSheet({ desktop, dirty, exportOpen, failed, disclosuresOpen }: BuiltOptions) {
  const [values, setValues] = useState<Params>(dirty ? { width: 96.5 } : {})
  const [highlight, setHighlight] = useState<number | null>(null)
  const [open, setOpen] = useState<Record<string, boolean>>({
    checks: Boolean(disclosuresOpen),
    slice: Boolean(disclosuresOpen),
  })
  const toggle = (key: string) => setOpen((prior) => ({ ...prior, [key]: !prior[key] }))

  return sheetStage(
    <>
      <ChatPanel
        strip={{ label: "Conversation" }}
        picker={desktop ? <AgentPicker /> : undefined}
        composer={<Composer />}
      >
        <div className="flex flex-col gap-3 p-4">
          <p className="mono-caption text-faint [letter-spacing:0.12em]">You 01</p>
          <p className="text-chat ml-8 rounded-content bg-raised px-3 py-2 text-ink">
            I need a bracket that clips onto the shelf rail and carries 2 kg.
          </p>
          <p className="mono-caption text-faint [letter-spacing:0.12em]">nurb 02</p>
          <div className="text-chat text-ink-soft">
            <AssistantMarkdown content="I measured the **shelf rail** at 25.16 mm across the flat and pinned it, so the seat cannot drift. The hook reaches 12.5 mm over the rail." />
          </div>
          <SpecCard spec={specFixture} model="claude-fable-5" effort="low" />
          <BuildCard build={failed ? buildFailed : buildPassed} />
        </div>
      </ChatPanel>

      <StageColumn>
        {failed ? <StageNotice>Showing rev 04 · rev 05 did not build</StageNotice> : null}
        <ViewerIsland
          glbUrl="/flagged.glb"
          findings={flaggedFindings}
          highlight={highlight}
          onHighlight={setHighlight}
          bed={[256, 256]}
          className="h-full"
        />
      </StageColumn>

      <ParamRail
        count={14}
        params={
          <>
            {failed ? <BuildFailedBanner revision={5} shownRevision={4} /> : null}
            <ParamsPanel
              params={railParams}
              values={values}
              onChange={setValues}
              onApply={() => setValues({})}
              stats={{ size_mm: [92.5, 41.2, 18], volume_mm3: 14820, faces: 62, build_s: 3.1 }}
            />
          </>
        }
        readouts={{ grams: 42, seconds: 4320, heightMm: 110 }}
        warnCount={1}
        disclosures={
          <>
            <RailDisclosure
              label="Checks"
              summary="1 warn"
              tone="warn"
              open={open.checks}
              onToggle={() => toggle("checks")}
            >
              <FindingsList findings={flaggedFindings} verdict="warn" highlight={highlight} onHighlight={setHighlight} />
            </RailDisclosure>
            <RailDisclosure label="Slice" summary="Prusa MK4" open={open.slice} onToggle={() => toggle("slice")}>
              <SliceRows />
            </RailDisclosure>
          </>
        }
        actions={
          <>
            {exportOpen ? (
              <AutoOpenExport />
            ) : (
              <ExportMenu
                partId="rail-bracket"
                export={fakeExport}
                status={{ state: "succeeded", grams: 42, seconds: 4320 }}
                revision={4}
              />
            )}
            <Button variant="outline" size="md">
              Rebuild
            </Button>
          </>
        }
      />
    </>,
    <WorkspaceHeader
      status={
        failed
          ? { tone: "fail", label: "Failed", detail: "rev 05 · 0:12" }
          : { tone: "pass", label: "Built", detail: "rev 04 · 0:47" }
      }
      tabs
      desktop={desktop}
    />
  )
}

/* hero · the nurb.app hero image, regenerated by `npm run site:hero` ------- */

// The gridfinity shelf from engine/examples/notch, at its defaults, with every check
// passing: the numbers match a real build of that part on a Bambu Lab H2C.
const heroParams: Param[] = [
  { name: "bracket_count", kind: "int", default: 4, min: 2, max: 8 },
  { name: "item_height", kind: "float", default: 42, min: 20, max: 120 },
  { name: "item_depth", kind: "float", default: 6, min: 2, max: 20 },
  { name: "grid_x", kind: "int", default: 2, min: 1, max: 6 },
  { name: "grid_y", kind: "int", default: 2, min: 1, max: 6 },
  { name: "shelf_thickness", kind: "float", default: 7, min: 4, max: 12 },
  { name: "back_gap", kind: "float", default: 4, min: 0, max: 10 },
  { name: "gusset_thickness", kind: "float", default: 3, min: 2, max: 8 },
  { name: "chamfer_size", kind: "float", default: 1, min: 0, max: 3 },
]

const heroBuild: BuildEvent = {
  ...buildPassed,
  id: "build-hero",
  part_name: "shelf_gridfinity",
  elapsed_s: 6,
  revision: 1,
  findings: [],
  stats: { size_mm: [94, 100.6, 42], build_s: 6.6 },
}

function HeroSheet() {
  return sheetStage(
    <>
      <ChatPanel strip={{ label: "Conversation" }} picker={<AgentPicker />} composer={<Composer />}>
        <div className="flex flex-col gap-3 p-4">
          <p className="mono-caption text-faint [letter-spacing:0.12em]">You 01</p>
          <p className="text-chat ml-8 rounded-content bg-raised px-3 py-2 text-ink">
            I need a shelf for my tool wall that holds four gridfinity bins, two by two.
          </p>
          <p className="mono-caption text-faint [letter-spacing:0.12em]">nurb 02</p>
          <div className="text-chat text-ink-soft">
            <AssistantMarkdown content={"Built it. Four bins, two by two, on a shelf 94 mm deep and 100.6 mm wide, hung from four brackets on the rail.\n\nAll checks pass. On your H2C it is 41 g and about 71 minutes. If your bins are taller than 42 mm, drag **item height** and the back grows with them."} />
          </div>
          <BuildCard build={heroBuild} />
        </div>
      </ChatPanel>

      <StageColumn>
        <ViewerIsland glbUrl="/shelf_gridfinity.glb" bed={[350, 320]} className="h-full" />
      </StageColumn>

      <ParamRail
        count={13}
        params={
          <ParamsPanel
            params={heroParams}
            values={{}}
            onChange={noop}
            onApply={noop}
            stats={heroBuild.stats}
          />
        }
        readouts={{ grams: 41, seconds: 4260, heightMm: 42 }}
        disclosures={
          <>
            <RailDisclosure label="Checks" summary="All pass" tone="pass" open={false} onToggle={noop}>
              <></>
            </RailDisclosure>
            <RailDisclosure label="Slice" summary="Bambu Lab H2C" open={false} onToggle={noop}>
              <></>
            </RailDisclosure>
          </>
        }
        actions={
          <ExportMenu
            partId="shelf-gridfinity"
            export={fakeExport}
            status={{ state: "succeeded", grams: 41, seconds: 4260 }}
            revision={1}
          />
        }
      />
    </>,
    <WorkspaceHeader status={{ tone: "pass", label: "Checks pass", detail: "rev 01 · 0:06" }} tabs desktop />
  )
}

/* 23 to 28 · the desktop sheets still being drawn --------------------------- */

function Placeholder({ caption }: { caption: string }) {
  return sheetStage(
    <StageEmpty>
      <p className="mono-label text-on-stage-muted [letter-spacing:0.12em]">{caption}</p>
    </StageEmpty>,
    <FloatingHeader
      start={<TrafficLights />}
      cells={
        <HeaderCell>
          <Lockup />
        </HeaderCell>
      }
    />
  )
}

export interface SheetRoute {
  id: string
  title: string
  View: () => ReactNode
}

export const SHEETS: SheetRoute[] = [
  { id: "05", title: "Library", View: () => <LibrarySheet /> },
  { id: "06", title: "Library empty", View: () => <LibraryEmptySheet /> },
  { id: "07", title: "Workspace first run", View: () => <FirstRunSheet /> },
  { id: "10", title: "Workspace built", View: () => <BuiltSheet /> },
  { id: "11", title: "Parameters changed", View: () => <BuiltSheet dirty /> },
  { id: "12", title: "Download menu", View: () => <BuiltSheet exportOpen /> },
  { id: "13", title: "Build failed", View: () => <BuiltSheet failed /> },
  { id: "21", title: "Desktop library", View: () => <LibrarySheet desktop /> },
  { id: "22", title: "Desktop workspace", View: () => <BuiltSheet desktop /> },
  { id: "23", title: "First launch", View: () => <Placeholder caption="Sheet 23 · First launch · desktop" /> },
  { id: "24", title: "Engine starting", View: () => <Placeholder caption="Sheet 24 · Engine starting · desktop" /> },
  { id: "25", title: "Settings", View: () => <Placeholder caption="Sheet 25 · Settings · desktop" /> },
  { id: "26", title: "About", View: () => <Placeholder caption="Sheet 26 · About · desktop" /> },
  { id: "27", title: "Add an agent", View: () => <Placeholder caption="Sheet 27 · Add an agent · desktop" /> },
  { id: "28", title: "Update ready", View: () => <LibrarySheet desktop update /> },
  { id: "29", title: "Findings, slice open", View: () => <BuiltSheet desktop disclosuresOpen /> },
  { id: "30", title: "Empty project", View: () => <FirstRunSheet desktop /> },
  { id: "hero", title: "nurb.app hero", View: () => <HeroSheet /> },
]
