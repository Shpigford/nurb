// Screenshots every design sheet the gallery serves, at 1440x900, into
// .design/gallery/ (gitignored). The design skill runs this and reads the PNGs.
//
//   npm run gallery:shots --workspace packages/ui            every sheet
//   npm run gallery:shots --workspace packages/ui -- 10 13   just those
//   npm run site:hero --workspace packages/ui                the nurb.app hero, into site/
//
// The hero is drawn from the same components the app ships, so re-running this after
// a UI change is how the site keeps showing the app as it is. /release runs it.
//
// It starts its own dev server on a free port and stops it on the way out.
import { spawn, spawnSync } from "node:child_process"
import { createServer } from "node:net"
import { mkdirSync, readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const uiRoot = resolve(here, "..")
const repoRoot = resolve(uiRoot, "../..")
const outDir = resolve(repoRoot, ".design/gallery")
const SESSION = "nurb-ui-gallery"

// Read out of sheets.tsx rather than kept in step by hand, so adding a sheet is
// one edit. The script still never imports TSX.
const sheetsSource = readFileSync(resolve(here, "sheets.tsx"), "utf8")
const SHEETS = [...sheetsSource.matchAll(/\{\s*id:\s*"(\w+)"/g)].map((m) => m[1])
if (SHEETS.length === 0) throw new Error("No sheets found in gallery/sheets.tsx")

// 7373 is the engine, 1420 is tauri dev, 5173 is vite's default and is often taken.
const TAKEN = new Set([1420, 5173, 7373])

function isFree(port) {
  return new Promise((done) => {
    const server = createServer()
    server.once("error", () => done(false))
    server.once("listening", () => server.close(() => done(true)))
    server.listen(port, "127.0.0.1")
  })
}

async function freePort(from = 5290) {
  for (let port = from; port < from + 40; port++) {
    if (TAKEN.has(port)) continue
    if (await isFree(port)) return port
  }
  throw new Error("No free port in the range")
}

function browser(args) {
  const run = spawnSync("agent-browser", [...args, "--session", SESSION], { encoding: "utf8" })
  if (run.status !== 0) throw new Error(`agent-browser ${args.join(" ")} failed: ${run.stderr || run.stdout}`)
  return run.stdout
}

async function waitForServer(url, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url)
      if (response.ok) return
    } catch {
      // not up yet
    }
    await new Promise((r) => setTimeout(r, 250))
  }
  throw new Error(`The gallery never came up at ${url}`)
}

const site = process.argv.includes("--site")
const wanted = process.argv.slice(2).filter((a) => !a.startsWith("-"))
// The hero is a site asset, not a design sheet, so a plain run leaves it out.
const sheets = site ? ["hero"] : wanted.length ? SHEETS.filter((id) => wanted.includes(id)) : SHEETS.filter((id) => id !== "hero")

// The sheets set headlines in Satoshi, which is fetched rather than committed.
spawnSync("sh", [resolve(uiRoot, "scripts/fetch-satoshi.sh")], { stdio: "inherit" })

const port = await freePort()
mkdirSync(outDir, { recursive: true })

// The workspace binary, not npx: killing npx leaves the vite it spawned running.
const vite = spawn(
  resolve(repoRoot, "node_modules/.bin/vite"),
  ["--config", "gallery/vite.config.ts", "--port", String(port), "--strictPort"],
  { cwd: uiRoot, stdio: "ignore" }
)

let failed = null
try {
  const base = `http://localhost:${port}/`
  await waitForServer(base)
  if (site) {
    // One 2x JPEG: sharp on retina, and the phone layout crops into it.
    browser(["set", "viewport", "1440", "900", "2"])
    browser(["open", `${base}#/sheet/hero`])
    browser(["wait", "2500"])
    const path = resolve(repoRoot, "site/app.jpg")
    browser(["screenshot", path, "--screenshot-format", "jpeg", "--screenshot-quality", "88"])
    console.log(path)
  }
  if (!site) browser(["set", "viewport", "1440", "900"])
  for (const id of site ? [] : sheets) {
    browser(["open", `${base}#/sheet/${id}`])
    // The viewer builds its scene from a GLB, so give three.js a frame or two.
    browser(["wait", "1500"])
    const path = resolve(outDir, `sheet-${id}.png`)
    browser(["screenshot", path])
    console.log(path)
  }
} catch (error) {
  failed = error
} finally {
  try {
    browser(["close"])
  } catch {
    // the browser may already be gone
  }
  vite.kill()
}

if (failed) {
  console.error(failed.message)
  process.exit(1)
}
