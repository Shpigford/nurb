---
name: nurb
description: Design 3D-printable parts as Python functions with nurb. Use when the user wants a part designed, changed, or checked for 3D printing (a bracket, mount, holder, enclosure, shelf, or any STL/STEP to print), and in any directory with a parts/ folder. The user describes the part and judges it in a browser; you model it.
---

# nurb

A part is a Python function and its keyword defaults are its parameters. A project is any directory with a `parts/` folder; there is no init step. You are the CAD operator: the user describes the part and you do everything else, including creating the project and modelling.

**Start `nurb dev` in the background and hand the user its URL before anything else.** It prints one, and the viewer it serves is where the user watches the part take shape: every save rebuilds and repaints without moving their camera. When your shell runs on the user's own machine, `--open` puts the viewer on their screen without the URL hop. So work in saves, not in silence. `nurb new` already emits a working part; put that blocky draft on screen in the first minute and refine it while they watch. Ten correct but invisible minutes of modelling read as a hang. And repeat the URL at the end of every reply, the handoff included: chat scrolls the link away, and a part the user was never pointed at is a part they cannot judge. The URL deep-links: `?part=<name>` opens on that part and `&variant=<name>` loads one of its card variants, so link the exact thing you changed rather than making the user find it in the list.

**Run `nurb rules` before you design.** It prints the doctrine: printability, load paths, the polish pass, the kernel traps, card discipline, and what to verify. This file stays thin on purpose so there is one copy of that, in the package, which cannot drift.

**Ask the tool before you read its source.** `nurb api` prints the vocabulary a part file gets, with signatures, so finding out what `concave_edges` returns is one command rather than a trip into site-packages. `nurb inspect <part>` measures a built one: face areas, normals, which faces sit on the bed, every concave edge, and each finding resolved to the face it fired on, in the units the rules report. Between them they answer the questions that otherwise become a throwaway probe script apiece, which is the most expensive habit in this loop.

**Ask before you model.** Anything the part has to fit (an opening, a bracket, the object it holds) is a question for the user: ask for those measurements in one batch, up front, using your harness's question tool if it has one, and record the answers in `measurements.toml` the way the doctrine describes. Anything that is taste rather than fit becomes a parameter instead of a question, because the viewer's sliders are how the user answers those. A guessed proportion costs one slider drag; a guessed clearance prints the wrong part.

**Finish with the polish pass.** Chamfered edges are what make a print feel designed rather than extruded, so the doctrine's last step (`polish`, 1mm on exposed edges) stays in the part through every edit; the template `nurb new` emits already ends with it. Say so when you hand the part over, because the user can only ask for sharp edges if they know the chamfers are there on purpose. The viewer builds polished by default, and its polish button flips to the faster draft build.

**Write the card before you hand the part over, even for a single part.** A part gets printed, used, and then revisited weeks later to adjust something, and by then the session that built it is gone. `## Don't` is the only record of what was tried and rejected, so without it the next agent helpfully re-adds the lead-in chamfer that was retired on purpose. There is no one-off: there is the first session and the ones after it, and the card is what you are leaving for them.

```
nurb rules            the doctrine, read this before designing
nurb api              the vocabulary a part file gets, with signatures
nurb new <name>       create parts/<name>.py and its card
nurb build [part]     build once, report size and timing
nurb check [part]     the printability rules, --strict for CI
nurb inspect [part]   faces, normals, concave edges, each finding on its face
nurb card [part]      regenerate a card's AUTO block
nurb verify [part]    the doctrine's verification list: solids, flex, checks, card
nurb render [part]    PNG into build/, so you can look at what you made
nurb export [part]    STL and STEP into build/, --formats for GLB
nurb extract          find duplication across parts
nurb dev              watch, rebuild, serve the viewer on :7373 or the next free port
nurb launcher         rewrite viewer.command, the double-clickable `nurb dev` a project is born with
```

A standing preference is a file, not a flag you have to remember: a user who never wants STEP gets `formats = ["stl"]` under `[export]` in `printer.toml`, and every bare `nurb export` honors it.

Read `parts/<name>.md` before editing `parts/<name>.py`. Its `## Don't` section is what was tried and rejected, and it is the only place that records it.

If `nurb` is not on PATH: `uv tool install nurb` or `pip install nurb`.
