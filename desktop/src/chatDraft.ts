export function restoreDraftText(failed: string, draft: string): string {
  if (!failed) return draft;
  if (!draft) return failed;
  return `${failed}\n\n${draft}`;
}

export function restoreDraftFiles(failed: string[], draft: string[]): string[] {
  return [...new Set([...failed, ...draft])];
}

export class AttachmentDraft {
  private files: string[] = [];
  private pending: Promise<string[]>[] = [];
  private readonly onChange: (files: string[]) => void;

  constructor(onChange: (files: string[]) => void) {
    this.onChange = onChange;
  }

  get hasContent(): boolean {
    return this.files.length > 0 || this.pending.length > 0;
  }

  add(paths: string[]): void {
    this.replace(restoreDraftFiles(this.files, paths));
  }

  restore(paths: string[]): void {
    this.replace(restoreDraftFiles(paths, this.files));
  }

  remove(path: string): void {
    this.replace(this.files.filter((file) => file !== path));
  }

  track(task: Promise<string[]>): Promise<void> {
    const pending = task.then((paths) => {
      this.add(paths);
      return paths;
    });
    this.pending.push(pending);
    // The caller reports failures; this branch only keeps settled work out of
    // the next submit boundary without creating an unhandled rejection.
    void pending
      .finally(() => {
        this.pending = this.pending.filter((item) => item !== pending);
      })
      .catch(() => {});
    return pending.then(() => undefined);
  }

  async take(): Promise<string[]> {
    // Snapshot the boundary: pastes begun before submit belong to this turn;
    // anything pasted afterward stays in the next draft.
    const files = [...this.files];
    const pending = [...this.pending];
    const settled = await Promise.allSettled(pending);
    for (const result of settled) {
      if (result.status === "fulfilled") files.push(...result.value);
    }
    const taken = [...new Set(files)];
    this.replace(this.files.filter((path) => !taken.includes(path)));
    return taken;
  }

  private replace(files: string[]): void {
    this.files = files;
    this.onChange(files);
  }
}
