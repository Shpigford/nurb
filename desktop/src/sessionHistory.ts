// One past conversation, as the agent's own session store reports it plus what
// the app recorded against it.
export type SessionInfo = {
  id: string;
  title: string | null;
  updatedAt: string | null;
  part: string | null;
  // The one session its part reopens on its own. The rest are history: still
  // listed under the part, entered only by choice.
  attached: boolean;
  agent: string;
};

// What a part reopens: the session's id and the agent that owns it.
export type PartChat = { id: string | null; agent: string | null };

export type GroupedSessions = {
  resume: Record<string, PartChat>;
  history: Record<string, SessionInfo[]>;
};

// The listing is newest first, so both halves keep that order: the first
// attached session per part is the one to reopen, and the history menu reads
// top-down from the most recent.
export function groupSessions(list: SessionInfo[]): GroupedSessions {
  const resume: Record<string, PartChat> = {};
  const history: Record<string, SessionInfo[]> = {};
  for (const entry of list) {
    if (!entry.part) continue;
    const seen = history[entry.part];
    if (seen) seen.push(entry);
    else history[entry.part] = [entry];
    if (entry.attached && !resume[entry.part]) {
      resume[entry.part] = { id: entry.id, agent: entry.agent };
    }
  }
  return { resume, history };
}

// Agents title a session from its first prompt, but a conversation abandoned
// before that has none. The timestamp beside it is what tells those apart.
export function sessionTitle(entry: SessionInfo): string {
  const title = entry.title?.trim();
  return title ? title : "untitled chat";
}

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

// When the conversation last moved, in the shortest form that still says it.
// Empty when the agent reported no timestamp, which is a row with a title and
// nothing else to add.
export function sessionWhen(updatedAt: string | null, now: number): string {
  if (!updatedAt) return "";
  const at = Date.parse(updatedAt);
  if (Number.isNaN(at)) return "";
  const ago = now - at;
  if (ago < MINUTE) return "just now";
  if (ago < HOUR) return `${Math.floor(ago / MINUTE)}m ago`;
  if (ago < DAY) return `${Math.floor(ago / HOUR)}h ago`;
  if (ago < 7 * DAY) return `${Math.floor(ago / DAY)}d ago`;
  return new Date(at).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
