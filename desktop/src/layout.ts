export const VIEWER_MIN = 240;

export const COLUMNS = {
  rail: { min: 160, max: 400, fallback: 220, key: "nurb-rail-width" },
  chat: { min: 240, max: 720, fallback: 300, key: "nurb-chat-width" },
} as const;

export type Column = keyof typeof COLUMNS;
export type ColumnWidths = Record<Column, number>;

function clampColumn(which: Column, width: number) {
  const { min, max } = COLUMNS[which];
  return Math.min(max, Math.max(min, width));
}

function savedColumn(which: Column, width: number) {
  return Number.isFinite(width) && width > 0
    ? clampColumn(which, width)
    : COLUMNS[which].fallback;
}

export function resizedColumn(
  which: Column,
  width: number,
  current: ColumnWidths,
  viewport: number,
) {
  const other = which === "rail" ? current.chat : current.rail;
  const available = viewport - VIEWER_MIN - other;
  const max = Math.max(COLUMNS[which].min, Math.min(COLUMNS[which].max, available));
  return Math.min(max, Math.max(COLUMNS[which].min, width));
}

export function fitColumns(widths: ColumnWidths, viewport: number): ColumnWidths {
  let rail = clampColumn("rail", widths.rail);
  let chat = clampColumn("chat", widths.chat);

  // Keep the seam nearest the viewer on-screen, then reduce the rail only when both
  // sidebars at their preferred widths still leave too little canvas.
  chat = resizedColumn("chat", chat, { rail, chat }, viewport);
  rail = resizedColumn("rail", rail, { rail, chat }, viewport);
  return { rail, chat };
}

export function initialColumns(saved: ColumnWidths, viewport: number): ColumnWidths {
  return fitColumns(
    {
      rail: savedColumn("rail", saved.rail),
      chat: savedColumn("chat", saved.chat),
    },
    viewport,
  );
}
