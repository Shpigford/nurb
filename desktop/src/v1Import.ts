/** Import each folder nurb 0.x listed. One folder that refuses does not stop the rest. */
export async function importV1Folders(
  folders: string[],
  importOne: (path: string) => Promise<unknown>,
  report: (text: string) => void,
): Promise<number> {
  let imported = 0;
  for (const path of folders) {
    try {
      await importOne(path);
      imported += 1;
    } catch (e) {
      report(`${path.split("/").filter(Boolean).pop() ?? path} (${e instanceof Error ? e.message : String(e)})`);
    }
  }
  return imported;
}

export function broughtOver(count: number): string {
  return `Brought over ${count} ${count === 1 ? "project" : "projects"} from nurb 0.x`;
}

export function notBroughtOver(refused: string[]): string {
  const count = refused.length;
  return `${count} ${count === 1 ? "project" : "projects"} from nurb 0.x didn't come over: ${refused.join("; ")}. Use Import folder to try again.`;
}
