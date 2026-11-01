import { downloadDir, join } from "@tauri-apps/api/path";
import { exists, writeFile } from "@tauri-apps/plugin-fs";
import { openPath, revealItemInDir } from "@tauri-apps/plugin-opener";

/** The name Finder gives the nth copy: `bracket 2.3mf`. */
export function numbered(name: string, n: number): string {
  const dot = name.lastIndexOf(".");
  return dot > 0 ? `${name.slice(0, dot)} ${n}${name.slice(dot)}` : `${name} ${n}`;
}

// A download lands where every other Mac download does, never over an earlier one.
async function writeDownload(name: string, blob: Blob): Promise<string> {
  const dir = await downloadDir();
  let path = await join(dir, name);
  for (let n = 2; await exists(path); n++) path = await join(dir, numbered(name, n));
  await writeFile(path, new Uint8Array(await blob.arrayBuffer()));
  return path;
}

// Finder shows the download, so the next step (into the slicer) starts from the file itself.
export async function saveToDownloads(name: string, blob: Blob): Promise<string> {
  const path = await writeDownload(name, blob);
  await revealItemInDir(path).catch(() => {});
  return "Downloads";
}

// Or the slicer takes it straight from Downloads. The capability names each slicer
// the engine can drive, so `app` can only be one of those.
export async function openInSlicer(name: string, blob: Blob, app: string): Promise<void> {
  await openPath(await writeDownload(name, blob), app);
}
