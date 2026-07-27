---
name: nurb
description: Design 3D-printable parts as Python functions with nurb. Use when the user wants a part designed, changed, or checked for 3D printing (a bracket, mount, holder, enclosure, shelf, or any STL/STEP to print), and in any directory with a parts/ folder. The user describes the part and judges it in a browser; you model it.
---

# nurb

A part is a Python function and its keyword defaults are its parameters. A project is any directory with a `parts/` folder; there is no init step. You are the CAD operator: the user describes the part and you do everything else, including creating the project and modelling. Keep `nurb dev` running in the background and hand the user its URL, because the browser it serves is where they judge the result.

**Run `nurb rules` first.** It prints the design doctrine: printability, load paths, the polish pass, the kernel traps, card discipline, and what to verify. This file stays thin on purpose so there is one copy of that, in the package, which cannot drift.

**Ask before you model.** Anything the part has to fit (an opening, a bracket, the object it holds) is a question for the user: ask for those measurements in one batch before the first build, using your harness's question tool if it has one, and record the answers in `measurements.toml` the way the doctrine describes. Anything that is taste rather than fit becomes a parameter instead of a question, because the viewer's sliders are how the user answers those. A guessed proportion costs one slider drag; a guessed clearance prints the wrong part.

```
nurb rules            the doctrine, read this first
nurb new <name>       create parts/<name>.py and its card
nurb build [part]     build once, report size and timing
nurb check [part]     the printability rules, --strict for CI
nurb card [part]      regenerate a card's AUTO block
nurb verify [part]    the doctrine's verification list: solids, flex, checks, card
nurb render [part]    PNG into build/, so you can look at what you made
nurb export [part]    STL and STEP into build/, --formats for GLB
nurb extract          find duplication across parts
nurb dev              watch, rebuild, serve the viewer on :7373 or the next free port
```

Read `parts/<name>.md` before editing `parts/<name>.py`. Its `## Don't` section is what was tried and rejected, and it is the only place that records it.

If `nurb` is not on PATH: `uv tool install nurb` or `pip install nurb`.
