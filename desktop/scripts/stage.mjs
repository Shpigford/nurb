// npm runs scripts through cmd.exe on Windows, where `sh` does not exist and
// System32's bash.exe is the WSL shim, not a shell for this filesystem. This
// launcher finds Git Bash (a dev requirement either way; the repo is a git
// checkout) and runs stage.sh with it; everywhere else it is just `sh`.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const script = path.join(path.dirname(fileURLToPath(import.meta.url)), "stage.sh");

function shell() {
  if (process.platform !== "win32") return "sh";
  const gitCore = spawnSync("git", ["--exec-path"], { encoding: "utf8" }).stdout?.trim();
  const candidates = [
    // <git>/mingw64/libexec/git-core -> <git>/bin/bash.exe
    gitCore && path.join(gitCore, "..", "..", "..", "bin", "bash.exe"),
    "C:\\Program Files\\Git\\bin\\bash.exe",
  ].filter(Boolean);
  const found = candidates.find((candidate) => existsSync(candidate));
  if (!found) {
    console.error("stage: could not find Git Bash to run stage.sh; install Git for Windows");
    process.exit(1);
  }
  return found;
}

const run = spawnSync(shell(), [script], { stdio: "inherit" });
process.exit(run.status ?? 1);
