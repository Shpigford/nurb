import {
  ClipboardEvent,
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
import { AttachmentDraft, restoreDraftText } from "./chatDraft";
import {
  describe,
  orderOptions,
  permissionPrompt,
  type PermissionOption,
} from "./toolLanguage";

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
  | {
      type: "permission_request";
      id: number;
      title: string;
      kind?: string;
      detail?: string;
      options: PermissionOption[];
    }
  | { type: "permission_resolved"; id: number }
  | { type: "session_error"; message: string };

type PlanEntry = { content: string; status: string };

type Item =
  | { kind: "user"; text: string; files?: string[]; localId?: number }
  | { kind: "agent"; text: string }
  | { kind: "thought"; text: string }
  | { kind: "tool"; id: string; title: string; toolKind?: string; status: string; input?: string; output?: string }
  | { kind: "plan"; entries: PlanEntry[] }
  | { kind: "note"; text: string };

type Permission = {
  id: number;
  title: string;
  kind?: string;
  detail?: string;
  options: PermissionOption[];
};

// Mirrors ApprovalState in src-tauri/src/acp.rs. `confined` is the kernel's
// answer, not a user-agent sniff, so the copy cannot contradict what is
// actually protecting the user.
type ApprovalState = { confined: boolean; auto: boolean };

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

const basename = (path: string) => path.split("/").pop() ?? path;

// The button's own label: the selected names, not the model ids, since those
// are the agent's wire values and mean nothing to someone printing a bracket.
function summarize(config: ConfigRow[]): string {
  return config
    .map((row) => row.options.find((o) => o.value === row.value)?.name ?? row.value)
    .join(" · ");
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
  agents: { id: string; label: string; loggedIn: boolean | null }[];
  resume: string | null;
  hidden: boolean;
  // Text waiting for the composer, from a viewer nudge. Prefilled when the column
  // is visible, never sent; onSeed reports it landed so the owner clears it.
  seed?: string | null;
  onSeed?: () => void;
  onSession: (id: string) => void;
  onFresh: () => void;
  // Switching agents cannot move a conversation across two different session
  // stores, so it starts a fresh one on the agent picked. `unstarted` is true
  // when nothing has been said yet, which makes the pick the new default.
  onAgent: (id: string, unstarted: boolean) => void;
  onBusy: (busy: boolean) => void;
  onSignIn: (agent: string) => Promise<boolean>;
}) {
  const label = AGENT_LABEL[agent] ?? agent;
  // Known signed out, not merely unknown: an unknown status stays quiet.
  const signedOut = agents.find((option) => option.id === agent)?.loggedIn === false;
  // The sentinel never reaches copy: everywhere the column says its name, the
  // project conversation speaks of the project.
  const isProject = part === PROJECT_CHAT;
  const [items, setItems] = useState<Item[]>([]);
  const [busy, setBusy] = useState(false);
  // A resumed transcript starts loading after the first paint, so treat it as
  // starting immediately rather than briefly exposing a live composer.
  const [starting, setStarting] = useState(Boolean(resume));
  // A refused prompt needs explicit resend guidance; a proactive or resume sign-in does not.
  const [authNeeded, setAuthNeeded] = useState<"none" | "sign-in" | "resume" | "resend">("none");
  const [signingIn, setSigningIn] = useState(false);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [approval, setApproval] = useState<ApprovalState | null>(null);
  // Absolute paths; the Rust side reads them at send time.
  const [attachments, setAttachments] = useState<string[]>([]);
  const attachmentDraftRef = useRef<AttachmentDraft | null>(null);
  if (!attachmentDraftRef.current) {
    attachmentDraftRef.current = new AttachmentDraft(setAttachments);
  }
  const attachmentDraft = attachmentDraftRef.current;
  const [dropping, setDropping] = useState(false);
  // The model and effort this conversation runs on. Empty before the agent has
  // ever reported its lists, which is only ever the first chat on this machine.
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
        attachmentDraft.add(paths);
      }
    });
    return () => {
      unlisten.then((stop) => stop());
    };
  }, [hidden, attachmentDraft]);

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
          {
            id: event.id,
            title: event.title,
            kind: event.kind,
            detail: event.detail,
            options: event.options,
          },
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

  const refreshApproval = useCallback(() => {
    invoke<ApprovalState>("approval_state", { path })
      .then(setApproval)
      .catch(() => {});
  }, [path]);

  useEffect(refreshApproval, [refreshApproval]);

  useEffect(() => {
    // Sibling columns on the same project mirror this flag, so a grant made
    // in one has to land in all of them.
    const unlisten = listen("project-approvals", () => refreshApproval());
    return () => {
      unlisten.then((stop) => stop());
    };
  }, [refreshApproval]);

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

  const restoreSession = useCallback(async () => {
    try {
      await ensureSession();
    } catch (e) {
      const message = String(e);
      if (message === "Error: chat closed") return;
      if (message.includes("auth_required")) {
        setAuthNeeded("resume");
      } else {
        setItems((list) => [...list, { kind: "note", text: message }]);
      }
    }
  }, [ensureSession]);

  useEffect(() => {
    // A history session replays its transcript when it opens, not on the first send; reuse this path after sign-in.
    if (resume) restoreSession();
  }, [resume, restoreSession]);

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
      setAuthNeeded("none");
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
          attachmentDraft.restore(files);
          setAuthNeeded("resend");
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
    [ensureSession, part, attachmentDraft],
  );

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const box = inputRef.current;
    const text = box?.value.trim() ?? "";
    // sendingRef, not busy: two Enters in one tick both read the stale state,
    // and a double send would spawn a second adapter. A photo alone is a
    // legitimate message ("model this"), so attachments count as content.
    if (
      (!text && !attachmentDraft.hasContent) ||
      sendingRef.current ||
      starting ||
      startRef.current
    )
      return;
    // Reserve the turn before waiting: a second Enter must not queue another
    // send while a pasted image is still crossing the IPC boundary.
    sendingRef.current = true;
    if (box) box.value = "";
    const files = await attachmentDraft.take();
    if (!text && files.length === 0) {
      sendingRef.current = false;
      return;
    }
    send(text, files);
  };

  const attach = async () => {
    const picked = await open({ multiple: true, title: "Attach files" });
    if (!picked) return;
    const paths = Array.isArray(picked) ? picked : [picked];
    attachmentDraft.add(paths);
  };

  // A pasted image (a screenshot, or an image copied from another app) has no
  // path, so the backend writes it to a temporary file that attaches like a
  // dropped one. Consuming the paste keeps a copied file's name out of the text.
  const paste = (event: ClipboardEvent<HTMLTextAreaElement>) => {
    const images = Array.from(event.clipboardData.items)
      .filter((item) => item.type.startsWith("image/"))
      .map((item) => item.getAsFile())
      .filter((blob): blob is File => blob !== null);
    if (images.length === 0) return;
    event.preventDefault();
    const saved = Promise.all(
      images.map((blob) =>
        blob.arrayBuffer().then((bytes) =>
          invoke<string>("save_pasted_image", new Uint8Array(bytes), {
            headers: { mime: blob.type },
          }),
        ),
      ),
    );
    attachmentDraft.track(saved).catch((e) =>
      setItems((list) => [...list, { kind: "note", text: String(e) }]),
    );
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
    const needsResend = authNeeded === "resend";
    const needsRestore = authNeeded === "resume";
    setSigningIn(true);
    try {
      if (!(await onSignIn(agent))) return;
      setAuthNeeded("none");
      if (needsRestore) await restoreSession();
      // Only a refused message needs sending again; a proactive sign-in has nothing to repeat.
      if (needsResend) {
        setItems((list) => [
          ...list,
          { kind: "note", text: "Signed in. Send your message again." },
        ]);
      }
    } catch (e) {
      setItems((list) => [...list, { kind: "note", text: String(e) }]);
      // Keep retry visible even though the failure adds an item to the transcript.
      setAuthNeeded((state) => state === "none" ? "sign-in" : state);
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

  // Standing yes for this project, then answer the request in front of us with
  // the adapter's own allow-once option. The app's choice stays the app's: no
  // invented option id crosses back over ACP.
  const trustProject = (permission: Permission) => {
    const allowOnce = permission.options.find((o) => o.kind === "allow_once");
    if (!allowOnce) return;
    setApproval((state) => (state ? { ...state, auto: true } : state));
    invoke("set_project_auto", { path, auto: true }).catch(() => {});
    setItems((list) => [
      ...list,
      {
        kind: "note",
        text: `${label} will now work in this project without asking. The button by the message box turns that back off.`,
      },
    ]);
    answerPermission(permission, allowOnce.optionId);
  };

  const toggleAuto = () => {
    if (!approval) return;
    const auto = !approval.auto;
    setApproval({ ...approval, auto });
    invoke("set_project_auto", { path, auto }).catch(() => {});
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
                          if (option.id !== agent) onAgent(option.id, items.length === 0);
                        }}
                      >
                        {option.label}
                        {option.loggedIn === false && (
                          <span className="chat-switcher-hint">sign in</span>
                        )}
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
        {/* Nothing said yet and the agent is known to be signed out: ask before the first message bounces. */}
        {items.length === 0 && !starting && authNeeded === "none" && signedOut && (
          <div className="chat-auth">
            Sign in to {label} to start.{" "}
            <button className="chat-auth-button" disabled={signingIn} onClick={signIn}>
              {signingIn ? "signing in…" : "sign in"}
            </button>
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
        {authNeeded !== "none" && (
          <div className="chat-auth">
            {label} isn't signed in on this computer.{" "}
            <button
              className="chat-auth-button"
              disabled={signingIn}
              onClick={signIn}
            >
              {signingIn ? "signing in…" : "sign in"}
            </button>
          </div>
        )}
        {permissions.map((permission) => {
          const prompt = permissionPrompt(permission, label);
          // Offer the standing yes only where it is the user's to give: an
          // unconfined machine, a project not already granted, and a request
          // the adapter is willing to have allowed.
          const offerTrust =
            prompt.verbatim &&
            approval !== null &&
            !approval.confined &&
            !approval.auto &&
            permission.options.some((o) => o.kind === "allow_once");
          return (
            <div key={permission.id} className="chat-permission">
              <div className="chat-permission-title">{prompt.headline}</div>
              {prompt.detail && (
                <pre className="chat-permission-detail">{prompt.detail}</pre>
              )}
              <div className="chat-permission-options">
                {orderOptions(permission.options).map((option) => (
                  <button
                    key={option.optionId}
                    className={`chat-permission-button ${option.kind}`}
                    onClick={() => answerPermission(permission, option.optionId)}
                  >
                    {option.name}
                  </button>
                ))}
                {offerTrust && (
                  <button
                    className="chat-permission-button allow_always"
                    onClick={() => trustProject(permission)}
                  >
                    Always allow in this project
                  </button>
                )}
              </div>
              {/* Shown at the moment it changes what the user decides, and
                  only where nothing is limiting the command. */}
              {prompt.verbatim && approval !== null && !approval.confined && (
                <div className="chat-permission-note">
                  nurb cannot limit what this does on your system, so it runs
                  with your account's access.
                </div>
              )}
            </div>
          );
        })}
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
                  onClick={() => attachmentDraft.remove(path)}
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
          onPaste={paste}
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
          {approval && (
            <button
              type="button"
              className="chat-approval"
              title={
                approval.confined
                  ? approval.auto
                    ? `${label} works without asking. Files outside this project are protected by macOS either way.`
                    : `${label} asks before running commands or changing files.`
                  : approval.auto
                    ? `${label} runs commands in this project without asking, and nurb cannot limit what they do. Click to make it ask first.`
                    : `${label} asks before running commands or changing files outside this project. Click to stop asking.`
              }
              onClick={toggleAuto}
            >
              {approval.auto ? "runs on its own" : "asks before running"}
            </button>
          )}
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
