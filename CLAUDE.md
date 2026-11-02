# nurb

Agentic CAD for 3D printing. A part is a Python function; a long-lived process rebuilds it on save and pushes geometry to a browser without moving the camera.

Built on build123d (OCCT), so parts are real B-rep solids.

## Long runs

- Done means the checks for what you touched pass, you saw the changed path work (see "Verify before claiming"), and the summary states the desktop pass. Stop there.
- Stop and ask only when you are blocked, or before something outside this worktree: `desktop/scripts/release.sh` outside a `/release` run (it publishes a GitHub release), a merge, a force-push, or deleting data.
- Run the full suite once. After it is green, verify later patches with focused tests. One adversarial review pass per task.
- Watch processes, not agents. A subagent with no command running is stuck, so stop it.
- When a run has more than a few steps, keep the checklist in `.context/TASKS.md` and tick items as they land. It survives the context summary; your memory of the plan does not.

## The part contract

One convention carries the whole system:

```python
from nurb import *

@part
def dispenser(width=80.0, height=120.0, wall=2.0, draft=False):
    body = Box(width, height, wall)
    if draft:
        return body
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    return polish(body, keep, 1.0)
```

**Keyword defaults are the parameters.** That single declaration feeds the agent, the viewer's sliders, the tests, and any future configurator. Never add a parallel `PARAMS` dict; the two would drift.

`draft` is optional and injected by the runtime, never passed by callers. When true, skip the polish pass. Worth 20% on a real part, not the 18x a cube suggested: chamfers are 23% of the gridfinity shelf's build.

The build is nearly all of the loop. Tessellation used to look like the larger half at 620ms, and almost all of that was one pathological iterator in build123d rather than any geometry; `builder._triangulate` reads the same triangles by index in 30ms. Write a continuous dimension as a float (`chamfer_size=1.0`) and a count as an int (`bracket_count=4`): the viewer reads the type of the default to decide whether that parameter's slider steps by one.

## Repo layout

One repo, one engine, one UI, one route for building: the agent drives the local MCP tools, whether it runs inside the app or connects from outside.

```
engine/     the Python engine and the local serve process (uv project; run everything here with `cd engine`)
packages/   @nurb/ui (tokens, viewer, panels, cards) and @nurb/workbench (the part page the engine serves and the app embeds)
desktop/    the Tauri app: Rust core, React shell, bundles the engine wheel
site/       nurb.app marketing pages
```

## Running it

```
cd engine
uv run python -m nurb.serve   serve the workbench, the API and the MCP endpoint on :7373 or the next free port
uv run pytest                 run the suite
```

The suite includes the parts in `engine/examples/`. The npm workspace (`desktop/`, `packages/*`) is rooted at the repo root: `npm ci` there, then `npm run build --workspace packages/workbench` writes the page into `engine/src/nurb/workbench/`.

A project is rows in the local SQLite database, owned by the one serve process. A folder containing `parts/` is how a project comes in (Import) and goes back out (checkout), and there is no init step, and there never should be.

A release is a version bump merged to main: `uv version X.Y.Z` in `engine/`, plus the matching semver `version` in `desktop/src-tauri/tauri.conf.json` and the matching `version` in `packages/ui/package.json` (a test enforces all three agree). `desktop/scripts/release.sh` builds the signed desktop app, uploads it to the `vX.Y.Z` GitHub release, and refreshes the updater feed the installed apps poll. The `/release` skill runs the whole ceremony end to end, changelog included.

## Layout

```
engine/src/nurb/registry.py      @part, signature introspection
engine/src/nurb/builder.py       load, build, tessellate, GLB
engine/src/nurb/checks.py        printability rules, convexity, Finding/Context, variants
engine/src/nurb/compare.py       deviation from a target mesh, the ghost's numbers
engine/src/nurb/polish.py        the bisecting polish pass, and chamfer with real errors
engine/src/nurb/orient.py        stand(), the diagonal print stance with its bed facet
engine/src/nurb/probe.py         what the inspect tool measures, in the rules' own units
engine/src/nurb/api.py           the vocabulary, derived from __all__ so it cannot drift
engine/src/nurb/printers.toml    shipped printer profiles, named by a project's printer.toml
engine/src/nurb/card.py          the card's AUTO block
engine/src/nurb/extract.py       duplication across sibling parts, up to alpha-equivalence
engine/src/nurb/mesh.py          import_stl(), the flat-faced meshes that can be a solid
engine/src/nurb/scan.py          a mesh file measured, and described as words plus a picture for a chat attachment
engine/src/nurb/threemf.py       the 3MF reader, standard library only, Bambu multi-file layout included
engine/src/nurb/measurements.py  measured(), and the refusal to guess
engine/src/nurb/edit.py          the keyword-default rewrite behind Apply
engine/src/nurb/labels.py        a person's names for spots on a part, snapped to the surface and checked against each build
engine/src/nurb/render.py        headless PNG through the numpy rasterizer in raster.py
engine/src/nurb/raster.py        GLB in, flat-shaded PNG out: the four views, the composite, and the PNG encoder
engine/src/nurb/slicing.py       the handoff to an installed slicer, and the two numbers back
engine/src/nurb/doctrine.md      the doctrine itself, shipped in the package
engine/src/nurb/serve.py         HTTP, websocket and MCP on one port, the one process that owns the database
engine/src/nurb/mcp_server.py    the tool dispatcher: tools.json is the contract, this is its only implementation
engine/src/nurb/tools.json       the tool contract an agent sees
engine/src/nurb/db.py            the SQLite store: projects, parts, revisions, build runs
engine/src/nurb/materialize.py   rows written back out as the folder the engine can build
engine/src/nurb/folder.py        import_folder and checkout, the two doors between a folder and the store
engine/src/nurb/guide.py         doctrine, vocabulary and kernel notes as the one document a model reads
engine/src/nurb/workbench/       the built workbench page, from packages/workbench
engine/examples/notch/           the real parts, which are also the calibration set
engine/tests/test_notch_fit.py   the hanging interface, asserted for every configuration
engine/tests/                    rules and examples, both cases per rule
```

The model leaderboard (tasks, scorer, runner, and every submitted run) lives in its own repo, [Shpigford/nurb-benchmarks](https://github.com/Shpigford/nurb-benchmarks): submissions dwarf everything else and keep growing, so they stay out of this repo. `site/benchmarks.html` here is regenerated from that repo's submissions by the `/leaderboard` skill.

## Rules

### This file is for developing nurb, not for using it

The part-design workflow (open the workbench first thing, end every reply with its URL, model while the user watches) is the agent-facing guidance the MCP server ships: its `instructions` and the `read_guide` tool. It applies in a user's parts project, never in this repo. Here you are building the tool. When verifying workbench or serve changes, run `NURB_HOME=<scratch dir> uv run python -m nurb.serve` in the background, import `examples/notch`, and share the URL for that; `?part=<name>&variant=<name>` deep-links to the exact configuration you want looked at. Never run a serve, a test probe or a review against the default home: that is the user's real library, and a dev import or a junk project left there shows up in their sidebar.

### Every feature gets a surface in the app

The desktop app is the primary entry point, and it is what to optimize for. A capability that exists only as a tool the agent can call, or only as a serve route, does not exist for the person who downloaded the app: they will never see it and never learn it is there. "The agent can run it when asked" is not a surface either, because it requires the user to already know the feature exists in order to ask for it.

So a feature is not done when the command works. It is done when someone looking at their part can see it and use it without being told. Ship the command and the surface in the same change, and if the surface is genuinely wrong for the feature, say why out loud rather than deferring it.

Nearly always that surface belongs in `packages/workbench`, not in `desktop/src`. The app embeds the workbench, so one control there reaches both the app and the served page in a browser. React shell work is for what only the shell can do: the window, the rail, projects, chat, updates. Anything about the part itself goes in the workbench.

Two things a surface owes the user that a command does not. It must not dead-end: when a feature needs something the project has not chosen yet, offer the choice in place rather than printing what the user should have configured. And a result that outlived its geometry is worse than no result, so anything cached from a build clears when that part rebuilds.

### No change is done until the desktop is accounted for

The recurring failure mode in this repo: a change lands in the Python engine or the viewer, works in a browser, and ships with the desktop app never considered. That is backwards. The desktop app is the primary UI, so every change ends with an explicit desktop pass: what does `desktop/src` need for this, and if the honest answer is nothing, say that in the summary rather than leaving it unexamined.

The shell renders the part surface in-process from `packages/workbench` (`PartView`, `useProject`, `api.ts`, `live.ts`) and reads projects and parts straight from the serve over `fetch` and the `/ws` change bus; there is no iframe, no `postMessage`, and no polling. Selection is local state in `desktop/src/App.tsx`. So check each seam: a new server field reaches the app only through the workbench's `api.ts` types and whichever of `ProjectsRail.tsx` or `PartView` shows it; anything the rail summarises (part counts, last built) comes from `GET /api/projects`, so a new summary field needs that route; a change to a `packages/workbench` module is a change to the app, so run the desktop checks after it too. The page origin is `tauri://localhost` in the bundle and `http://localhost:1420` under `tauri dev`: the serve's CORS allowlist and its same-origin write guard name both, and a secure context refuses `ws://localhost` (loopback by IP is exempt), so verify transport changes in a `tauri build --debug` bundle, never only in dev. Labels: embed mode no longer exists, and the app speaks to hobbyists, so no user-facing string names a `.py` or `.md` file.

The check is cheap: grep `desktop/src` for the concept you touched, and run `npm run typecheck` plus `npm test` in `desktop/` whenever it or `packages/workbench` changed. Debug builds listen on `127.0.0.1:7399` for `create:`, `open:`, `import:`, `part:`, `param:`, `send:`, `eval:` and plain composer text, so a WKWebView can be driven and probed without touching the keyboard; `eval:` results land on the app's stderr. Point a debug bundle at a scratch data home with `NURB_DESKTOP_DATA=<dir>` (provisioning happens once per home, so reuse it); and activate the window before `screencapture -l<id>`, because an occluded WKWebView paints blank. The composer hooks (`send:` and plain text) only reach the visible chat, so enter the workspace with `part:` first.

### The part is the unit, the project is a folder

Most people make one part at a time. A project exists only for a system, like a storage set whose bins and rails must agree, and it is born from parts that already exist. So creation, chat, the workspace header and the library all speak in parts: "New part" opens the workspace in one click, the conversation belongs to the part, and a project is something a part is added to later. Nothing may say "project" where the person is looking at a part.

### Tool names stay boring

The tools' user is a language model, while the app's user is a person; both surfaces are real and neither substitutes for the other. An agent that has never seen this server can guess `run_build`, `read_findings`, `write_part_source`. It cannot guess a themed alias. Every clever name is an indirection that degrades in a fresh context. The brand can be distinctive; the interface cannot.

### Never port Fusion scaffolding

Notch's Fusion timelines contain constructions that exist only to work around a stateful CAD kernel: `ChannelTool`, the 16-lobe comb, `CombWeb`, `JoinComb`, fixed over-counts, derive links. In code these are a `for` loop and an `import`. Porting them imports accidental complexity into a system that never had the problem.

What does survive is physics: the print doctrine, sliver thresholds, chamfer sizing limits, and chamfer ordering effects.

### Prefer `new_edges` over geometric selectors for chamfers

Each chamfer changes topology, so selectors resolved against pristine geometry drift once an earlier chamfer runs. `new_edges(before, combined=after)` returns exactly the edges an operation created and sidesteps the problem. It is the algebra-mode equivalent of a builder's `Select.LAST`, and algebra mode is what a part file uses, so `part.edges() - last` is not available to you. Reach for it before falling back on strict operation ordering.

### Two chamfered edges need room between them

More than `2 * chamfer_size` of face, or OCCT fails with `BRep_API: command not done`. This is the analogue of Fusion's `ASM_BL_NO_MATE` and it is the single most common way a part stops building. The trap: every edge chamfers fine on its own and only the batch fails, so testing them one at a time reports that nothing is wrong. Bisect the set.

### Systems are extracted, never scaffolded

Notch did not begin as a system; `block_width = 25.16` exists because a real wall got measured after parts existed. Guessing what is shared before you know propagates the wrong abstraction. The tool is `extract`, not `new system`.

It reports and does not rewrite, because choosing which free names become parameters and what the function is called are judgements about what the thing *is*, and noticing is the only mechanical part. Run over the finished port it found `system.slab()` in six files at once. **The test of a real extraction is what does not use it**: three parts still build their own plate, because they genuinely differ, and a helper with a flag for each of them would have been the wrong abstraction wearing the right name.

### Generated files stay nearly empty

Scaffolders traditionally emit commented placeholder blocks. That is fine for humans skimming and actively bad for an agent, where it is context to read past. A new part is a working part and a card with headings only.

### Verify before claiming

Untested code is a guess. Before saying something works: run it, trigger the exact path changed, and observe the result. For viewer changes that means a screenshot, not a DOM query. Two traps already hit here, both of which produced confident wrong conclusions:

- `elementFromPoint` skips `pointer-events: none` elements, so it reports the canvas covering an overlay when painting is fine.
- A repro that starts at equilibrium proves nothing. The ResizeObserver loop needs an initial size mismatch to ratchet against.

Also: `print(..., flush=True)` in the server. Python buffers stdout when it is not a tty, and buffered output makes debugging the watcher blind.

## Engine conventions

This is source-available under FSL-1.1-MIT, which converts each release to MIT two years after it ships. Build as though every file will be read by a stranger.

- **No secrets, ever.** No API keys, no absolute paths pointing into a home directory, no personal data in committed files or test fixtures.
- **Public API is `engine/src/nurb/__init__.py`.** Anything exported there is a promise. Everything else is internal and free to change. Keep the surface small.
- **Dependencies are a cost.** Five right now: build123d, mcp, pillow, trimesh, websockets. Adding a sixth needs a reason that survives being asked out loud.
- **Watch the transitive license surface.** build123d is Apache-2.0, but it pulls OCP, whose wheel bundles OCCT native libraries under LGPL-2.1-with-exception. That is fine while we dynamically link and do not redistribute them. It stops being automatic if nurb is ever bundled into a single-file binary, which would require shipping the OCCT license and keeping the library replaceable. Attribution lives in the README's third-party notices.
- **Never commit Satoshi.** Its Fontshare license allows embedding it in the app and serving it on nurb.app, and forbids a public repository. `packages/ui/scripts/fetch-satoshi.sh` downloads it before the workbench and desktop builds (strict under `NURB_REQUIRE_FONTS=1`, which the release sets), and the site loads it from Fontshare's servers. The Nucleo icons in `Icon.tsx` are capped at 100 in public source by their license, and `@nurb/ui` stays private, because publishing it would make it an icon library.
- **Errors are the interface.** Most users will meet this tool through a failure. Tracebacks get trimmed to the user's own file; messages say what went wrong and what to do, never just "invalid input".
- **The doctrine ships in the package**, reached by an agent through the `read_guide` tool. One source of truth, assembled at call time so an upgrade cannot leave a stale copy teaching the wrong rules.
- **The workbench works offline.** Everything it *needs* is local: three.js and the fonts are bundled into `engine/src/nurb/workbench/` by the workbench build, because a CAD tool that needs a CDN is broken on a plane. Anything new the workbench imports is bundled too, and `pyproject.toml`'s `source-include` has to carry the output. Network is allowed for nudges that degrade silently, like the daily update check, which also stays out of headless renders.
- **Examples are tests.** `engine/examples/` holds real parts that the suite builds, so a broken example is a red build rather than a stale README.

## Style

- Match the surrounding code. Comments explain *why*, and only where the reason is not obvious from the code.
- No em-dashes in user-facing copy, docs, or comments.
- Commit messages describe what changed and why, in plain sentences.
- **Never hard-wrap prose. Ever.** One paragraph is one line; editors soft-wrap. This applies to every markdown and text file, and it applies even when the surrounding file is already wrapped: fix the paragraph you touch instead of matching the wrapping. Code, tables, and fenced blocks keep their formatting.
