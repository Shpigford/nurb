# nurb

A part is a Python function and its keyword defaults are its parameters. A project is any
directory with a `parts/` folder.

**Run `nurb rules` first.** It prints the design doctrine: printability, load paths, the
polish pass, the kernel traps, card discipline, and what to verify. This file stays thin
on purpose so there is one copy of that, in the package, which cannot drift.

```
nurb rules            the doctrine, read this first
nurb build [part]     build once, report size and timing
nurb check [part]     the printability rules, --strict for CI
nurb card [part]      regenerate a card's AUTO block
nurb render [part]    PNG into build/, so you can look at what you made
nurb export [part]    STL/STEP/GLB into build/
nurb dev              watch, rebuild, serve the viewer on :7373
```

Read `parts/<name>.md` before editing `parts/<name>.py`. Its `## Don't` section is what
was tried and rejected, and it is the only place that records it.
