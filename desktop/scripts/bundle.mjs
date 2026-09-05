// `tauri build`, except that it survives not having the updater signing key.
// The config asks for updater artifacts unconditionally, and Tauri refuses to
// build one it cannot sign, so a local or fork build fails before it starts.
// Without TAURI_SIGNING_PRIVATE_KEY this drops the updater artifact for that
// one invocation, never touching the config files: the installer is the same
// installer, minus the ability to update itself. With the key set (upstream
// CI, release.sh) nothing is overridden and the output is unchanged.
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const desktop = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const cli = path.join(desktop, "node_modules", "@tauri-apps", "cli", "tauri.js");

const args = ["build", ...process.argv.slice(2)];
if (!process.env.TAURI_SIGNING_PRIVATE_KEY) {
  console.log("bundle: no TAURI_SIGNING_PRIVATE_KEY, building an installer that cannot self-update");
  args.push("--config", JSON.stringify({ bundle: { createUpdaterArtifacts: false } }));
}

const run = spawnSync(process.execPath, [cli, ...args], { stdio: "inherit", cwd: desktop });
process.exit(run.status ?? 1);
