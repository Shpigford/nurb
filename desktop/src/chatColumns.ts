export type ChatColumn = {
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
