export function restoreDraftText(failed: string, draft: string): string {
  if (!failed) return draft;
  if (!draft) return failed;
  return `${failed}\n\n${draft}`;
}

export function restoreDraftFiles(failed: string[], draft: string[]): string[] {
  return [...new Set([...failed, ...draft])];
}
