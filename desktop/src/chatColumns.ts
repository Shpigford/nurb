export type ChatColumn = {
  // What the mounted Chat is keyed by. A part's name can change under a running
  // turn, and remounting the column would end that turn.
  id: number;
  path: string;
  part: string;
  agent: string | null;
  resume: string | null;
  gen: number;
  // A hidden turn finished with state that has not been shown yet. Keep the
  // mounted column until it is visible so drafts, errors, and replies survive.
  unseen: boolean;
};

// Paths can contain ":" or spaces, so map keys join on a NUL, which no
// filesystem path can carry.
export const chatKey = (path: string, part: string) => `${path}\u0000${part}`;

/** The conversation follows its part to a new name. A column left under that name goes. */
export function renameChatColumn(columns: ChatColumn[], path: string, was: string, name: string) {
  return columns
    .filter((column) => !(column.path === path && column.part === name))
    .map((column) => (column.path === path && column.part === was ? { ...column, part: name } : column));
}

export function renameChatKey(chats: Record<string, boolean>, was: string, name: string) {
  if (!(was in chats)) return chats;
  const { [was]: flag, ...rest } = chats;
  return { ...rest, [name]: flag };
}

export function retainChatColumns(
  columns: ChatColumn[],
  active: string | null,
  busyChats: Record<string, boolean>,
) {
  const kept = columns.filter(
    (column) =>
      column.path === active ||
      column.unseen ||
      busyChats[chatKey(column.path, column.part)],
  );
  return kept.length === columns.length ? columns : kept;
}

export function updateChatActivity(
  columns: ChatColumn[],
  path: string,
  part: string,
  agent: string,
  busy: boolean,
  visible: boolean,
  wasBusy: boolean,
) {
  let changed = false;
  const next = columns.map((column) => {
    if (column.path !== path || column.part !== part) return column;
    if (busy && (column.agent === null || column.unseen)) {
      changed = true;
      return { ...column, agent: column.agent ?? agent, unseen: false };
    }
    if (!busy && wasBusy && !visible && !column.unseen) {
      changed = true;
      return { ...column, unseen: true };
    }
    return column;
  });
  return changed ? next : columns;
}

export function markChatSeen(columns: ChatColumn[], path: string, part: string) {
  let changed = false;
  const next = columns.map((column) => {
    if (column.path !== path || column.part !== part || !column.unseen) return column;
    changed = true;
    return { ...column, unseen: false };
  });
  return changed ? next : columns;
}
