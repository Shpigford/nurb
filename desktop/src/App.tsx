import { Fragment, FormEvent, PointerEvent as ReactPointerEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { ask, message, open as pickFolder } from "@tauri-apps/plugin-dialog";
import { revealItemInDir } from "@tauri-apps/plugin-opener";
import { check, Update } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";
import About from "./About";
import AgentsHelp from "./AgentsHelp";
import Chat, { AGENT_LABEL, PROJECT_CHAT } from "./Chat";
import GeminiKeyDialog from "./GeminiKeyDialog";
import {
  chatKey,
  markChatSeen,
  retainChatColumns,
  updateChatActivity,
  type ChatColumn,
} from "./chatColumns";
import { IconCube, IconCubes, IconFolder, IconFolderPlus, IconGear, IconVariant } from "./Icons";
import { COLUMNS, fitColumns, initialColumns, resizedColumn } from "./layout";
import { createLatestRequestGate } from "./latestRequest";
import Logo from "./Logo";
import type { Column } from "./layout";
import { partMessage, type PartConfigurationRequest } from "./partMessages";
import { createPartRecovery } from "./partRecovery";
import { isWindows } from "./platform";
import Setup from "./Setup";
import Settings from "./Settings";
import "./App.css";

type Project = {
  name: string;
  path: string;
  lastOpened: number;
  selectedPart?: string;
  missing: boolean;
};

type Server = { url: string; port: number };
// `assembly` and `uses` are the placed-parts pair: an assembly is not one printable
// solid, and the rail says so rather than letting it pass as another part.
type Variant = { name: string; params: Record<string, unknown>; note?: string | null };
type Part = {
  name: string;
  error: string | null;
  refused: boolean;
  assembly: boolean;
  uses: string[];
  variants: Variant[];
  // The variant the server resolved from the last successful build, so the rail's
  // active mark tracks truth (an agent or a slider drag can move it) rather than
  // the last click.
  variant: string | null;
};
type PartState = { path: string; parts: Part[] };
type ChatInfo = {
  id: string;
  title: string | null;
  updatedAt: string | null;
  part: string | null;
  agent: string;
};

type AgentStatus = {
  id: string;
  label: string;
  installed: boolean;
  loggedIn: boolean | null;
  detail: string | null;
  note: string;
  install: string | null;
};

type AboutInfo = {
  appVersion: string;
  nurbVersion: string;
  occtVersion: string | null;
  osVersion: string;
  arch: string;
};

// What a project's session list says to resume, per part: the newest recorded
// session's id and the agent that owns it. There is no visible session list;
// each part has one rolling conversation, picked up where it left off. Built
// once per project open, then only read to seed columns.
type PartChat = { id: string | null; agent: string | null };
type ResumeState = { path: string; byPart: Record<string, PartChat> };

const NO_PARTS: Part[] = [];
const PROJECTS_FOLDER_KEY = "nurb-projects-folder";

// What the rail says about an assembly, or nothing for an ordinary part. An
// assembly that places nothing is still an assembly; it just has no list.
function assemblyLabel(part: Part) {
  if (!part.assembly) return undefined;
  return part.uses.length ? `assembly, places ${part.uses.join(", ")}` : "assembly";
}

// What a delete costs, worst first. An assembly reaches its parts by filename, so
// deleting one it places is not a dangling reference the app can repair: the next
// build of that assembly raises and the rail goes red. Say so before, not after.
function DeleteHints({ places }: { places: string[] }) {
  return (
    <>
      {places.length > 0 && (
        <span className="context-warn">
          {places.join(", ")} {places.length > 1 ? "place" : "places"} it and will stop
          building
        </span>
      )}
      <span className="context-hint">moves its files to the Trash</span>
    </>
  );
}

// The engine's cold start runs a heavy geometry-kernel import that can take minutes
// on a busy machine, and a static message over an empty window reads as a frozen app
// (issue #202: killed and reopened three times while the engine was still starting).
// A ticking count is the proof of life; the second line sets an honest expectation.
function EngineStarting() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);
  return (
    <div className="viewer-status">
      starting the CAD engine…
      {seconds >= 10 && (
        <div className="viewer-status-detail">
          {seconds}s — a cold start can take a few minutes when the computer is busy
        </div>
      )}
    </div>
  );
}

// Which assemblies place each part. Every assembly already carries its `uses`, so
// the other direction is a read of the list the rail has, not a second server call.
function placedInMap(parts: Part[]) {
  const map = new Map<string, string[]>();
  for (const part of parts) {
    if (!part.assembly) continue;
    for (const used of part.uses) {
      map.set(used, [...(map.get(used) ?? []), part.name]);
    }
  }
  return map;
}

// The sidebar columns, draggable at their seams (issue #103: overlays in the viewer
// had nowhere to go). Clamped so neither the labels nor the canvas can be crushed
// into uselessness; a width that keeps a column workable is the whole point of one.
const viewportWidth = () => document.documentElement.clientWidth;

function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsLoaded, setProjectsLoaded] = useState(false);
  const [servers, setServers] = useState<Record<string, Server>>({});
  const [opening, setOpening] = useState<Record<string, boolean>>({});
  const [active, setActive] = useState<string | null>(null);
  const [partState, setPartState] = useState<PartState | null>(null);
  // One explicit configuration click waiting for the loaded viewer. Kept out of
  // render state because delivery consumes it; the version wakes the effect when
  // the selected part itself did not change.
  const variantRequest = useRef<PartConfigurationRequest | null>(null);
  const [variantRequestVersion, setVariantRequestVersion] = useState(0);
  // The viewer's report of which variant the sliders started from, and whether they
  // have drifted off it. It is what keeps a drifted variant's rail row pinned.
  const [variantOrigin, setVariantOrigin] = useState<{ part: string; variant: string; drifted: boolean } | null>(null);
  const [naming, setNaming] = useState(false);
  const [creating, setCreating] = useState(false);
  const [partNaming, setPartNaming] = useState(false);
  const [partCreating, setPartCreating] = useState(false);
  const [menu, setMenu] = useState<
    | { kind: "project"; x: number; y: number; path: string }
    | { kind: "part"; x: number; y: number; part: string; armed?: boolean }
    | null
  >(null);
  const [error, setError] = useState<string | null>(null);
  const [resumeState, setResumeState] = useState<ResumeState | null>(null);
  // Chat columns opened this run. Columns stay mounted when the selection
  // moves away, so a part's agent keeps working in the background; only the
  // selected part's column is visible. A column whose agent is mid-turn even
  // survives a project switch (issue: creating a project used to kill a
  // 30-minute run in the previous one). A hidden completed column stays until
  // shown, preserving results and unsent drafts that session history cannot.
  const [columns, setColumns] = useState<ChatColumn[]>([]);
  const [busyChats, setBusyChats] = useState<Record<string, boolean>>({});
  // A ref for effects that must read the latest busy map without re-running on
  // every activity update.
  const busyRef = useRef(busyChats);
  busyRef.current = busyChats;
  // The project row's conversation covers the whole project; while it is focused
  // the viewer keeps showing the selected part, so this is chat focus, not selection.
  const [projectChatFocused, setProjectChatFocused] = useState(false);
  // Composer text waiting for the project chat, from the viewer's "unify in chat"
  // nudge. Prefilled, never sent: the lift stays the user's call.
  const [projectSeed, setProjectSeed] = useState<string | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([]);
  const [agentStatusState, setAgentStatusState] = useState<"loading" | "ready" | "error">("loading");
  const agentStatusRequests = useRef(createLatestRequestGate());
  const [signingIn, setSigningIn] = useState<string | null>(null);
  // A UI preference like the agent below, so it persists the same way.
  const [columnWidths, setColumnWidths] = useState(() =>
    initialColumns(
      {
        rail: Number(localStorage.getItem(COLUMNS.rail.key)),
        chat: Number(localStorage.getItem(COLUMNS.chat.key)),
      },
      viewportWidth(),
    ),
  );
  const { rail: railW, chat: chatW } = columnWidths;
  useEffect(() => {
    const fit = () =>
      setColumnWidths((current) => {
        const next = fitColumns(current, viewportWidth());
        if (next.rail === current.rail && next.chat === current.chat) return current;
        localStorage.setItem(COLUMNS.rail.key, String(next.rail));
        localStorage.setItem(COLUMNS.chat.key, String(next.chat));
        return next;
      });
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);
  // Pointer capture, not a mousemove listener on the window: the drag crosses the
  // viewer iframe, and capture is what keeps the moves coming once it does.
  const dragSeam = (e: ReactPointerEvent<HTMLDivElement>, which: Column) => {
    const handle = e.currentTarget;
    const startX = e.clientX;
    const from = columnWidths[which];
    let last = from;
    handle.setPointerCapture(e.pointerId);
    handle.classList.add("dragging");
    const move = (ev: PointerEvent) => {
      last = resizedColumn(
        which,
        from + ev.clientX - startX,
        columnWidths,
        viewportWidth(),
      );
      setColumnWidths((current) => ({ ...current, [which]: last }));
    };
    const up = () => {
      handle.classList.remove("dragging");
      handle.removeEventListener("pointermove", move);
      localStorage.setItem(COLUMNS[which].key, String(last));
    };
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", up, { once: true });
  };
  const resetSeam = (which: Column) => {
    localStorage.removeItem(COLUMNS[which].key);
    setColumnWidths((current) => ({
      ...current,
      [which]: resizedColumn(
        which,
        COLUMNS[which].fallback,
        current,
        viewportWidth(),
      ),
    }));
  };
  // Fresh conversations use this agent; existing ones keep the agent that ran
  // them. Persisted locally: it is a UI preference, not project state.
  const [defaultAgent, setDefaultAgent] = useState(
    () => localStorage.getItem("nurb-default-agent") ?? "claude",
  );
  // null while the check runs, false when first-launch provisioning has work
  // to do, true once the environment is healthy and the app can start.
  const [ready, setReady] = useState<boolean | null>(null);
  const bootstrapped = useRef(false);
  const [about, setAbout] = useState<AboutInfo | null>(null);
  const [showAbout, setShowAbout] = useState(false);
  const [showAgentsHelp, setShowAgentsHelp] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const geminiKeyResolver = useRef<((key: string | null) => void) | null>(null);
  const [defaultProjectsFolder, setDefaultProjectsFolder] = useState<string | null>(null);
  const [projectsFolder, setProjectsFolder] = useState<string | null>(
    () => localStorage.getItem(PROJECTS_FOLDER_KEY),
  );
  const [update, setUpdate] = useState<Update | null>(null);
  const [updating, setUpdating] = useState(false);
  // The one update this run acts on: found once, downloaded eagerly so the
  // restart is instant. `ready` resolves false if the background download
  // failed, in which case installing downloads again.
  const found = useRef<{ update: Update; ready: Promise<boolean> } | null>(null);

  useEffect(() => {
    invoke<boolean>("provision_status")
      .then(setReady)
      .catch(() => setReady(false));
  }, []);

  // Checks run outside the provisioning gate: an app whose first-run setup is
  // broken can still be rescued by an update. `tauri dev` serves the vite dev
  // build and skips the check entirely.
  const findUpdate = useCallback(async () => {
    if (!import.meta.env.PROD || found.current) return found.current?.update ?? null;
    const next = await check();
    if (next && !found.current) {
      found.current = { update: next, ready: next.download().then(() => true, () => false) };
      setUpdate(next);
    }
    return next;
  }, []);

  useEffect(() => {
    // At launch and every six hours after: the app stays open for days, and a
    // missing or unreachable endpoint fails silently on these timed checks.
    findUpdate().catch(() => {});
    const timer = setInterval(() => findUpdate().catch(() => {}), 6 * 60 * 60 * 1000);
    return () => clearInterval(timer);
  }, [findUpdate]);

  useEffect(() => {
    if (ready !== true) return;
    invoke<AboutInfo>("about_info").then(setAbout).catch(() => {});
    invoke<string>("default_projects_folder").then(setDefaultProjectsFolder).catch(() => {});
  }, [ready]);

  const installUpdate = useCallback(async () => {
    if (!found.current || updating) return;
    setUpdating(true);
    setError(null);
    try {
      const pending = found.current;
      if (await pending.ready) await pending.update.install();
      else await pending.update.downloadAndInstall();
      await relaunch();
    } catch (e) {
      setError(String(e));
      setUpdating(false);
    }
  }, [updating]);

  // The user-initiated check: the macOS "Check for Updates…" menu item and
  // the about box's button on every platform (Windows has no app menu).
  // Unlike the timed checks, this one answers even when there is nothing to
  // install.
  const checkForUpdates = useCallback(async () => {
    // The dev build never checks, so saying "newest version" would be a lie.
    if (!import.meta.env.PROD) return;
    try {
      const next = await findUpdate();
      if (!next) {
        await message("You're on the newest version.", { title: "nurb" });
      } else if (
        await ask(`nurb ${next.version} is ready to install.`, {
          title: "nurb",
          okLabel: "Restart & Update",
          cancelLabel: "Later",
        })
      ) {
        await installUpdate();
      }
    } catch (e) {
      setError(String(e));
    }
  }, [findUpdate, installUpdate]);

  useEffect(() => {
    const unlisten = listen("menu:check-updates", checkForUpdates);
    return () => {
      unlisten.then((fn) => fn());
    };
  }, [checkForUpdates]);

  // Two things the embedded viewer cannot do for itself. It forwards mousedowns
  // from its own top strip (the titlebar area lives inside the iframe, out of
  // data-tauri-drag-region's reach) and the shell starts the native window drag.
  // And its STL/STEP buttons write into the project's build folder, then hand
  // over the path: a webview ignores an <a download>, so the file is revealed in
  // Finder instead of downloaded.
  const focusProjectChat = useCallback((seed?: string) => {
    // The column itself mounts via the focus effect below, once the project's
    // session list has arrived.
    setProjectChatFocused(true);
    if (seed) setProjectSeed(seed);
  }, []);

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      if (!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(event.origin)) return;
      // The drag forward exists for the macOS overlay titlebar; Windows has a
      // real one, and a drag from the viewer's top strip should not move the
      // window there.
      if (event.data === "nurb:drag" && !isWindows)
        getCurrentWindow().startDragging().catch(() => {});
      if (event.data?.type === "nurb:saved" && typeof event.data.path === "string")
        revealItemInDir(event.data.path).catch(() => {});
      // The viewer's variant pin: the sliders started from a variant and may have
      // left it, and the rail draws its own variant rows, so it needs to know.
      if (event.data?.type === "nurb:variant")
        setVariantOrigin(
          typeof event.data.part === "string" && typeof event.data.variant === "string"
            ? { part: event.data.part, variant: event.data.variant, drifted: !!event.data.drifted }
            : null,
        );
      // The viewer's "unify in chat" nudge: parts repeating the same construction
      // are a project-wide matter, so it lands in the project conversation.
      if (
        event.data?.type === "nurb:shared" &&
        Array.isArray(event.data.parts) &&
        event.data.parts.every((p: unknown) => typeof p === "string")
      ) {
        const names = event.data.parts as string[];
        focusProjectChat(
          `The parts ${names.join(", ")} repeat the same construction. If it is genuinely shared, unify it so they stay in step.`,
        );
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [focusProjectChat]);

  const refreshAgents = useCallback(async () => {
    const isLatest = agentStatusRequests.current.begin();
    setAgentStatusState((state) => state === "ready" ? state : "loading");
    try {
      const statuses = await invoke<AgentStatus[]>("agent_statuses");
      if (!isLatest()) return;
      setAgentStatuses(statuses);
      setAgentStatusState("ready");
    } catch (e) {
      if (isLatest()) setAgentStatusState((state) => state === "ready" ? state : "error");
      throw e;
    }
  }, []);

  useEffect(() => {
    if (ready === true) refreshAgents().catch(() => {});
  }, [ready, refreshAgents]);

  // Signing in happens in a terminal or a browser, outside this window, so
  // coming back is the moment to notice it.
  useEffect(() => {
    if (ready !== true) return;
    const onFocus = () => refreshAgents().catch(() => {});
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [ready, refreshAgents]);

  const chooseAgent = (id: string) => {
    setDefaultAgent(id);
    localStorage.setItem("nurb-default-agent", id);
  };

  const requestGeminiKey = () =>
    new Promise<string | null>((resolve) => {
      geminiKeyResolver.current = resolve;
      setShowGeminiKey(true);
    });

  const finishGeminiKey = (key: string | null) => {
    setShowGeminiKey(false);
    geminiKeyResolver.current?.(key);
    geminiKeyResolver.current = null;
  };

  const signInAgent = async (id: string): Promise<boolean> => {
    const apiKey = id === "gemini" ? await requestGeminiKey() : null;
    if (id === "gemini" && apiKey === null) return false;
    setSigningIn(id);
    setError(null);
    try {
      await invoke("agent_login", { agent: id, apiKey });
      await refreshAgents();
      return true;
    } catch (e) {
      setError(String(e));
      throw e;
    } finally {
      setSigningIn(null);
    }
  };

  const refreshProjects = useCallback(async () => {
    const list = await invoke<Project[]>("list_projects");
    setProjects(list);
    setProjectsLoaded(true);
    return list;
  }, []);

  const changeProjectsFolder = async (folder: string | null) => {
    setProjectsFolder(folder);
    if (folder) localStorage.setItem(PROJECTS_FOLDER_KEY, folder);
    else localStorage.removeItem(PROJECTS_FOLDER_KEY);

    const selected =
      folder ?? defaultProjectsFolder ?? await invoke<string>("default_projects_folder");
    if (!defaultProjectsFolder && !folder) setDefaultProjectsFolder(selected);
    if (
      !(await ask("Load existing nurb projects directly inside this folder?", {
        title: "Projects folder changed",
        okLabel: "Load Projects",
        cancelLabel: "Not Now",
      }))
    ) return;

    try {
      const loaded = await invoke<string[]>("add_projects_from_folder", { folder: selected });
      await refreshProjects();
      if (loaded.length === 0) {
        await message("No nurb projects were found directly inside that folder.", {
          title: "Projects folder",
        });
      }
    } catch (e) {
      setError(String(e));
    }
  };

  const openProject = useCallback(
    async (path: string) => {
      setActive(path);
      setError(null);
      setOpening((o) => ({ ...o, [path]: true }));
      try {
        const server = await invoke<Server>("open_project", { path });
        setServers((s) => ({ ...s, [path]: server }));
        await refreshProjects();
      } catch (e) {
        setError(String(e));
      } finally {
        setOpening((o) => {
          const { [path]: _, ...rest } = o;
          return rest;
        });
      }
    },
    [refreshProjects],
  );

  useEffect(() => {
    if (ready !== true || bootstrapped.current) return;
    bootstrapped.current = true;
    refreshProjects().then((list) => {
      // The list is alphabetical; restore the most recently opened project.
      const recent = list
        .filter((p) => !p.missing)
        .sort((a, b) => b.lastOpened - a.lastOpened)[0];
      if (recent) openProject(recent.path);
    });
  }, [ready, refreshProjects, openProject]);

  // The parent page cannot join the viewer's websocket (the server only admits
  // its own origin), so the parts list refreshes on a light poll instead.
  const activeServer = active ? servers[active] : undefined;
  useEffect(() => {
    if (!active || !activeServer) {
      setPartState(null);
      return;
    }
    setPartState(null);
    let stale = false;
    const recovery = createPartRecovery(() => openProject(active));
    const fetchParts = async () => {
      try {
        const entries = await invoke<Part[]>("list_parts", { path: active });
        if (stale) return;
        recovery.success();
        setPartState({
          path: active,
          parts: entries
            .map(({ name, error, refused, assembly, uses, variants, variant }) => ({ name, error, refused, assembly, uses, variants, variant }))
            .sort((a, b) => a.name.localeCompare(b.name)),
        });
      } catch {
        if (stale) return;
        // A brief failure is the server restarting after a save. A run of them
        // means the engine died, and nothing else ever respawns it. Opening the
        // project is a no-op while the server is alive, so a false positive is
        // cheap, and clearing the count means another full run of failures has
        // to pass before the next attempt.
        recovery.failure();
      }
    };
    fetchParts();
    const timer = setInterval(fetchParts, 2500);
    return () => {
      stale = true;
      recovery.stop();
      clearInterval(timer);
    };
  }, [active, activeServer, openProject]);

  const parts = partState?.path === active ? partState.parts : NO_PARTS;
  const placedIn = useMemo(() => placedInMap(parts), [parts]);

  // Opening a project silently resumes each part's conversation: the newest
  // session recorded against that part (one short-lived adapter call, not
  // polled). Sessions with no recorded part, or a failed listing (logged out,
  // an agent without session listing), just mean fresh chats.
  useEffect(() => {
    setResumeState(null);
    setVariantOrigin(null);   // the pin belongs to the viewer this project just left
    // Leaving a project keeps busy columns and hidden results. Ordinary idle
    // columns go now; an unseen one goes after its exact chat has been shown.
    setColumns((list) => retainChatColumns(list, active, busyRef.current));
    setPartNaming(false);
    setProjectChatFocused(false);
    setProjectSeed(null);
    if (!active) return;
    let stale = false;
    invoke<ChatInfo[]>("list_sessions", { path: active })
      .then((list) => {
        if (stale) return;
        const byPart: Record<string, PartChat> = {};
        for (const entry of list) {
          // Newest first, so the first session seen per part wins.
          if (entry.part && !byPart[entry.part]) {
            byPart[entry.part] = { id: entry.id, agent: entry.agent };
          }
        }
        setResumeState({ path: active, byPart });
      })
      .catch(() => {
        if (!stale) setResumeState({ path: active, byPart: {} });
      });
    return () => {
      stale = true;
    };
  }, [active]);


  // Added projects have no selection, and a selected source can be deleted while
  // the app is closed. Keep the registry, rail, viewer, and chat on the same real
  // source; list_parts includes files whose first build is still running.
  useEffect(() => {
    if (!active || partState?.path !== active) return;
    const project = projects.find((entry) => entry.path === active);
    if (!project) return;
    const selected = project.selectedPart;
    if (selected && parts.some((part) => part.name === selected)) return;
    const fallback = parts[0]?.name;
    if (selected === fallback) return;
    setProjects((list) =>
      list.map((entry) =>
        entry.path === active ? { ...entry, selectedPart: fallback } : entry,
      ),
    );
    invoke("select_part", { path: active, part: fallback ?? null }).catch((e) =>
      setError(String(e)),
    );
  }, [active, partState, parts, projects]);

  // A deleted or renamed source has no rail row that can reveal its chat.
  // Unmount that column so its adapter and any pending permission request do
  // not survive invisibly until the whole project closes. The busy flag
  // clears itself on unmount.
  useEffect(() => {
    if (!active || partState?.path !== active) return;
    const live = new Set(partState.parts.map((part) => part.name));
    live.add(PROJECT_CHAT); // no rail part backs it, but its row never goes away
    setColumns((list) => {
      const kept = list.filter((col) => col.path !== active || live.has(col.part));
      return kept.length === list.length ? list : kept;
    });
  }, [active, partState]);

  const removeProject = async (path: string) => {
    // Removed projects lose their columns even mid-turn; there is no rail row
    // left to ever show the result.
    setColumns((list) => list.filter((col) => col.path !== path));
    await invoke("remove_project", { path });
    setServers((s) => {
      const { [path]: _, ...rest } = s;
      return rest;
    });
    if (active === path) setActive(null);
    await refreshProjects();
  };

  const createNamed = useCallback(
    async (name: string) => {
      if (!name || creating) return;
      setCreating(true);
      setError(null);
      try {
        const path = await invoke<string>("create_project", { name, folder: projectsFolder });
        setNaming(false);
        await refreshProjects();
        openProject(path);
      } catch (e) {
        setError(String(e));
      } finally {
        setCreating(false);
      }
    },
    [creating, projectsFolder, refreshProjects, openProject],
  );

  const createProject = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const name = new FormData(event.currentTarget).get("name")?.toString().trim();
    if (name) createNamed(name);
  };

  // Debug-build automation only: the loopback test hook forwards a project
  // name because AX cannot type into WKWebView inputs. The event never fires
  // in release builds (the hook is not compiled into them).
  useEffect(() => {
    const unlisten = listen<string>("test-create", (event) => {
      createNamed(event.payload.trim());
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  }, [createNamed]);

  // Same hook: "open:<name>" switches to a listed project, which AX cannot
  // do either (the rail's rows are list items, not buttons).
  useEffect(() => {
    const unlisten = listen<string>("test-open", (event) => {
      const name = event.payload.trim();
      const project = projects.find((entry) => entry.name === name);
      if (project) openProject(project.path);
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  }, [projects, openProject]);

  const addExisting = async () => {
    const picked = await pickFolder({ directory: true });
    if (typeof picked !== "string") return;
    setError(null);
    try {
      const path = await invoke<string>("add_project", { path: picked });
      await refreshProjects();
      openProject(path);
    } catch (e) {
      setError(String(e));
    }
  };

  const activeProject = projects.find((p) => p.path === active);
  const savedPart = activeProject?.selectedPart;
  const selectedPart = savedPart && parts.some((part) => part.name === savedPart)
    ? savedPart
    : parts[0]?.name;
  const partsReady = partState?.path === active;

  // Only the active project's focused chat shows; every other column stays
  // mounted but hidden so its turn keeps streaming. The viewer-side gates
  // (server up, parts listed, project present) put the placeholder up instead.
  const visiblePart =
    active && activeServer && partsReady && !activeProject?.missing
      ? projectChatFocused
        ? PROJECT_CHAT
        : selectedPart
      : null;
  const visibleChatKey = active && visiblePart ? chatKey(active, visiblePart) : null;
  const columnVisible = (col: ChatColumn) =>
    visibleChatKey === chatKey(col.path, col.part);

  // A hidden result has now actually painted. It can return to the ordinary
  // idle-column lifecycle and be torn down the next time its project is left.
  useEffect(() => {
    if (!active || !visiblePart) return;
    setColumns((list) => markChatSeen(list, active, visiblePart));
  }, [active, visiblePart]);

  // Opening a chat column waits for the project's session list, then seeds
  // the column with the conversation to resume. A column that survived a
  // project switch is already in the list and is left alone, mid-stream.
  const openChat = useCallback(
    (part: string) => {
      if (!active || resumeState?.path !== active) return;
      const seed = resumeState.byPart[part];
      setColumns((list) =>
        list.some((col) => col.path === active && col.part === part)
          ? list
          : [
              ...list,
              {
                path: active,
                part,
                agent: seed?.agent ?? null,
                resume: seed?.id ?? null,
                gen: 0,
                unseen: false,
              },
            ],
      );
    },
    [active, resumeState],
  );

  // Selecting a part opens (and keeps open) its chat column.
  useEffect(() => {
    if (selectedPart) openChat(selectedPart);
  }, [openChat, selectedPart]);

  // Focusing the project conversation opens its column the same way.
  useEffect(() => {
    if (projectChatFocused) openChat(PROJECT_CHAT);
  }, [openChat, projectChatFocused]);

  // The part row is the defaults configuration, so selecting it clears any
  // variant; a variant row passes its name and the viewer loads its overrides.
  const selectPart = (name: string, variant?: string) => {
    if (!active) return;
    setProjectChatFocused(false);
    variantRequest.current = { path: active, part: name, variant: variant ?? null };
    setVariantRequestVersion((version) => version + 1);
    setProjects((list) =>
      list.map((p) => (p.path === active ? { ...p, selectedPart: name } : p)),
    );
    invoke("select_part", { path: active, part: name });
  };

  // Part files change on disk the moment create/delete returns, but the
  // server's watcher registers them asynchronously. Poll until the listing
  // settles (or give up and take what the server says) before committing, so
  // the selection-fallback effect never acts on a stale list.
  const syncParts = async (path: string, settled: (parts: Part[]) => boolean) => {
    for (let attempt = 0; ; attempt++) {
      const entries = await invoke<Part[]>("list_parts", { path });
      const listed = entries
        .map(({ name, error, refused, assembly, uses, variants, variant }) => ({ name, error, refused, assembly, uses, variants, variant }))
        .sort((a, b) => a.name.localeCompare(b.name));
      if (settled(listed) || attempt >= 19) {
        setPartState({ path, parts: listed });
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  };

  const createPart = async (name: string) => {
    if (!active || partCreating) return;
    setPartCreating(true);
    setError(null);
    try {
      const created = await invoke<string>("create_part", { path: active, name });
      setPartNaming(false);
      await syncParts(active, (listed) => listed.some((part) => part.name === created));
      selectPart(created);
    } catch (e) {
      setError(String(e));
    } finally {
      setPartCreating(false);
    }
  };

  const deletePart = async (part: string) => {
    if (!active) return;
    setError(null);
    try {
      await invoke("delete_part", { path: active, part });
      await syncParts(active, (listed) => listed.every((p) => p.name !== part));
    } catch (e) {
      setError(String(e));
    }
  };

  const createPartSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const name = new FormData(event.currentTarget).get("name")?.toString().trim();
    if (name) createPart(name);
  };

  // Bump the part's generation to remount its column without a session to
  // resume. With no agent named ("start fresh") the agent resets too, so the
  // new conversation takes the current default; naming one pins it, which is
  // how the chat header switches agents. Either way the old conversation stays
  // in its agent's own store.
  const startFresh = async (path: string, part: string, agent: string | null = null) => {
    try {
      // Persist the empty selection before remounting. Otherwise quitting
      // before the first new prompt would restore the old newest session.
      await invoke("select_part_chat", {
        path,
        part,
        sessionId: null,
      });
    } catch (e) {
      setError(String(e));
      return;
    }
    setColumns((list) =>
      list.map((col) =>
        col.path === path && col.part === part
          ? { ...col, resume: null, agent, gen: col.gen + 1 }
          : col,
      ),
    );
  };

  // Track live session ids so switching parts and back resumes the same
  // conversation even before the agent's store has it listed. Pinning the
  // agent here is what keeps a conversation on the agent that started it
  // when the default changes later.
  const chatStarted = (path: string, part: string, id: string, agent: string) => {
    // A session exists before its first prompt is stored by the adapter. Keep
    // that id as the part's choice now, so a failed/abandoned first prompt does
    // not resurrect the conversation that "start fresh" set aside.
    invoke("select_part_chat", { path, part, sessionId: id }).catch((e) =>
      setError(String(e)),
    );
    setColumns((list) =>
      list.map((col) =>
        col.path === path && col.part === part ? { ...col, resume: id, agent } : col,
      ),
    );
  };

  const chatBusy = (
    path: string,
    part: string,
    agent: string,
    busy: boolean,
    visible: boolean,
  ) => {
    const key = chatKey(path, part);
    const wasBusy = Boolean(busyRef.current[key]);
    setBusyChats((map) => {
      if (busy) return { ...map, [key]: true };
      if (!(key in map)) return map;
      const { [key]: _, ...rest } = map;
      return rest;
    });
    // Pin a fresh column before adapter startup can overlap a default-agent
    // change. Hidden completions remain mounted until the user sees them: an
    // auth failure's restored draft and error have no session to reload.
    setColumns((list) =>
      updateChatActivity(list, path, part, agent, busy, visible, wasBusy),
    );
  };

  // ?embed hides the viewer's own title and part list; the rail is the one
  // place parts live in the app. The src is pinned per project: WKWebView
  // suspends requestAnimationFrame in an iframe that is navigated in place, so
  // following the selection with the URL freezes the canvas. The iframe loads
  // once per server and part switches travel by postMessage instead.
  const frameRef = useRef<HTMLIFrameElement | null>(null);
  const [frame, setFrame] = useState<{ key: string; src: string } | null>(null);
  const [loadedFrame, setLoadedFrame] = useState<{ key: string; token: number } | null>(null);
  useEffect(() => {
    if (!activeServer || !partsReady) {
      setFrame(null);
      return;
    }
    setFrame((prev) =>
      prev?.key === activeServer.url
        ? prev
        : {
            key: activeServer.url,
            src: selectedPart
              ? `${activeServer.url}/?embed&part=${encodeURIComponent(selectedPart)}`
              : `${activeServer.url}/?embed`,
          },
    );
  }, [activeServer, partsReady, selectedPart]);

  // A request belongs to the project where it was clicked. Do not carry it out
  // and back across a project switch, where it would overwrite newer viewer state.
  useEffect(() => {
    if (variantRequest.current?.path !== active) variantRequest.current = null;
  }, [active]);

  const postPart = useCallback(() => {
    if (!frame || loadedFrame?.key !== frame.key || !active || !selectedPart) return;
    const request = variantRequest.current;
    const { message, consumed } = partMessage(active, selectedPart, request);
    // Any other current selection makes an older request stale. Consume before
    // posting so React's development effect replay cannot send it twice.
    if (request && (consumed || request.path !== active || request.part !== selectedPart)) {
      variantRequest.current = null;
    }
    frameRef.current?.contentWindow?.postMessage(
      message,
      frame.key,
    );
  }, [frame, loadedFrame, selectedPart, active, variantRequestVersion]);
  useEffect(postPart, [postPart]);

  if (ready !== true) {
    // The status check settles in well under a second; until then the window
    // shows the app background, never a flash of the setup screen.
    return ready === false ? <Setup onDone={() => setReady(true)} /> : <div className="setup" />;
  }

  return (
    <div
      className="shell"
      style={{ gridTemplateColumns: `${railW}px ${chatW}px minmax(0, 1fr)` }}
    >
      <aside className="rail">
        <div className="rail-title" data-tauri-drag-region />
        <div className="rail-heading">
          <span>projects</span>
          <button className="rail-button" title="new project" onClick={() => setNaming(true)}>
            +
          </button>
        </div>
        {naming && (
          <form className="name-form" onSubmit={createProject}>
            <input
              className="name-input"
              name="name"
              placeholder="project name"
              autoCapitalize="off"
              autoCorrect="off"
              spellCheck={false}
              disabled={creating}
              autoFocus
              onKeyDown={(e) => e.key === "Escape" && setNaming(false)}
            />
            <button className="rail-button" type="submit" disabled={creating}>
              {creating ? "creating…" : "create"}
            </button>
          </form>
        )}
        <div className="projects">
          {projects.map((project) => (
            <div key={project.path}>
              <div
                className={`project-row ${project.path === active ? "active" : ""} ${project.missing ? "missing" : ""}`}
                onClick={() => !project.missing && openProject(project.path)}
                onContextMenu={(e) => {
                  e.preventDefault();
                  setMenu({ kind: "project", x: e.clientX, y: e.clientY, path: project.path });
                }}
              >
                <IconFolder />
                <span className="project-name">{project.name}</span>
                {project.missing ? (
                  <span className="tag">missing</span>
                ) : opening[project.path] ? (
                  <span className="tag">starting…</span>
                ) : null}
                {project.path !== active &&
                  Object.keys(busyChats).some((key) =>
                    key.startsWith(chatKey(project.path, "")),
                  ) && (
                    // The dot the part rows wear, lifted to the project row:
                    // an agent is still working here in the background.
                    <span
                      className="part-busy"
                      title="the agent is still working in this project"
                    />
                  )}
                {project.path !== active &&
                  !Object.keys(busyChats).some((key) =>
                    key.startsWith(chatKey(project.path, "")),
                  ) &&
                  columns.some((col) => col.path === project.path && col.unseen) && (
                    <span
                      className="part-unseen"
                      title="the agent finished in this project"
                    />
                  )}
              </div>
              {project.path === active && partsReady && (
                <ul className="parts">
                  {/* The whole-project conversation: spawn parts, set what the
                      family shares, act on the duplication nudge. Chat focus, not
                      part selection, so the viewer stays on the selected part. */}
                  <li
                    className={`part-row project-chat ${projectChatFocused ? "selected" : ""}`}
                    title="a conversation about the whole project"
                    onClick={() => focusProjectChat()}
                  >
                    <IconCubes label="the whole project" />
                    <span className="part-name">project</span>
                    {busyChats[chatKey(project.path, PROJECT_CHAT)] ? (
                      <span className="part-busy" title="the agent is working on the project" />
                    ) : columns.some(
                        (col) =>
                          col.path === project.path &&
                          col.part === PROJECT_CHAT &&
                          col.unseen,
                      ) ? (
                      <span className="part-unseen" title="the agent finished on the project" />
                    ) : null}
                  </li>
                  {parts.map((part) => (
                    <Fragment key={part.name}>
                      <li
                        className={`part-row ${part.name === selectedPart ? "selected" : ""} ${part.assembly ? "assembly" : ""}`}
                        // One string for the hover and the accessible name of the
                        // mark, because a row that reads as a part to a screen
                        // reader is the same miss the plain cube icon was.
                        title={assemblyLabel(part)}
                        onClick={() => selectPart(part.name)}
                        onContextMenu={(e) => {
                          e.preventDefault();
                          setMenu({ kind: "part", x: e.clientX, y: e.clientY, part: part.name });
                        }}
                      >
                        {part.assembly ? <IconCubes label={assemblyLabel(part)} /> : <IconCube />}
                        <span className="part-name">{part.name}</span>
                        {busyChats[chatKey(project.path, part.name)] ? (
                          <span className="part-busy" title="the agent is working on this part" />
                        ) : columns.some(
                            (col) =>
                              col.path === project.path &&
                              col.part === part.name &&
                              col.unseen,
                          ) ? (
                          <span className="part-unseen" title="the agent finished on this part" />
                        ) : null}
                        {part.error && (
                          // A refusal is the part declining a configuration, not
                          // breaking, so it wears amber like the viewer's own mark.
                          <span
                            className={part.refused ? "part-refused" : "part-error"}
                            title={part.error}
                          >
                            !
                          </span>
                        )}
                        {/* Folded-away variants still say how many there are, so the
                            rail does not hide them without a trace. */}
                        {part.variants.length > 0 && part.name !== selectedPart && (
                          <span className="var-count">
                            <IconVariant size={9} />
                            {part.variants.length}
                          </span>
                        )}
                      </li>
                      {/* The card's variants nest under their part the way the
                          browser viewer draws them: the same part at other values,
                          wearing the sliders glyph. They unfold under the selection
                          only, because twenty parts' variants at once is a wall. The
                          active mark follows the server's resolved variant, so it
                          tracks slider drags and agent edits too, one poll behind. */}
                      {part.name === selectedPart &&
                        part.variants.map((v) => {
                          const how = Object.entries(v.params)
                            .map(([k, val]) => `${k} = ${val}`)
                            .join("\n");
                          // Drifted off this variant: no longer resolved by the server,
                          // but still where the work is, so the row stays pinned.
                          const modified =
                            part.variant !== v.name &&
                            variantOrigin?.drifted === true &&
                            variantOrigin.part === part.name &&
                            variantOrigin.variant === v.name;
                          return (
                            <li
                              key={`${part.name}:${v.name}`}
                              className={`part-var ${part.variant === v.name ? "selected" : ""} ${modified ? "modified" : ""}`}
                              title={v.note ? `${v.note}\n\n${how}` : how}
                              onClick={() => selectPart(part.name, v.name)}
                            >
                              <IconVariant />
                              <span className="part-name">{v.name}</span>
                            </li>
                          );
                        })}
                      {/* The selection expands to its counterparts: the assemblies
                          that place this part, or the parts this assembly places.
                          Only under the selection, because the relationship is what
                          you want while looking at one thing and clutter on the
                          other twenty rows. Each is a link, so the rail walks a
                          placement in both directions. */}
                      {part.name === selectedPart &&
                        (part.assembly ? part.uses : placedIn.get(part.name) ?? []).map((other) => (
                          <li
                            key={other}
                            className="part-link"
                            // The icon is the relation. A part can only be placed by
                            // an assembly and never the reverse, so which end this is
                            // says which way the placement runs, and the row keeps its
                            // full width for the name. The rail is narrow enough that
                            // holder_paper_towel and holder_paper_towel_arm truncate
                            // to the same string once a word sits in front of them.
                            title={
                              part.assembly
                                ? `${part.name} places ${other}`
                                : `${other} places ${part.name}`
                            }
                            onClick={() => selectPart(other)}
                          >
                            {part.assembly ? <IconCube size={11} /> : <IconCubes size={12} />}
                            <span className="part-name">{other}</span>
                          </li>
                        ))}
                    </Fragment>
                  ))}
                  <li className="part-new">
                    {partNaming ? (
                      <form className="name-form" onSubmit={createPartSubmit}>
                        <input
                          className="name-input"
                          name="name"
                          placeholder="part name"
                          autoCapitalize="off"
                          autoCorrect="off"
                          spellCheck={false}
                          disabled={partCreating}
                          autoFocus
                          onKeyDown={(e) => e.key === "Escape" && setPartNaming(false)}
                        />
                        <button className="rail-button" type="submit" disabled={partCreating}>
                          {partCreating ? "creating…" : "create"}
                        </button>
                      </form>
                    ) : (
                      <button className="part-add" onClick={() => setPartNaming(true)}>
                        + new part…
                      </button>
                    )}
                  </li>
                </ul>
              )}
            </div>
          ))}
        </div>
        <button className="rail-add" onClick={addExisting}>
          <IconFolderPlus />
          add existing…
        </button>
        {error && <div className="rail-error">{error}</div>}
        <div className="rail-foot">
          {update && (
            <button className="rail-update" disabled={updating} onClick={installUpdate}>
              {updating ? "updating…" : `update to ${update.version}`}
            </button>
          )}
          <div className="rail-foot-row">
            {about && (
              <button className="rail-version" onClick={() => setShowAbout(true)}>
                nurb {about.appVersion}
              </button>
            )}
            <button
              className="rail-settings"
              title="settings"
              aria-label="settings"
              onClick={() => setShowSettings(true)}
            >
              <IconGear />
            </button>
          </div>
        </div>
      </aside>
      {menu && (
        <div
          className="menu-overlay"
          onMouseDown={() => setMenu(null)}
          onContextMenu={(e) => {
            e.preventDefault();
            setMenu(null);
          }}
        >
          <div
            className="context-menu"
            style={{ left: menu.x, top: menu.y }}
            onMouseDown={(e) => e.stopPropagation()}
          >
            {menu.kind === "project" ? (
              <button
                className="context-item"
                onClick={() => {
                  removeProject(menu.path);
                  setMenu(null);
                }}
              >
                remove from sidebar
                <span className="context-hint">the files stay on disk</span>
              </button>
            ) : menu.armed ? (
              <button
                className="context-item danger"
                onClick={() => {
                  deletePart(menu.part);
                  setMenu(null);
                }}
              >
                really delete {menu.part}?
                <DeleteHints places={placedIn.get(menu.part) ?? []} />
              </button>
            ) : (
              // Arming instead of deleting keeps the recovery path inside the
              // app: closing the menu is the "no".
              <button
                className="context-item"
                onClick={() => setMenu({ ...menu, armed: true })}
              >
                delete part
                <DeleteHints places={placedIn.get(menu.part) ?? []} />
              </button>
            )}
          </div>
        </div>
      )}
      {showSettings && (
        <Settings
          folder={projectsFolder ?? defaultProjectsFolder ?? "~/Documents/nurb"}
          customized={projectsFolder !== null}
          onChange={changeProjectsFolder}
          onReset={() => changeProjectsFolder(null)}
          agents={agentStatuses.filter((status) => status.installed)}
          agentStatusState={agentStatusState}
          signingIn={signingIn}
          onSignIn={signInAgent}
          onMoreAgents={() => {
            setShowSettings(false);
            setShowAgentsHelp(true);
          }}
          onClose={() => setShowSettings(false)}
        />
      )}
      {showGeminiKey ? (
        <GeminiKeyDialog
          onSubmit={(key) => finishGeminiKey(key)}
          onClose={() => finishGeminiKey(null)}
        />
      ) : null}
      {showAbout && about && (
        <About
          appVersion={about.appVersion}
          nurbVersion={about.nurbVersion}
          occtVersion={about.occtVersion}
          osVersion={about.osVersion}
          arch={about.arch}
          onClose={() => setShowAbout(false)}
          onCheckUpdates={checkForUpdates}
        />
      )}
      {showAgentsHelp && (
        <AgentsHelp
          missing={agentStatuses.filter((status) => !status.installed)}
          onClose={() => {
            setShowAgentsHelp(false);
            // The user may have just run an installer; notice it now, not on
            // the next launch.
            refreshAgents().catch(() => {});
          }}
        />
      )}
      {/* One column per opened chat, all mounted so background turns keep
          streaming; only the active project's focused chat is visible. Keyed
          by project, part, and generation: starting fresh remounts a column
          (and its adapter); switching parts or projects does not. */}
      {columns.map((col) => {
        const agent = col.agent ?? defaultAgent;
        const isProject = col.part === PROJECT_CHAT;
        return (
          <Chat
            key={`${col.path}:${col.part}:${col.gen}:${agent}`}
            path={col.path}
            part={col.part}
            agent={agent}
            agents={agentStatuses
              // Settings lists uninstalled agents with an install hint; the
              // switcher only offers ones that can actually run.
              .filter((status) => status.installed)
              .map((status) => ({
                id: status.id,
                label: AGENT_LABEL[status.id] ?? status.label,
                loggedIn: status.loggedIn,
              }))}
            resume={col.resume}
            hidden={!columnVisible(col)}
            seed={isProject && col.path === active ? projectSeed : null}
            onSeed={isProject ? () => setProjectSeed(null) : undefined}
            onSession={(id) => chatStarted(col.path, col.part, id, agent)}
            onFresh={() => startFresh(col.path, col.part)}
            onAgent={(id, unstarted) => {
              // Picking an agent before the first message is choosing which
              // agent you work with, so it sticks for later chats too.
              if (unstarted) chooseAgent(id);
              startFresh(col.path, col.part, id);
            }}
            onBusy={(busy) =>
              chatBusy(col.path, col.part, agent, busy, columnVisible(col))
            }
            onSignIn={signInAgent}
          />
        );
      })}
      {!columns.some(columnVisible) && (
        <section className="chat">
          <div className="chat-header" data-tauri-drag-region />
          {projectsLoaded && projects.length === 0 ? (
            // The zero-project welcome: the one moment the app has to explain
            // itself, so the create form lives here, not behind the rail's +.
            <div className="welcome">
              <Logo size={36} />
              <div className="welcome-title">Design your first part</div>
              <p className="welcome-copy">
                A project holds the parts you design. Name it, then describe
                what you want to make.
              </p>
              <form className="name-form welcome-form" onSubmit={createProject}>
                <input
                  className="name-input"
                  name="name"
                  placeholder="project name"
                  autoCapitalize="off"
                  autoCorrect="off"
                  spellCheck={false}
                  disabled={creating}
                />
                <button className="rail-button welcome-create" type="submit" disabled={creating}>
                  {creating ? "creating…" : "create"}
                </button>
              </form>
              <button className="welcome-existing" onClick={addExisting}>
                or add an existing folder…
              </button>
            </div>
          ) : (
            <div className="placeholder">chat</div>
          )}
        </section>
      )}
      <main className="viewer">
        {frame ? (
          <iframe
            key={frame.key}
            ref={frameRef}
            className="viewer-frame"
            src={frame.src}
            title="nurb viewer"
            // The selection can move while the document is still loading and a
            // message posted into a loading frame is dropped; repeat it on load.
            onLoad={() =>
              setLoadedFrame((loaded) => ({
                key: frame.key,
                token: (loaded?.token ?? 0) + 1,
              }))
            }
          />
        ) : active && opening[active] ? (
          <EngineStarting />
        ) : (
          <div className="viewer-status">
            {projectsLoaded && projects.length === 0
              ? "create a project to start"
              : "open a project to start"}
          </div>
        )}
      </main>
      <div
        className="seam"
        style={{ left: railW }}
        title="drag to resize; double-click to reset"
        onPointerDown={(e) => dragSeam(e, "rail")}
        onDoubleClick={() => resetSeam("rail")}
      />
      <div
        className="seam seam-chat"
        style={{ left: railW + chatW }}
        title="drag to resize; double-click to reset"
        onPointerDown={(e) => dragSeam(e, "chat")}
        onDoubleClick={() => resetSeam("chat")}
      />
    </div>
  );
}

export default App;
