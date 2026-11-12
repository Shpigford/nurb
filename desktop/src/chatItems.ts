// The live half of a chat column: what the agent is doing right now, before the
// project's own transcript has it. Pure functions so the mapping is testable
// without a renderer.

import type { StepStatus, ToolStep } from "@nurb/ui";

export type PlanEntry = { content: string; status: string };
export type PermissionOption = { optionId: string; name: string; kind: string };

// Mirrors ChatEvent in src-tauri/src/acp.rs.
export type ChatEvent =
  | { type: "user_text"; text: string }
  | { type: "agent_text"; text: string }
  | { type: "agent_thought"; text: string }
  // A finished block of assistant prose, which the driver sends once the
  // streamed deltas are complete.
  | { type: "prose"; text: string }
  | { type: "session_info"; title: string | null }
  | { type: "note"; text: string }
  | { type: "tool_call"; id: string; title: string; kind?: string; status: string; input?: string; output?: string; locations?: string[] }
  | { type: "tool_call_update"; id: string; title?: string; status?: string; input?: string; output?: string; locations?: string[] }
  | { type: "plan"; entries: PlanEntry[] }
  | { type: "permission_request"; id: number; title: string; options: PermissionOption[] }
  | { type: "permission_resolved"; id: number }
  | { type: "session_error"; message: string };

export type Item =
  | { kind: "user"; text: string; files?: string[]; localId?: number }
  | { kind: "agent"; text: string }
  | { kind: "thought"; text: string }
  // `tool` and `seq` let a nurb step find its own transcript row: the row the
  // dispatcher writes for it arrives with a sequence number above `seq`.
  | { kind: "step"; toolKind?: string; tool?: string; seq?: number; step: ToolStep }
  | { kind: "plan"; entries: PlanEntry[] }
  | { kind: "note"; text: string };

// Tool titles arrive as developer-speak ("Edit parts/lid.py", "nurb check").
// The app's audience is hobbyists, so rows and permission dialogs translate what
// they can into plain activity language and fall back to the raw title.
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

/**
 * mode 0 is the activity form ("editing lid"); mode 1 the plain verb form for
 * permission dialogs ("edit lid").
 */
export function describe(title: string, kind: string | undefined, mode: 0 | 1): string {
  const file = title.match(FILE_TITLE);
  if (file) return `${FILE_VERBS[file[1]][mode]} ${file[2]}`;
  const nurb = title.match(NURB_TITLE);
  if (nurb && NURB_VERBS[nurb[1]]) return NURB_VERBS[nurb[1]][mode];
  if (kind && KIND_VERBS[kind]) return KIND_VERBS[kind][mode];
  return title;
}

// What the working line says while a tool runs, in the person's words. The chat no
// longer lists the calls, so this is the one place the work shows.
const ACTIVITY: [RegExp, string][] = [
  [/^(pin|amend)_spec$/, "planning the part"],
  [/^record_measurement$/, "noting the sizes"],
  [/^find_photos$/, "looking at the photos"],
  [/^(set|delete)_label$/, "labelling the part"],
  [/^(write|edit)_(part|shared)_source$|^run_build$/, "building the part"],
  [/^(render|inspect|check|verify|compare)/, "checking the part"],
  [/^(export|slice)/, "preparing the print"],
];

// How long a silence lasts before the line says how long. A model can think for
// twenty minutes with nothing to show, and a line that never changes reads as a hang.
export const QUIET_MS = 30_000;

/**
 * "building the part" while that is the newest running call. With no call running
 * the agent is thinking, and once it has been quiet a while the line says for how
 * long: "thinking (4 min)".
 */
export function activity(items: Item[], quietMs = 0): string {
  for (let i = items.length - 1; i >= 0; i--) {
    const item = items[i];
    if (item.kind !== "step" || item.step.status !== "running") continue;
    const tool = (item.tool ?? "").replace(/^mcp__nurb__/, "");
    return ACTIVITY.find(([pattern]) => pattern.test(tool))?.[1] ?? "working";
  }
  if (quietMs < QUIET_MS) return "thinking";
  const seconds = Math.floor(quietMs / 1000);
  return `thinking (${seconds < 60 ? `${seconds} s` : `${Math.floor(seconds / 60)} min`})`;
}

const STEP_STATUS: Record<string, StepStatus> = {
  pending: "running",
  in_progress: "running",
  completed: "done",
  failed: "failed",
};

/** The tool input as the card wants it: an object when it parses, the raw text otherwise. */
function payload(input: string | undefined): unknown {
  if (!input) return undefined;
  try {
    return JSON.parse(input);
  } catch {
    return input;
  }
}

function subject(input: string | undefined): string | null {
  const parsed = payload(input);
  if (!parsed || typeof parsed !== "object") return null;
  const named = parsed as Record<string, unknown>;
  const name = named.part_name ?? named.name;
  return typeof name === "string" ? name : null;
}

/** Verb and object for one tool call, in the words the card prints. */
export function toolWords(
  title: string,
  kind: string | undefined,
  input: string | undefined,
): [string, string] {
  if (kind === "nurb") {
    const [verb, ...rest] = title.split("_");
    return [verb, subject(input) ?? rest.join(" ")];
  }
  const [verb, ...rest] = describe(title, kind, 1).split(" ");
  return [verb, rest.join(" ")];
}

export function stepFrom(
  event: Extract<ChatEvent, { type: "tool_call" }>,
  at: number,
): ToolStep {
  const [verb, object] = toolWords(event.title, event.kind, event.input);
  return {
    id: event.id,
    verb,
    object,
    status: STEP_STATUS[event.status] ?? "running",
    started_at: new Date(at).toISOString(),
    input: payload(event.input),
    output: event.output,
  };
}

export function advanceStep(
  step: ToolStep,
  event: Extract<ChatEvent, { type: "tool_call_update" }>,
  at: number,
  kind: string | undefined,
): ToolStep {
  const status = event.status ? STEP_STATUS[event.status] ?? step.status : step.status;
  const input = event.input ?? undefined;
  const [verb, object] = event.title
    ? toolWords(event.title, kind, input)
    : [step.verb, step.object];
  return {
    ...step,
    verb,
    object,
    status,
    input: input === undefined ? step.input : payload(input),
    output: event.output ?? step.output,
    elapsed_s:
      status === "running"
        ? step.elapsed_s
        : Math.max(0, (at - Date.parse(step.started_at)) / 1000),
  };
}

function settled(status: StepStatus): boolean {
  return status !== "running";
}

/**
 * Fold one event into the overlay. Permission events and titles are the caller's.
 * `seq` is the project's newest transcript sequence number, remembered on a step
 * so pruneLanded can tell its own row from an older call of the same tool.
 */
export function applyChatEvent(items: Item[], event: ChatEvent, at: number, seq = 0): Item[] {
  const last = items[items.length - 1];
  switch (event.type) {
    case "user_text":
      if (last && last.kind === "user") {
        return [...items.slice(0, -1), { ...last, text: last.text + event.text }];
      }
      return [...items, { kind: "user", text: event.text }];
    case "note":
    case "session_error":
      return [...items, { kind: "note", text: event.type === "note" ? event.text : event.message }];
    case "agent_text":
    case "agent_thought": {
      const kind = event.type === "agent_text" ? "agent" : "thought";
      if (last && last.kind === kind) {
        return [...items.slice(0, -1), { ...last, text: last.text + event.text }];
      }
      return [...items, { kind, text: event.text } as Item];
    }
    case "prose":
      // The block is on its way to the project's transcript, so the streaming
      // copy has done its job. So have the finished steps before it: the
      // transcript keeps the ones that matter, in order, and left here they
      // would pile up after the words they came before. A failure stays.
      if (!last || last.kind !== "agent") return items;
      return items.slice(0, -1).filter((item) => item.kind !== "step" || item.step.status !== "done");
    case "tool_call":
      return [
        ...items,
        { kind: "step", toolKind: event.kind, tool: event.title, seq, step: stepFrom(event, at) },
      ];
    case "tool_call_update": {
      const next: Item[] = [];
      for (const item of items) {
        if (item.kind !== "step" || item.step.id !== event.id) {
          next.push(item);
          continue;
        }
        next.push({ ...item, step: advanceStep(item.step, event, at, item.toolKind) });
      }
      return next;
    }
    case "plan": {
      let index = -1;
      for (let i = items.length - 1; i >= 0; i--) {
        if (items[i].kind === "plan") {
          index = i;
          break;
        }
      }
      if (index < 0) return [...items, { kind: "plan", entries: event.entries }];
      const next = [...items];
      next[index] = { kind: "plan", entries: event.entries };
      return next;
    }
    default:
      return items;
  }
}

const CLAUDE_OUTDATED = /claude_outdated:\s*([^\s"']+)/;

/**
 * What to say when Claude Code itself is the problem. Each one is something the
 * person fixes in a terminal, so none of them offers a button.
 */
export function claudeNote(message: string): string | null {
  if (message.includes("claude_missing")) {
    return "Install Claude Code first, then come back. It is free to install; a Claude subscription signs it in.";
  }
  const outdated = message.match(CLAUDE_OUTDATED);
  if (outdated) {
    return `Update Claude Code: in a terminal run claude update (you have ${outdated[1]}, 2.1.221 or newer is needed).`;
  }
  if (message.includes("auth_required")) {
    return "Sign in to Claude Code first: open a terminal, run claude, and follow the prompts. Then come back here.";
  }
  return null;
}

/**
 * Drop the nurb steps whose transcript row has arrived, so a call shows once.
 * A call that never reached the serve (the tools dropped, a transport error)
 * has no row and stays on screen with its failure.
 */
export function pruneLanded(
  items: Item[],
  messages: { sequence_number?: number; payload?: { tool?: string } | null }[],
): Item[] {
  return items.filter((item) => {
    if (item.kind !== "step" || item.toolKind !== "nurb" || !settled(item.step.status)) return true;
    return !messages.some(
      (m) => m.payload?.tool === item.tool && (m.sequence_number ?? 0) > (item.seq ?? 0),
    );
  });
}

/** A note once, however many paths report the same trouble in one turn. */
export function withNote(items: Item[], text: string): Item[] {
  const last = items[items.length - 1];
  if (last && last.kind === "note" && last.text === text) return items;
  return [...items, { kind: "note", text }];
}
