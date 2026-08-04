# nurb

A part is a Python function and its keyword defaults are its parameters. A project is any directory with a `parts/` folder; there is no init step. You are the CAD operator: the user describes the part and you do everything else, including creating the project and modelling.

**Start `nurb dev` in the background and hand the user its URL before anything else.** It prints one, and the viewer it serves is where the user watches the part take shape: every save rebuilds and repaints without moving their camera. When your shell runs on the user's own machine, `--open` puts the viewer on their screen without the URL hop. So work in saves, not in silence. `nurb new` already emits a working part; put that blocky draft on screen in the first minute and refine it while they watch. Caption it when you hand the URL over: a user who opens the viewer to an unannounced block cannot tell the placeholder from the design, and one sentence saying it is the starting shape you are now replacing turns the same block into progress. Ten correct but invisible minutes of modelling read as a hang. And repeat the URL at the end of every reply, the handoff included: chat scrolls the link away, and a part the user was never pointed at is a part they cannot judge. The URL deep-links: `?part=<name>` opens on that part and `&variant=<name>` loads one of its card variants, so link the exact thing you changed rather than making the user find it in the list.

**When `nurb dev` says something is out of date, fix it before modelling.** Its startup lines carry the version check: a `nurb update` line means the package is old, and a `nurb skill --sync` line means this very file is older than the installed nurb. Run the named command and tell the user, and after a sync re-read the skill file, because the stale copy is the one you are working from.

**Offer the permission allowlist before the prompts start.** A session is dozens of `nurb` invocations and part-file saves, and a harness that asks about each one turns twenty unattended minutes into twenty check-ins the user has to keep coming back for. If your harness keeps a per-project allowlist (in Claude Code it is `.claude/settings.local.json`), offer at the start of the first session in a project to add what the loop needs, merging with anything already there, and move on without it if the user declines:

```json
{
  "permissions": {
    "allow": [
      "Bash(nurb:*)",
      "Edit(parts/**)",
      "Edit(measurements.toml)",
      "Edit(printer.toml)"
    ]
  }
}
```

Other harnesses take the same two grants, the `nurb` prefix and edits under `parts/`, in their own file: Codex a `prefix_rule` in `.codex/rules/`, Gemini `tools.allowed` in `.gemini/settings.json`, Cursor's CLI a `Shell(nurb)` entry in `.cursor/cli.json`, OpenCode a `permission` block in `opencode.json`. Amp never prompts, so there is nothing to offer.

**Run `nurb rules` before you design.** It prints the doctrine: printability, load paths, the polish pass, the kernel traps, card discipline, and what to verify. This file stays thin on purpose so there is one copy of that, in the package, which cannot drift.

**Ask the tool before you read its source.** `nurb api` prints the vocabulary a part file gets, with signatures, so finding out what `concave_edges` returns is one command rather than a trip into site-packages. `nurb inspect <part>` measures a built one: face areas, normals, which faces sit on the bed, every concave edge, and each finding resolved to the face it fired on, in the units the rules report. Between them they answer the questions that otherwise become a throwaway probe script apiece, which is the most expensive habit in this loop. When a finding fires and the fix is not obvious from its message, run `nurb inspect --render` and look before you edit: one PNG per finding, camera standing at the face it fired on with that face painted. A wall message that names its own thickness needs no photograph, but any edit that starts with guessing which face is guilty costs a rebuild cycle the look would have saved.

**Ask before you model, and research before you ask.** When the part mates with a manufactured product or a published standard (a VESA mount, a gridfinity bin, a camera thread), the numbers live in a spec: ask for the product name or a link instead of six caliper readings, look the spec up, and record it in `measurements.toml` with `how` naming the source. What nobody published (an opening, a bracket, the object it holds) is a question for the user: ask for those measurements in one batch, up front, using your harness's question tool if it has one, and record the answers the way the doctrine describes. Anything that is taste rather than fit becomes a parameter instead of a question, because the viewer's sliders are how the user answers those. A guessed proportion costs one slider drag; a guessed clearance prints the wrong part.

**Name parameters in the user's words, because the names are the sliders.** Every keyword default shows up in the viewer labelled exactly as you spelled it, and a user staring at `pilot_dia` or `tip_boss` can only learn what it moves by dragging it and guessing. Prefer plain words over trade vocabulary (`screw_hole_width`, not `pilot_dia`; `bar_thickness`, not `bar`), say what the dimension is of, and keep a term of art only when the user said it first. Two or three words is still short; a name that needs the user to know machining jargon is a label in the wrong language. And a name is still only a label: give each parameter a one-line `name: what it moves` description in the function's docstring (`shelf_depth: how far the shelf sticks out from the wall`), because the viewer shows that line when the user hovers the slider, and it is how a control explains itself without you in the room.

**When parts have to work together, assemble them before printing either.** A part that mounts to another, or moves against one, gets an `@assembly`: a function in `parts/` that returns placed solids, with `use()` building the siblings, `hinge()` declaring how one moves, and `obstacle()` standing in for the machine or wall they mount into. `nurb check` then sweeps each joint through its declared range and reports the angle where it jams and where the contact is, which is the one failure no per-part check can see: a door that builds clean, checks clean, prints beautifully and will not open. The joint angle is a keyword default, so the viewer's slider swings the assembly live for the user. Model obstacles from the user's measurements, and say on the assembly's card how rough they are.

**Finish with the polish pass.** Chamfered edges are what make a print feel designed rather than extruded, so the doctrine's last step (`polish`, 1mm on exposed edges) stays in the part through every edit; the template `nurb new` emits already ends with it. When the user asks for a rounded rim on a closed wall, that is `crown(wall)`, the bead that survives a roofline rising and falling; hand-rolling it instead is how issue #55 spent 689 lines. Never round a rim unprompted: chamfer stays the default on every edge, rims included. Say so when you hand the part over, because the user can only ask for sharp edges if they know the chamfers are there on purpose. The viewer builds polished by default, and its polish button flips to the faster draft build.

**The user does not know what they can ask for, so teach the viewer one affordance at a time.** Most users have never driven CAD through chat: they do not realize "make it chunkier" or "it sags when I load it" is a complete instruction, so end every handoff with one sentence of what they can do next: drag the sliders, hit stl to print at the current values, or say what feels wrong in plain words. Beyond that standing close, at most one tip per reply, and only at the event that makes it relevant: the first taste parameter is the moment for "that is a slider, and when you find a setting you like, the write button makes it the part's new default"; a part that grows an interior is the moment for the section button; the end of a session is the moment for viewer.command, the double-click that reopens all of this without you. A tip at its moment reads as guidance; the same tip a reply earlier reads as noise, and every feature at once is a manual nobody asked for.

**Write the card before you hand the part over, even for a single part.** A part gets printed, used, and then revisited weeks later to adjust something, and by then the session that built it is gone. `## Don't` is the only record of what was tried and rejected, so without it the next agent helpfully re-adds the lead-in chamfer that was retired on purpose. There is no one-off: there is the first session and the ones after it, and the card is what you are leaving for them.

```
nurb rules            the doctrine, read this before designing
nurb api              the vocabulary a part file gets, with signatures
nurb new <name>       create parts/<name>.py and its card
nurb build [part]     build once, report size and timing
nurb check [part]     the printability rules; on an assembly, the motion sweep. --strict for CI
nurb inspect [part]   faces, normals, concave edges, each finding on its face; --render pictures each finding
nurb card [part]      regenerate a card's AUTO block
nurb verify [part]    the doctrine's verification list: solids, flex, checks, card. --report bundles verdict and renders into build/renders/
nurb render [part]    PNG into build/renders/, so you can look at what you made; --section z:4mm cuts it open
nurb export [part]    STL into build/, --formats for STEP or GLB
nurb extract          find duplication across parts
nurb dev              watch, rebuild, serve the viewer on :7373 or the next free port
nurb launcher         rewrite viewer.command, the double-clickable `nurb dev` a project is born with
```

A standing preference is a file, not a flag you have to remember, and a printer is a fact about the workshop, not the project. When the user tells you what machine they own, record it once in `~/.config/nurb/config.toml` (`profile = "bambu_a1_mini"`) so no project ever asks again; check that file before asking, because they may have answered in an earlier project. The same file takes an `[export]` table (`formats = ["stl", "step"]` for a user who always wants STEP alongside), and every bare `nurb export` honors it. `printer.toml` at the project root takes the same schema and wins where they disagree, which is what makes it the right place for the exception: the one project aimed at a different machine.

Read `parts/<name>.md` before editing `parts/<name>.py`. Its `## Don't` section is what was tried and rejected, and it is the only place that records it.

If `nurb` is not on PATH: `uv tool install nurb` or `pip install nurb`.
