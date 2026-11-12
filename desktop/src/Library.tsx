import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { save as saveDialog } from "@tauri-apps/plugin-dialog";
import { openPath, revealItemInDir } from "@tauri-apps/plugin-opener";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import clsx from "clsx";
import {
  Button,
  ConfirmDialog,
  cue,
  duration,
  ease,
  EmptyShelf,
  FloatingHeader,
  HeaderCell,
  HeaderDivider,
  Icon,
  IconButton,
  Lockup,
  Menu,
  useContextMenu,
  PanelStrip,
  PartCard,
  ProgressBar,
  Stage,
  StageColumn,
  type MenuItem,
  type PartCardPart,
} from "@nurb/ui";
import {
  absolute,
  deletePart,
  deleteProject,
  exportProject,
  renamePart,
  renameProject,
  type LibraryPart,
  type Part,
  type ProjectSummary,
} from "@nurb/workbench/api";
import { folders, isDraft, matchesSearch, partsIn, sortParts, titleCase, type LibrarySort } from "./parts";

const SORTS: Record<LibrarySort, string> = { built: "Last built", name: "Name" };
const SORT_KEY = "nurb.librarySort";

function readSort(): LibrarySort {
  try {
    const saved = localStorage.getItem(SORT_KEY);
    if (saved === "built" || saved === "name") return saved;
  } catch {
    // Storage can be off; the default is the right answer then.
  }
  return "built";
}

// motion's types want a tuple; ease.out is a plain number[].
const OUT = ease.out as [number, number, number, number];

// Set the first time a part exists, so the first-run line is said once and the
// shelf is plain every time after that.
const FIRST_PART_KEY = "nurb-first-part";

type Removal = { project: ProjectSummary } | { part: LibraryPart };

type Props = {
  projects: ProjectSummary[];
  /** Every part in the library, which is what "All parts" shows. */
  allParts: LibraryPart[];
  /** The ids of the parts whose agent turn is running. */
  designing: Set<string>;
  /** Whether the rail is on All parts or on the selected folder. */
  showAll: boolean;
  /** Bumped by Find Parts in the menu bar, which focuses the search. */
  findKey: number;
  projectId: string | null;
  updateReady: boolean;
  /** The sheet-28 card, anchored over the rail footer by this screen. */
  updateCard?: ReactNode;
  /** Brings the card back after Later, so the chip is never a dead end. */
  onShowUpdate: () => void;
  importing: boolean;
  error: string | null;
  onSelectProject: (id: string) => void;
  onSelectAll: () => void;
  onOpenPart: (projectId: string, name: string) => void;
  /** Starts a part, inside the folder when one is named. */
  onNewPart: (folderId?: string) => void;
  /** Opens the picker that puts this part in a folder. */
  onAddToProject: (part: LibraryPart) => void;
  onImportFolder: () => void;
  /** The project that went, or null when only a part inside one did. */
  onRemoved: (id: string | null) => void;
  /** The shell moves the part's conversation and its selection to the new name. */
  onPartRenamed: (projectId: string, was: string, name: string) => void;
  /** The project panel: its shared settings, measurements and pieces. */
  onOpenProject: (id: string, name: string) => void;
  onSettings: () => void;
};

// The card wants the shape of the last build, not the build itself. The folder
// name rides along when the part is in one, because the footer says that instead
// of the revision.
function toCard(part: Part, folder?: string | null, designing = false): PartCardPart {
  const build = part.build;
  const status: PartCardPart["status"] = isDraft(part)
    ? "draft"
    : !build
    ? "unbuilt"
    : !build.finished_at
      ? "building"
      : build.status === "ok"
        ? "built"
        : "failed";
  const bbox = build?.stats?.bbox ?? null;
  return {
    id: part.id,
    name: part.title ?? titleCase(part.name),
    identifier: part.name,
    bbox: Array.isArray(bbox) ? bbox : null,
    status,
    revision: part.revision,
    builtAt: build?.finished_at ?? null,
    buildingSince: status === "building" ? build?.started_at ?? null : null,
    thumbnailUrl: build?.thumbnail_url ? absolute(build.thumbnail_url) : null,
    folder: folder ?? null,
    designing,
  };
}

/// Sheet 21: the screen the app opens on. Every project on the left, the
/// selected project's parts as cards, and one card away from the workspace.
export default function Library({
  projects,
  allParts,
  designing,
  showAll,
  findKey,
  projectId,
  updateReady,
  updateCard,
  onShowUpdate,
  importing,
  error,
  onSelectProject,
  onSelectAll,
  onOpenPart,
  onNewPart,
  onAddToProject,
  onImportFolder,
  onRemoved,
  onPartRenamed,
  onOpenProject,
  onSettings,
}: Props) {
  const [query, setQuery] = useState("");
  const [confirm, setConfirm] = useState<Removal | null>(null);
  const context = useContextMenu();
  const [failure, setFailure] = useState<string | null>(null);
  const [renaming, setRenaming] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const reduced = useReducedMotion() === true;
  const [firstRun, setFirstRun] = useState(() => {
    try {
      return localStorage.getItem(FIRST_PART_KEY) === null;
    } catch {
      return false;
    }
  });
  // Enter and Escape both take the input away, and its blur would ask a second time.
  const settled = useRef(false);
  const listRef = useRef<HTMLUListElement | null>(null);
  const searchRef = useRef<HTMLInputElement | null>(null);
  // The screen is unhidden in the same commit, so the input can take focus now.
  useEffect(() => {
    if (!findKey) return;
    searchRef.current?.focus();
    searchRef.current?.select();
  }, [findKey]);

  // The rail names folders only; a part's own container has no name to show.
  const rail = useMemo(() => folders(projects), [projects]);

  // The first part retires the first-run line for good.
  useEffect(() => {
    if (!firstRun || allParts.length === 0) return;
    try {
      localStorage.setItem(FIRST_PART_KEY, "yes");
    } catch {
      // A locked storage only means the line is said once more.
    }
    setFirstRun(false);
  }, [firstRun, allParts.length]);

  // An import that landed is the parts arriving, so it is worth a sound. A
  // refused one already has the engine's sentence on screen.
  const wasImporting = useRef(importing);
  useEffect(() => {
    const landed = wasImporting.current && !importing;
    wasImporting.current = importing;
    if (landed && !error) cue("ready");
  }, [importing, error]);

  // One shape for both views, so a card in a folder and a card in All parts are
  // the same card and lead to the same place.
  const parts = useMemo(
    () => (showAll ? allParts : partsIn(allParts, projectId)),
    [showAll, allParts, projectId],
  );

  const [sort, setSort] = useState<LibrarySort>(readSort);
  const chooseSort = (next: LibrarySort) => {
    setSort(next);
    try {
      localStorage.setItem(SORT_KEY, next);
    } catch {
      // Remembered for this session only.
    }
  };

  const shown = useMemo(() => {
    const found = query.trim() ? parts.filter((p) => matchesSearch(p, query)) : parts;
    return sortParts(found, sort);
  }, [parts, query, sort]);

  // One tab stop for the whole list; the arrows walk it from there.
  const move = (from: HTMLElement, delta: number) => {
    const rows = Array.from(listRef.current?.querySelectorAll<HTMLElement>("[data-row]") ?? []);
    rows[rows.indexOf(from) + delta]?.focus();
  };

  // The database is the project; files are something you take out of it. The save
  // panel names the new folder, the engine writes the 0.x layout there, and Finder
  // shows the result.
  const exportFolder = async (summary: ProjectSummary) => {
    try {
      const target = await saveDialog({ title: "Export as folder", defaultPath: summary.name, canCreateDirectories: true });
      if (!target) return;
      const written = await exportProject(summary.id, target);
      await revealItemInDir(written.directory).catch(() => openPath(written.directory));
    } catch (e) {
      setFailure(e instanceof Error ? e.message : String(e));
    }
  };

  const [renamingPart, setRenamingPart] = useState<string | null>(null);
  const [scrolled, setScrolled] = useState(false);
  const endPartRename = (part: LibraryPart, name: string | null) => {
    setRenamingPart(null);
    if (!name) return;
    renamePart(part.id, name)
      .then((renamed) => onPartRenamed(part.project_id, renamed.was, renamed.name))
      .catch((e) => setFailure(e instanceof Error ? e.message : String(e)));
  };

  const startRename = (summary: ProjectSummary) => {
    settled.current = false;
    setDraft(summary.name);
    setRenaming(summary.id);
  };

  // The list redraws itself from the live project event, so nothing is set here.
  const endRename = (summary: ProjectSummary, save: boolean) => {
    if (settled.current) return;
    settled.current = true;
    const name = draft.trim();
    setRenaming(null);
    if (!save || !name || name === summary.name) return;
    renameProject(summary.id, name).catch((e) => {
      setFailure(e instanceof Error ? e.message : String(e));
    });
  };

  const projectMenu = (summary: ProjectSummary): MenuItem[] => [
    { label: "New part in this project", onSelect: () => onNewPart(summary.id) },
    { label: "Project settings", onSelect: () => onOpenProject(summary.id, summary.name) },
    { label: "Rename", onSelect: () => startRename(summary) },
    { label: "Export as folder…", onSelect: () => void exportFolder(summary) },
    { label: "Remove from library", tone: "danger", separated: true, onSelect: () => setConfirm({ project: summary }) },
  ];

  // A part in a folder can move to another one; a loose part joins its first.
  const partMenu = (part: LibraryPart): MenuItem[] => [
    { label: "Rename", onSelect: () => setRenamingPart(part.id) },
    {
      label: part.folder ? "Move to another project" : "Add to project",
      onSelect: () => onAddToProject(part),
    },
    { label: "Delete part", tone: "danger", separated: true, onSelect: () => setConfirm({ part }) },
  ];

  // A part alone in its container takes the container with it, so the engine's
  // answer says whether a project went too.
  const remove = async (removal: Removal) => {
    setConfirm(null);
    try {
      if ("project" in removal) {
        await deleteProject(removal.project.id);
        onRemoved(removal.project.id);
      } else {
        const gone = await deletePart(removal.part.id);
        onRemoved(gone.project_deleted ? gone.project_id : null);
      }
    } catch (e) {
      setFailure(e instanceof Error ? e.message : String(e));
    }
  };

  // The open folder is where a new part goes, so the button says so.
  const selected = projects.find((summary) => summary.id === projectId);
  const folder = !showAll && selected?.folder ? selected : null;

  const header = (
    <FloatingHeader
      dragRegion
      start={
        <>
          {/* The window's own buttons are painted here by macOS. */}
          <div className="h-full w-[92px] shrink-0" data-tauri-drag-region />
          <HeaderDivider />
          <HeaderCell>
            <Lockup />
          </HeaderCell>
          <HeaderDivider />
          <div className="relative flex h-full items-center px-4">
            <span className="mono-label text-ink">Library</span>
            <span className="absolute inset-x-0 bottom-0 h-0.5 bg-accent" />
          </div>
        </>
      }
      end={
        <div className="flex h-full items-center gap-2 px-3">
          <label className="flex h-8 w-[230px] items-center gap-2 rounded-[3px] border border-line bg-ground px-2.5 focus-within:border-panel-edge">
            <Icon name="search" className="shrink-0 text-faint" />
            <input
              ref={searchRef}
              type="search"
              aria-label="Search parts"
              title="Search parts (⌘F)"
              placeholder="Search parts"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="mono-label min-w-0 flex-1 bg-transparent text-ink uppercase placeholder:text-faint focus:outline-none [&::-webkit-search-cancel-button]:appearance-none"
            />
          </label>
          <Button variant="outline" size="md" icon="folder" onClick={onImportFolder} disabled={importing} title="Import folder (⌘O)">
            {importing ? "Importing…" : "Import folder"}
          </Button>
          <Button
            variant="accent"
            size="md"
            icon="plus"
            onClick={() => onNewPart(folder?.id)}
            title="New part (⌘N)"
            className="max-w-[260px]"
          >
            <span className="min-w-0 truncate">{folder ? `New part in ${folder.name}` : "New part"}</span>
          </Button>
        </div>
      }
    />
  );

  const note = error ?? failure;

  return (
    <Stage className="relative" header={header} dragRegion>
      <aside className="panel flex w-[220px] shrink-0 flex-col overflow-hidden">
        <div className="shrink-0 p-1.5">
          <button
            type="button"
            aria-pressed={showAll}
            onClick={onSelectAll}
            className={clsx(
              "flex h-[30px] w-full cursor-default items-center gap-2 rounded-[3px] px-2.5",
              "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
              showAll ? "bg-raised" : "hover:bg-raised/60",
            )}
          >
            <span className="mono-value min-w-0 flex-1 truncate text-left uppercase text-ink">
              All parts
            </span>
            <span className="mono-caption shrink-0 text-muted">{allParts.length}</span>
          </button>
        </div>
        {/* Projects are rare, so the rail only names them once one exists. The empty list stays to hold the settings strip at the bottom. */}
        {rail.length > 0 ? <PanelStrip label="Projects" inset={16} /> : null}
        <ul
          ref={listRef}
          role="tree"
          aria-label="Projects"
          className="min-h-0 flex-1 overflow-y-auto p-1.5"
        >
          {rail.map((summary, index) => {
            const selected = !showAll && summary.id === projectId;
            return (
              <li key={summary.id} role="treeitem" aria-selected={selected}>
                <div
                  data-row
                  role="button"
                  tabIndex={selected || (showAll && index === 0) ? 0 : -1}
                  onClick={() => onSelectProject(summary.id)}
                  onContextMenu={(e) => context.open(e, renaming === summary.id ? undefined : projectMenu(summary))}
                  onKeyDown={(e) => {
                    // The actions menu is a button inside this row. Its own keys
                    // are its own, or Enter would select the project instead of
                    // opening the menu.
                    if (e.target !== e.currentTarget) return;
                    if (e.key === "ArrowDown") {
                      e.preventDefault();
                      move(e.currentTarget, 1);
                    } else if (e.key === "ArrowUp") {
                      e.preventDefault();
                      move(e.currentTarget, -1);
                    } else if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelectProject(summary.id);
                    }
                  }}
                  className={clsx(
                    "group flex h-[30px] cursor-default items-center gap-2 rounded-[3px] px-2.5",
                    "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
                    selected ? "bg-raised" : "hover:bg-raised/60",
                  )}
                >
                  {renaming === summary.id ? (
                    <input
                      autoFocus
                      aria-label={`Rename ${summary.name}`}
                      maxLength={100}
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      onBlur={() => endRename(summary, true)}
                      onKeyDown={(e) => {
                        e.stopPropagation();
                        if (e.key === "Enter") endRename(summary, true);
                        else if (e.key === "Escape") endRename(summary, false);
                      }}
                      className="mono-value h-[22px] min-w-0 flex-1 rounded-[2px] border border-accent bg-ground px-1 uppercase text-ink focus:outline-none"
                    />
                  ) : (
                    <span className="mono-value min-w-0 flex-1 truncate uppercase text-ink">
                      {summary.name}
                    </span>
                  )}
                  {/* The count gives way to the row's actions, so no column sits empty at rest. An open menu keeps them, or its trigger would vanish under it. */}
                  <span className="mono-caption shrink-0 text-muted group-hover:hidden group-focus-within:hidden group-has-[[aria-expanded=true]]:hidden">
                    {summary.parts}
                  </span>
                  <span className="-mr-1 hidden shrink-0 items-center group-hover:flex group-focus-within:flex group-has-[[aria-expanded=true]]:flex">
                    <IconButton
                      icon="plus"
                      label={`New part in ${summary.name}`}
                      className="size-6"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNewPart(summary.id);
                      }}
                    />
                    <Menu
                      portal
                      label={`Actions for ${summary.name}`}
                      items={projectMenu(summary)}
                    />
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
        {note ? (
          <div className="mono-caption shrink-0 px-4 pb-2 text-fail" role="alert">
            {note}
          </div>
        ) : null}
        <div className="flex h-10 shrink-0 items-center gap-2 border-t border-line-soft px-4">
          {updateReady ? (
            <button
              type="button"
              onClick={onShowUpdate}
              className="mono-label chrome rounded-[2px] bg-accent-wash px-1.5 py-0.5 text-[9px] leading-3 text-accent-ink"
            >
              Update ready
            </button>
          ) : null}
          <IconButton className="ml-auto" icon="gear" label="Settings" title="Settings (⌘,)" onClick={onSettings} />
        </div>
      </aside>

      {/* The column runs into the stage's bottom and right gutters: the grid scrolls off
       * the window's own edge rather than stopping on a line in the air, and the
       * scrollbar sits in the right gutter instead of over the cards. Children put the
       * right gutter back with pr-4. */}
      {context.menu}
      {/* A right-click on the shelf itself, between the cards, offers what its buttons do. */}
      <StageColumn
        className="-mr-4 -mb-4"
        onContextMenu={(e) =>
          context.open(e, [
            { label: folder ? `New part in ${folder.name}` : "New part", onSelect: () => onNewPart(folder?.id) },
            { label: "Import folder…", disabled: importing, onSelect: onImportFolder },
          ])
        }
      >
        {importing ? (
          <div className="shrink-0 pr-4 pb-3">
            <ProgressBar value={null} label="Importing folder" pendingLabel="Reading the parts" />
          </div>
        ) : null}
        {parts.length === 0 && showAll ? (
          <div className="flex min-h-0 flex-1 flex-col pr-4 pb-4">
            <EmptyShelf
              firstRun={firstRun}
              caption="Start a part and describe it, or import a folder of parts you already have."
              primary={{ label: "New part", icon: "plus", onClick: () => onNewPart() }}
              secondary={{
                label: importing ? "Importing…" : "Import folder",
                icon: "folder",
                onClick: onImportFolder,
                disabled: importing,
              }}
            />
          </div>
        ) : parts.length === 0 ? (
          <div className="flex min-h-0 flex-1 flex-col pr-4 pb-4">
            <EmptyShelf
              caption={`No parts in ${selected?.name ?? "this project"} yet. Start one here.`}
              primary={{ label: "New part", icon: "plus", onClick: () => onNewPart(projectId ?? undefined) }}
              secondary={{ label: "All parts", onClick: onSelectAll }}
            />
          </div>
        ) : (
          <>
            <div className="chrome flex h-[30px] shrink-0 items-center justify-between pr-4">
              <span className="mono-caption text-on-stage-muted">
                {shown.length} {shown.length === 1 ? "part" : "parts"}
                {showAll || !selected ? "" : ` · ${selected.name}`}
              </span>
              <Menu
                portal
                label="Sort parts"
                triggerClassName="h-6 rounded-control px-1.5"
                trigger={() => (
                  <span className="mono-caption flex items-center gap-1 text-on-stage-muted transition-colors hover:text-ink">
                    Sort · {SORTS[sort]}
                    <Icon name="chevron-down" />
                  </span>
                )}
                items={(Object.keys(SORTS) as LibrarySort[]).map((key) => ({
                  label: SORTS[key],
                  checked: key === sort,
                  onSelect: () => chooseSort(key),
                }))}
              />
            </div>
            {/* The last row stops on the gutter, level with the sidebar's foot. */}
            <div
              onScroll={(e) => setScrolled(e.currentTarget.scrollTop > 0)}
              // Scrolled, the cards fade out under the count instead of being cut on a line.
              className={clsx(
                "min-h-0 flex-1 overflow-y-auto pt-1 pr-4 pb-4",
                scrolled && "[mask-image:linear-gradient(to_bottom,transparent,black_20px)]",
              )}
            >
              {shown.length === 0 ? (
                <p className="mono-caption pt-8 text-center text-on-stage-muted">
                  Nothing here matches {query.trim()}
                </p>
              ) : (
                <div className="grid grid-cols-4 gap-4">
                  {/* A deleted card leaves a hole its neighbours close, so the grid
                      is the same grid before and after rather than a new one. */}
                  <AnimatePresence initial={false}>
                    {shown.map((part) => (
                      <motion.div
                        key={part.id}
                        layout
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: reduced ? 0 : duration.settle, ease: OUT }}
                      >
                        <PartCard
                          part={toCard(part, part.folder ? part.project_name : null, designing.has(part.id))}
                          menu={partMenu(part)}
                          renaming={renamingPart === part.id}
                          onRename={(name) => endPartRename(part, name)}
                          onOpen={() => onOpenPart(part.project_id, part.name)}
                        />
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </div>
          </>
        )}
      </StageColumn>

      {updateCard}

      {confirm && "project" in confirm ? (
        <ConfirmDialog
          title={`Remove ${confirm.project.name}?`}
          confirmLabel="Remove"
          hold
          onConfirm={() => void remove(confirm)}
          onCancel={() => setConfirm(null)}
        >
          Its parts go with it. The folder on your Mac stays where it is.
        </ConfirmDialog>
      ) : null}
      {confirm && "part" in confirm ? (
        <ConfirmDialog
          title={`Delete ${confirm.part.title ?? titleCase(confirm.part.name)}?`}
          confirmLabel="Delete"
          hold
          onConfirm={() => void remove(confirm)}
          onCancel={() => setConfirm(null)}
        >
          Every revision goes with it. There is no undo.
        </ConfirmDialog>
      ) : null}
    </Stage>
  );
}
