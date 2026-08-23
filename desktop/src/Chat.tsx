import {
  FormEvent,
  KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { Channel, invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWebview } from "@tauri-apps/api/webview";
import { open } from "@tauri-apps/plugin-dialog";
import { IconChevronDown, IconMessagePlus, IconPaperclip } from "./Icons";
import Markdown from "./Markdown";
import { playChime, shouldPlayCompletionChime } from "./chime";
import { restoreDraftFiles, restoreDraftText } from "./chatDraft";

// The whole-project conversation rides the per-part plumbing under a name no part
// file can have. Twins live in App.tsx's mount and acp.rs's context line.
export const PROJECT_CHAT = "//project";

// Mirrors ChatEvent in src-tauri/src/acp.rs.
type ChatEvent =
  | { type: "user_text"; text: string }
  | { type: "agent_text"; text: string }
  | { type: "agent_thought"; text: string }
  | { type: "session_info"; title: string | null }
  | { type: "note"; text: string }
  | { type: "tool_call"; id: string; title: string; kind?: string; status: string; input?: string; output?: string }
  | { type: "tool_call_update"; id: string; title?: string; status?: string; input?: string; output?: string }
  | { type: "plan"; entries: PlanEntry[] }
  | { type: "permission_request"; id: number; title: string; options: PermissionOption[] }
  | { type: "permission_resolved"; id: number }
  | { type: "session_error"; message: string };

type PlanEntry = { content: string; status: string };
type PermissionOption = { optionId: string; name: string; kind: string };

type Item =
  | { kind: "user"; text: string; files?: string[]; localId?: number }
  | { kind: "agent"; text: string }
  | { kind: "thought"; text: string }
  | { kind: "tool"; id: string; title: string; toolKind?: string; status: string; input?: string; output?: string }
  | { kind: "plan"; entries: PlanEntry[] }
  | { kind: "note"; text: string };

type Permission = { id: number; title: string; options: PermissionOption[] };

// Mirrors ConfigRow in src-tauri/src/prefs.rs: the model and effort selects,
// as the agent itself describes them.
type ConfigChoice = { value: string; name: string; description?: string };
type ConfigRow = {
  id: string;
  // "model" or "thought_level": the key the app addresses a row by, since the
  // agents name the options themselves differently.
  category: string;
  name: string;
  value: string;
  options: ConfigChoice[];
};

// Mirrors AgentKind::label in src-tauri/src/agents.rs.
export const AGENT_LABEL: Record<string, string> = {
  claude: "Claude",
  codex: "Codex",
  gemini: "Gemini",
  cursor: "Cursor",
  grok: "Grok",
};

const TOOL_STATUS_LABEL: Record<string, string> = {
  pending: "waiting",
  in_progress: "working…",
  completed: "done",
  failed: "failed",
};

// Tool titles arrive as developer-speak ("Edit parts/lid.py", "nurb check").
// The app's audience is hobbyists, so cards and permission dialogs translate
// what they can into plain activity language and fall back to the raw title,
// which stays untouched in state and in the debug event log.
const FILE_TITLE = /^(Read|Edit|Write)\s+(?:.*\/)?parts\/([A-Za-z0-9_]+)\.py$/;
const NURB_TITLE = /^(?:uv run\s+)?nurb\s+([a-z]+)/;
const FILE_VERBS: Record<string, [string, string]> = {
  Read: ["looking at", "look at"],
  Edit: ["editing", "edit"],
  Write: ["creating", "create"],
};
const NURB_VERBS: Record<string, [string, string]> = {
  build: ["building the part", "build the part"],
  check: ["checking printability", "check printability"],
  inspect: ["inspecting the part", "inspect the part"],
  verify: ["double-checking the part", "double-check the part"],
  compare: ["measuring against the original", "measure against the original"],
  render: ["rendering a preview", "render a preview"],
  export: ["exporting print files", "export print files"],
  rules: ["reading the design rules", "read the design rules"],
  api: ["checking the toolbox", "check the toolbox"],
  card: ["updating the part's notes", "update the part's notes"],
};
const KIND_VERBS: Record<string, [string, string]> = {
  read: ["reading project files", "read project files"],
  edit: ["editing project files", "edit project files"],
  delete: ["removing project files", "remove project files"],
  search: ["searching the project", "search the project"],
  execute: ["running a command", "run a command"],
  fetch: ["looking something up", "look something up"],
  think: ["thinking", "think"],
};

const basename = (path: string) => path.split("/").pop() ?? path;

// The button's own label: the selected names, not the model ids, since those
// are the agent's wire values and mean nothing to someone printing a bracket.
function summarize(config: ConfigRow[]): string {
  return config
    .map((row) => row.options.find((o) => o.value === row.value)?.name ?? row.value)
    .join(" · ");
}

// mode 0 is the activity form for cards ("editing lid"); mode 1 the plain verb
// form for permission dialogs ("edit lid").
function describe(title: string, kind: string | undefined, mode: 0 | 1): string {
  const file = title.match(FILE_TITLE);
  if (file) return `${FILE_VERBS[file[1]][mode]} ${file[2]}`;
  const nurb = title.match(NURB_TITLE);
  if (nurb && NURB_VERBS[nurb[1]]) return NURB_VERBS[nurb[1]][mode];
  if (kind && KIND_VERBS[kind]) return KIND_VERBS[kind][mode];
  return title;
}

function Chat({
  path,
  part,
  agent,
  agents,
  resume,
  hidden,
  seed,
  onSeed,
  onSession,
  onFresh,
  onAgent,
  onBusy,
  onSignIn,
}: {
  path: string;
  // The column's identity: this is the part's conversation, whatever the
  // viewer shows by the time a reply lands.
  part: string;
  // Fixed for the life of the conversation: a resumed session keeps the agent
  // that ran it, a fresh one takes the default from the agents pane.
  agent: string;
  // Everything the app can host, for the header's switcher.
  agents: { id: string; label: string }[];
  resume: string | null;
  hidden: boolean;
  // Text waiting for the composer, from a viewer nudge. Prefilled when the column
  // is visible, never sent; onSeed reports it landed so the owner clears it.
  seed?: string | null;
  onSeed?: () => void;
  onSession: (id: string) => void;
  onFresh: () => void;
  // Switching agents cannot move a conversation across two different session
  // stores, so it starts a fresh one on the agent picked.
  onAgent: (id: string) => void;
  onBusy: (busy: boolean) => void;
  onSignIn: (agent: string) => Promise<boolean>;
}) {
  const label = AGENT_LABEL[agent] ?? agent;
  // The sentinel never reaches copy: everywhere the column says its name, the
  // project conversation speaks of the project.
  const isProject = part === PROJECT_CHAT;
  const [items, setItems] = useState<Item[]>([]);
  const [busy, setBusy] = useState(false);
  // A resumed transcript starts loading after the first paint, so treat it as
  // starting immediately rather than briefly exposing a live composer.
  const [starting, setStarting] = useState(Boolean(resume));
  const [authNeeded, setAuthNeeded] = useState(false);
  const [signingIn, setSigningIn] = useState(false);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  // Absolute paths; the Rust side reads them at send time.
  const [attachments, setAttachments] = useState<string[]>([]);
  const [dropping, setDropping] = useState(false);
  // The model and effort this conversation runs on. Empty before the agent has
  // ever reported its lists, which is only ever the first chat on this Mac.
  const [config, setConfig] = useState<ConfigRow[]>([]);
  const [picking, setPicking] = useState(false);
  const [switching, setSwitching] = useState(false);
  const sessionRef = useRef<string | null>(null);
  // A resume id is single-use after the adapter accepts it. Authentication
  // failures retain it; a dead resumed session must not replay it again.
  const resumeRef = useRef<string | null>(resume);
  const restoringRef = useRef(Boolean(resume));
  // Refs, not state: these guard against races within a tick (double-Enter)
  // and after unmount, where state reads are stale or gone.
  const closedRef = useRef(false);
  const sendingRef = useRef(false);
  const nextLocalIdRef = useRef(1);
  // In-flight start, shared across StrictMode's double mount so a resume on
  // mount cannot spawn two adapters.
  const startRef = useRef<Promise<string> | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  // Latest callbacks behind stable refs so ensureSession never goes stale.
  const onSessionRef = useRef(onSession);
  onSessionRef.current = onSession;
  const onBusyRef = useRef(onBusy);
  onBusyRef.current = onBusy;

  useEffect(() => {
    // A removed column cannot leave a stale rail dot behind. Turn transitions
    // report synchronously in send(), before adapter startup can race UI state.
    return () => onBusyRef.current(false);
  }, []);

  useEffect(() => {
    // Kill the adapter when this project's chat column goes away. StrictMode
    // remounts reuse the refs, so closed is reset on mount.
    closedRef.current = false;
    return () => {
      closedRef.current = true;
      const session = sessionRef.current;
      sessionRef.current = null;
      if (session) invoke("close_chat", { sessionId: session }).catch(() => {});
    };
  }, []);

  useEffect(() => {
    const pane = scrollRef.current;
    if (pane) pane.scrollTop = pane.scrollHeight;
  }, [items, permissions, busy]);

  useEffect(() => {
    // Dev-only test hook: the Rust side forwards loopback-socket text here so
    // UI automation can fill the composer without stealing keyboard focus.
    if (!import.meta.env.DEV) return;
    const unlisten = listen<string>("test-type", (event) => {
      if (inputRef.current) inputRef.current.value = event.payload;
    });
    return () => {
      unlisten.then((stop) => stop());
    };
  }, []);

  useEffect(() => {
    // Same hook, submit half: every mounted column hears the event, so only
    // the visible one sends.
    if (!import.meta.env.DEV || hidden) return;
    const unlisten = listen("test-send", () => {
      inputRef.current?.form?.requestSubmit();
    });
    return () => {
      unlisten.then((stop) => stop());
    };
  }, [hidden]);

  useEffect(() => {
    // A seed lands once the column is visible. Below any half-typed draft rather
    // than over it; the user's own words outrank a nudge's.
    if (hidden || !seed) return;
    const box = inputRef.current;
    if (box) {
      // Idempotent: StrictMode double-runs mount effects, and the clearing of
      // the seed above only lands after this commit.
      if (box.value !== seed && !box.value.endsWith(`\n${seed}`)) {
        box.value = box.value.trim() ? `${box.value}\n${seed}` : seed;
      }
      box.focus();
    }
    onSeed?.();
  }, [hidden, seed, onSeed]);

  useEffect(() => {
    // OS file drags arrive as Tauri window events with paths, not HTML5 drops.
    // Every part's chat is mounted at once, so only the visible column listens
    // or one drop would attach to every conversation.
    if (hidden) return;
    const unlisten = getCurrentWebview().onDragDropEvent((event) => {
      if (event.payload.type === "enter") setDropping(true);
      if (event.payload.type === "leave") setDropping(false);
      if (event.payload.type === "drop") {
        setDropping(false);
        const paths = event.payload.paths;
        setAttachments((list) => [...new Set([...list, ...paths])]);
      }
    });
    return () => {
      unlisten.then((stop) => stop());
    };
  }, [hidden]);

  const applyEvent = useCallback((event: ChatEvent) => {
    switch (event.type) {
      case "user_text":
        // Only replayed history carries user chunks; live turns render the
        // composer text directly in send().
        setItems((list) => {
          const last = list[list.length - 1];
          if (last && last.kind === "user") {
            return [...list.slice(0, -1), { ...last, text: last.text + event.text }];
          }
          return [...list, { kind: "user", text: event.text }];
        });
        break;
      case "session_info":
        // Titles have no home since the visible session list went away.
        break;
      case "note":
        setItems((list) => [...list, { kind: "note", text: event.text }]);
        break;
      case "agent_text":
      case "agent_thought": {
        const kind = event.type === "agent_text" ? "agent" : "thought";
        setItems((list) => {
          const last = list[list.length - 1];
          if (last && last.kind === kind) {
            return [...list.slice(0, -1), { ...last, text: last.text + event.text }];
          }
          return [...list, { kind, text: event.text } as Item];
        });
        break;
      }
      case "tool_call":
        setItems((list) => [
          ...list,
          {
            kind: "tool",
            id: event.id,
            title: event.title,
            toolKind: event.kind,
            status: event.status,
            input: event.input,
            output: event.output,
          },
        ]);
        break;
      case "tool_call_update":
        // Absent fields mean unchanged; present ones replace (ACP semantics).
        setItems((list) =>
          list.map((item) =>
            item.kind === "tool" && item.id === event.id
              ? {
                  ...item,
                  title: event.title ?? item.title,
                  status: event.status ?? item.status,
                  input: event.input ?? item.input,
                  output: event.output ?? item.output,
                }
              : item,
          ),
        );
        break;
      case "plan":
        setItems((list) => {
          let index = -1;
          for (let i = list.length - 1; i >= 0; i--) {
            if (list[i].kind === "plan") {
              index = i;
              break;
            }
          }
          if (index >= 0) {
            const next = [...list];
            next[index] = { kind: "plan", entries: event.entries };
            return next;
          }
          return [...list, { kind: "plan", entries: event.entries }];
        });
        break;
      case "permission_request":
        setPermissions((list) => [
          ...list,
          { id: event.id, title: event.title, options: event.options },
        ]);
        break;
      case "permission_resolved":
        setPermissions((list) => list.filter((p) => p.id !== event.id));
        break;
      case "session_error":
        // The dead session is gone from the Rust map too; forgetting it here
        // is what lets the next send start the fresh chat the note promises.
        sessionRef.current = null;
        setItems((list) => [...list, { kind: "note", text: event.message }]);
        break;
    }
  }, []);

  const refreshConfig = useCallback(() => {
    invoke<ConfigRow[]>("chat_config", { agent, sessionId: sessionRef.current })
      .then(setConfig)
      .catch(() => {});
  }, [agent]);

  useEffect(refreshConfig, [refreshConfig]);

  useEffect(() => {
    // The lists arrive from the project's session-list probe, which can land
    // after this column mounted. Without this the first chat opened on a fresh
    // install has no picker until something else remounts it.
    const unlisten = listen("agent-config", () => refreshConfig());
    return () => {
      unlisten.then((stop) => stop());
    };
  }, [refreshConfig]);

  const pick = useCallback(
    async (category: string, value: string) => {
      // Optimistic: the round trip goes through the adapter, and a select that
      // lags behind the click reads as a dropped one.
      setConfig((rows) =>
        rows.map((row) => (row.category === category ? { ...row, value } : row)),
      );
      try {
        setConfig(
          await invoke<ConfigRow[]>("set_chat_config", {
            agent,
            sessionId: sessionRef.current,
            category,
            value,
          }),
        );
      } catch {
        refreshConfig();
      }
    },
    [agent, refreshConfig],
  );

  const ensureSession = useCallback(async () => {
    if (sessionRef.current) return sessionRef.current;
    // One start at a time: StrictMode double-mounts share this promise, so a
    // resume on mount cannot spawn two adapters.
    if (startRef.current) return startRef.current;
    const start = (async () => {
      const requestedResume = resumeRef.current;
      restoringRef.current = Boolean(requestedResume);
      setStarting(true);
      try {
        const onEvent = new Channel<ChatEvent>();
        onEvent.onmessage = applyEvent;
        const session = await invoke<string>("start_chat", {
          path,
          agent,
          onEvent,
          resume: requestedResume,
        });
        if (closedRef.current) {
          // The user switched projects while the adapter was starting; without
          // this, the session outlives its column until app exit.
          invoke("close_chat", { sessionId: session }).catch(() => {});
          throw new Error("chat closed");
        }
        sessionRef.current = session;
        resumeRef.current = null;
        onSessionRef.current(session);
        // The live session is authoritative: it may have clamped a remembered
        // pick the account no longer offers.
        refreshConfig();
        return session;
      } finally {
        startRef.current = null;
        setStarting(false);
      }
    })();
    startRef.current = start;
    return start;
  }, [path, agent, applyEvent, refreshConfig]);

  useEffect(() => {
    // A history session replays its transcript the moment it opens, not on
    // the first send.
    if (!resume) return;
    ensureSession().catch((e) => {
      const message = String(e);
      if (message === "Error: chat closed") return;
      if (message.includes("auth_required")) {
        setAuthNeeded(true);
      } else {
        setItems((list) => [...list, { kind: "note", text: message }]);
      }
    });
    // ensureSession is stable for this mount; resume never changes without a
    // remount (the parent keys this component on it).
  }, [resume, ensureSession]);

  const send = useCallback(
    async (text: string, files: string[]) => {
      sendingRef.current = true;
      const startedAt = Date.now();
      const localId = nextLocalIdRef.current++;
      setItems((list) => [
        ...list,
        {
          kind: "user",
          text,
          files: files.length ? files.map(basename) : undefined,
          localId,
        },
      ]);
      setBusy(true);
      onBusyRef.current(true);
      setAuthNeeded(false);
      let completed = false;
      try {
        const session = await ensureSession();
        await invoke<string>("send_prompt", {
          sessionId: session,
          text,
          part: part ?? null,
          attachments: files,
        });
        completed = true;
      } catch (e) {
        const message = String(e);
        if (message.includes("auth_required")) {
          // Nothing was sent. Restore it ahead of any next draft composed
          // during the turn, and keep both turns' attachments.
          setItems((list) =>
            list.filter((item) => item.kind !== "user" || item.localId !== localId),
          );
          if (inputRef.current) {
            inputRef.current.value = restoreDraftText(text, inputRef.current.value);
          }
          setAttachments((draftFiles) => restoreDraftFiles(files, draftFiles));
          setAuthNeeded(true);
        } else {
          setItems((list) => [...list, { kind: "note", text: message }]);
        }
      } finally {
        sendingRef.current = false;
        setBusy(false);
        onBusyRef.current(false);
        setPermissions([]);
        // Only successful turns long enough to wander away from earn a chime;
        // quick back-and-forth and failures should stay quiet.
        if (shouldPlayCompletionChime(completed, Date.now() - startedAt)) playChime();
      }
    },
    [ensureSession, part],
  );

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const box = inputRef.current;
    const text = box?.value.trim() ?? "";
    // sendingRef, not busy: two Enters in one tick both read the stale state,
    // and a double send would spawn a second adapter. A photo alone is a
    // legitimate message ("model this"), so attachments count as content.
    if (
      (!text && attachments.length === 0) ||
      sendingRef.current ||
      starting ||
      startRef.current
    )
      return;
    if (box) box.value = "";
    setAttachments([]);
    send(text, attachments);
  };

  const attach = async () => {
    const picked = await open({ multiple: true, title: "Attach files" });
    if (!picked) return;
    const paths = Array.isArray(picked) ? picked : [picked];
    setAttachments((list) => [...new Set([...list, ...paths])]);
  };

  const keydown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  };

  const cancel = () => {
    const session = sessionRef.current;
    if (session) invoke("cancel_turn", { sessionId: session }).catch(() => {});
  };

  const signIn = async () => {
    setSigningIn(true);
    try {
      if (!(await onSignIn(agent))) return;
      setAuthNeeded(false);
      setItems((list) => [
        ...list,
        { kind: "note", text: "Signed in. Send your message again." },
      ]);
    } catch (e) {
      setItems((list) => [...list, { kind: "note", text: String(e) }]);
    } finally {
      setSigningIn(false);
    }
  };

  const answerPermission = (permission: Permission, optionId: string) => {
    const session = sessionRef.current;
    if (!session) return;
    setPermissions((list) => list.filter((p) => p.id !== permission.id));
    invoke("respond_permission", {
      sessionId: session,
      requestId: permission.id,
      optionId,
    }).catch(() => {});
  };

  return (
    <section className={hidden ? "chat chat-hidden" : "chat"}>
      <div className="chat-header" data-tauri-drag-region>
        {/* The part name is the only thing here allowed to truncate, so the
            switcher lives beside it rather than inside it. */}
        <span className="chat-header-left">
          <span className="chat-header-label">{isProject ? "project" : part}</span>
          <span aria-hidden="true">·</span>
          {agents.length > 1 ? (
            <span className="chat-switcher">
              <button
                type="button"
                className="chat-switcher-button"
                aria-expanded={switching}
                disabled={busy || starting}
                title={
                  items.length > 0
                    ? "switch agents, which starts a fresh conversation"
                    : "switch agents"
                }
                onClick={() => setSwitching((open) => !open)}
              >
                {label}
                <IconChevronDown />
              </button>
              {switching && (
                <>
                  <div className="chat-switcher-away" onClick={() => setSwitching(false)} />
                  <div className="chat-switcher-menu">
                    {agents.map((option) => (
                      <button
                        key={option.id}
                        type="button"
                        className={
                          option.id === agent ? "chat-switcher-item current" : "chat-switcher-item"
                        }
                        onClick={() => {
                          setSwitching(false);
                          if (option.id !== agent) onAgent(option.id);
                        }}
                      >
                        {option.label}
                      </button>
                    ))}
                    {items.length > 0 && (
                      <p className="chat-switcher-note">
                        Switching starts a fresh conversation. This one is kept.
                      </p>
                    )}
                  </div>
                </>
              )}
            </span>
          ) : (
            <span>{label}</span>
          )}
        </span>
        {items.length > 0 && (
          <button
            className="chat-fresh"
            title="set this conversation aside and start a fresh one"
            disabled={busy || starting}
            onClick={onFresh}
          >
            <IconMessagePlus />
            start fresh
          </button>
        )}
      </div>
      <div className="chat-transcript" ref={scrollRef}>
        {items.length === 0 && !busy && (
          <div className="chat-empty">
            {isProject
              ? `This conversation covers the whole project. Ask ${label} for new parts, or for changes every part should share.`
              : `You're chatting with ${part}. Describe it or ask for changes, and ${label} will model it in the viewer.`}
          </div>
        )}
        {items.map((item, index) => {
          switch (item.kind) {
            case "user":
              return (
                <div key={index} className="chat-user">
                  {item.text}
                  {item.files && (
                    <span className="chat-user-files">
                      {item.files.map((name, i) => (
                        <span key={i} className="chat-user-file">
                          {name}
                        </span>
                      ))}
                    </span>
                  )}
                </div>
              );
            case "agent":
              return (
                <div key={index} className="chat-agent">
                  <Markdown text={item.text} />
                </div>
              );
            case "thought":
              return (
                <details key={index} className="chat-thought">
                  <summary>thinking</summary>
                  <div>{item.text}</div>
                </details>
              );
            case "tool": {
              const shown = describe(item.title, item.toolKind, 0);
              // The collapsed row is plain language; the expansion is the raw
              // material (command, output), untranslated on purpose. The raw
              // title only earns a line when the row paraphrased it away.
              const raw = item.input ?? (shown === item.title ? undefined : item.title);
              if (!raw && !item.output) {
                return (
                  <div key={index} className={`chat-tool ${item.status}`}>
                    <span className="chat-tool-title">{shown}</span>
                    <span className="chat-tool-status">
                      {TOOL_STATUS_LABEL[item.status] ?? item.status}
                    </span>
                  </div>
                );
              }
              return (
                <details key={index} className={`chat-tool expandable ${item.status}`}>
                  <summary>
                    <span className="chat-tool-title">{shown}</span>
                    <span className="chat-tool-status">
                      {TOOL_STATUS_LABEL[item.status] ?? item.status}
                    </span>
                  </summary>
                  <div className="chat-tool-detail">
                    {raw && <pre className="chat-tool-input">{raw}</pre>}
                    {item.output && <pre className="chat-tool-output">{item.output}</pre>}
                  </div>
                </details>
              );
            }
            case "plan":
              return (
                <ul key={index} className="chat-plan">
                  {item.entries.map((entry, i) => (
                    <li key={i} className={entry.status}>
                      {entry.content}
                    </li>
                  ))}
                </ul>
              );
            case "note":
              return (
                <div key={index} className="chat-note">
                  {item.text}
                </div>
              );
          }
        })}
        {starting && (
          <div className="chat-status">
            {restoringRef.current ? "restoring conversation…" : `starting ${label}…`}
          </div>
        )}
        {/* A first build can run ten minutes or more; a silent transcript
            reads as a hang, so the turn keeps a heartbeat on screen. Hidden
            while a dialog is up, since then it is the user's move. */}
        {busy && !starting && permissions.length === 0 && (
          <div className="chat-working">
            <span className="chat-working-dot" aria-hidden="true" />
            {label} is working…
          </div>
        )}
        {authNeeded && (
          <div className="chat-auth">
            {label} isn't signed in on this Mac.{" "}
            <button
              className="chat-auth-button"
              disabled={signingIn}
              onClick={signIn}
            >
              {signingIn ? "signing in…" : "sign in"}
            </button>
          </div>
        )}
        {permissions.map((permission) => (
          <div key={permission.id} className="chat-permission">
            <div className="chat-permission-title">
              {(() => {
                // The permission event carries no tool kind, so only pattern
                // matches translate; anything else reads as "use: <title>".
                // The Rust fallback title is already a full sentence.
                if (permission.title.startsWith(`${label} `)) return permission.title;
                const asked = describe(permission.title, undefined, 1);
                return asked === permission.title
                  ? `${label} wants to use: ${permission.title}`
                  : `${label} wants to ${asked}`;
              })()}
            </div>
            <div className="chat-permission-options">
              {permission.options.map((option) => (
                <button
                  key={option.optionId}
                  className={`chat-permission-button ${option.kind}`}
                  onClick={() => answerPermission(permission, option.optionId)}
                >
                  {option.name}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      <form
        className={dropping ? "chat-composer dropping" : "chat-composer"}
        onSubmit={submit}
      >
        {attachments.length > 0 && (
          <div className="chat-attachments">
            {attachments.map((path) => (
              <span key={path} className="chat-attachment">
                <span className="chat-attachment-name">{basename(path)}</span>
                <button
                  type="button"
                  className="chat-attachment-remove"
                  aria-label={`remove ${basename(path)}`}
                  onClick={() =>
                    setAttachments((list) => list.filter((p) => p !== path))
                  }
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
        <textarea
          ref={inputRef}
          className="chat-input"
          placeholder={
            busy
              ? `${label} is working…`
              : starting
                ? restoringRef.current
                  ? "Restoring conversation…"
                  : `Starting ${label}…`
                : `Describe or change ${isProject ? "the project" : part}…`
          }
          rows={2}
          disabled={starting}
          onKeyDown={keydown}
        />
        <div className="chat-composer-controls">
          <button
            type="button"
            className="chat-attach"
            title="attach photos or files"
            aria-label="attach photos or files"
            disabled={starting}
            onClick={attach}
          >
            <IconPaperclip />
          </button>
          {config.length > 0 && (
            <div className="chat-config">
              <button
                type="button"
                className="chat-config-button"
                aria-expanded={picking}
                title={`${label} is set to ${summarize(config)}`}
                onClick={() => setPicking((open) => !open)}
              >
                {summarize(config)}
              </button>
              {picking && (
                <>
                  {/* Click-away, rather than a document listener that has to be
                      taught which clicks are its own. */}
                  <div className="chat-config-away" onClick={() => setPicking(false)} />
                  <div className="chat-config-menu">
                    {config.map((row) => (
                      <label key={row.category} className="chat-config-row">
                        <span>{row.name}</span>
                        <select
                          value={row.value}
                          disabled={busy || starting}
                          onChange={(event) => pick(row.category, event.target.value)}
                        >
                          {row.options.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.name}
                            </option>
                          ))}
                        </select>
                      </label>
                    ))}
                    <p className="chat-config-note">
                      {busy
                        ? `Wait for ${label} to finish to change these.`
                        : "Bigger models and higher effort use up your plan faster."}
                    </p>
                  </div>
                </>
              )}
            </div>
          )}
          {busy ? (
            <button type="button" className="chat-send chat-stop" onClick={cancel}>
              stop
            </button>
          ) : (
            <button type="submit" className="chat-send" disabled={starting}>
              send
            </button>
          )}
        </div>
      </form>
    </section>
  );
}

export default Chat;
