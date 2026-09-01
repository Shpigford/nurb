"""nurb command line."""

import argparse
import asyncio
import errno
import importlib.metadata
import pathlib
import sys

PART_TEMPLATE = '''from nurb import *


@part
def {name}(width=40.0, depth=30.0, height=20.0, wall=2.0, draft=False):
    body = Box(width, depth, height)
    if draft:
        return body
    # Name what must stay sharp, then let `polish` chamfer whatever the kernel takes.
    # A bare `chamfer(...)` is all or nothing: one edge that cannot land loses the lot.
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    return polish(body, keep, 1.0)
'''

CARD_TEMPLATE = """# {name}

## What it is

## Design notes

## Don't

## Changelog
"""


def project_root(start=None):
    here = pathlib.Path(start or pathlib.Path.cwd()).resolve()
    for d in [here, *here.parents]:
        if (d / "parts").is_dir():
            return d
    return here


CLI_ONLY_OPEN = "<!-- cli-only -->"
CLI_ONLY_CLOSE = "<!-- /cli-only -->"


def agents_text(embed=False):
    """The shim as a project should receive it, for the harness that will read it.

    Parts of the file only make sense where the agent owns the loop: starting
    `nurb dev`, keeping the package and skill current, and asking for permission
    grants. An app that embeds the viewer already does all three, so an agent
    told to do them there wastes turns and edits files it does not own.
    """
    from . import __file__ as pkg

    text = (pathlib.Path(pkg).parent / "agents.md").read_text(encoding="utf-8")
    kept, skipping = [], False
    for line in text.splitlines():
        if line == CLI_ONLY_OPEN:
            skipping = True
            continue
        if line == CLI_ONLY_CLOSE:
            skipping = False
            continue
        if not (embed and skipping):
            kept.append(line)
    out = "\n".join(kept)
    while "\n\n\n" in out:
        out = out.replace("\n\n\n", "\n\n")
    return out.strip("\n") + "\n"


def _seed_agents(root, embed=False):
    """Put a pointer to `nurb rules` where an agent will find it on day one.

    Everything an agent needs is already reachable: `nurb --help` lists the commands and
    `nurb rules` prints the doctrine. What was missing is any reason to type `nurb` at
    all. A fresh project is two files that look like an ordinary build123d script, so an
    agent reads them as one, writes generic geometry, and never learns the tool exists.

    This is not an init step. It is the command you were already running, it respects
    harness files of the user's own, and `nurb new` prints everything it writes either
    way.
    """
    full_shim = agents_text()
    embedded_shim = agents_text(True)
    shim = embedded_shim if embed else full_shim
    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    if agents.is_file():
        # Heal projects seeded before Claude's native pointer was added, but
        # never make a second harness file alongside one the user wrote.
        existing = agents.read_text(encoding="utf-8")
        if existing in (full_shim, embedded_shim):
            written = []
            if existing != shim:
                agents.write_text(shim, encoding="utf-8")
                written.append(agents)
            if not claude.is_file():
                claude.write_text("@AGENTS.md\n", encoding="utf-8")
                written.append(claude)
            return written, None
        legacy_generated = (
            existing.startswith("# nurb\n")
            and "`nurb rules`" in existing
            and "If `nurb` is not on PATH:" in existing
        )
        if legacy_generated:
            if not claude.is_file():
                claude.write_text("@AGENTS.md\n", encoding="utf-8")
                return [claude], None
            return [], None
        return [], agents.name
    if claude.is_file():
        return [], claude.name
    agents.write_text(shim, encoding="utf-8")
    # Claude Code deliberately does not discover AGENTS.md. Import the shared
    # doctrine from its native file instead of maintaining a second copy.
    claude.write_text("@AGENTS.md\n", encoding="utf-8")
    return [agents, claude], None


def cmd_new(args):
    # The desktop app creates projects under one shared directory, which may itself
    # already be a nurb project. Its explicit root keeps this seed inside the new
    # child instead of letting project_root() walk upward into an existing parts/.
    root = (
        pathlib.Path(args.root).resolve()
        if getattr(args, "root", None)
        else project_root()
    )
    parts = root / "parts"
    # The first part is the project's birth, the only moment the launcher appears
    # on its own. Deleting it is a decision, so it is never written back over one.
    born = not parts.is_dir()
    parts.mkdir(parents=True, exist_ok=True)
    name = args.name.replace("-", "_")
    py, md = parts / f"{name}.py", parts / f"{name}.md"
    if py.exists():
        sys.exit(f"{py} already exists")
    py.write_text(PART_TEMPLATE.format(name=name), encoding="utf-8")
    md.write_text(CARD_TEMPLATE.format(name=name), encoding="utf-8")
    written = [py, md]
    if born:
        written.append(_write_launcher(root))
    seeded, already = _seed_agents(root, getattr(args, "embed", False))
    written.extend(seeded)
    for path in written:
        print(f"  {path.relative_to(root)}")
    if already:
        print(f"  {already} is yours, so it was left alone. Point it at `nurb rules`.")


def _resolve(root, name):
    from . import builder

    found = builder.find_parts(root)
    if not found:
        sys.exit("no parts found (expected a parts/ directory)")
    if name is None:
        return found
    match = [p for p in found if p.stem == name.replace("-", "_")]
    if not match:
        sys.exit(f"no part named {name}. have: {', '.join(p.stem for p in found)}")
    return match


def _configs(path, base=None):
    """A part's configurations: itself, then whatever variants its card declares.

    Every command that walks parts walks these instead, so a variant is checked,
    exported and reported exactly like a part. A card that will not parse comes back
    as an empty list with the reason printed, which is how the per-part commands
    already report a part that will not build.
    """
    from . import checks

    try:
        return checks.configurations(path, base=base)
    except Exception as exc:
        print(f"  {path.stem}: {type(exc).__name__}: {exc}")
        return []


def cmd_build(args):
    import hashlib
    import json

    from . import builder

    root = project_root()
    # What the last build of each configuration produced. A cut that misses the body
    # subtracts nothing and still builds, so an edit can succeed, take its usual
    # milliseconds, and leave the part exactly as it was. This is how the line says so.
    store = root / "build" / "fingerprints.json"
    try:
        before = json.loads(store.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        before = {}
    prints = dict(before)
    for path in _resolve(root, args.part):
        source = path.relative_to(root).as_posix()
        old_configs = before.get(source, {})
        new_configs = dict(old_configs)
        prints[source] = new_configs
        for name, overrides, _ in _configs(path):
            try:
                shape, _, ms = builder.build(path, overrides=overrides or None, draft=args.draft)
                info = builder.stats(shape)
                bbox = " x ".join(str(v) for v in info["bbox"])
                mark = hashlib.blake2b(
                    builder.to_glb(shape), digest_size=8
                ).hexdigest()
                same = old_configs.get(name) == mark
                new_configs[name] = mark
                note = ", geometry unchanged since last build" if same else ""
                print(f"  {name}: {bbox} mm  {ms:.0f}ms{note}")
            except Exception as exc:
                print(f"  {name}: {type(exc).__name__}: {exc}")
    if prints != before:
        store.parent.mkdir(parents=True, exist_ok=True)
        store.write_text(json.dumps(prints, indent=1, sort_keys=True), encoding="utf-8")


def cmd_check(args):
    from . import builder, checks

    root = project_root()
    # Resolved once, and only when asked for: `--printer a1_mini` answers "does this
    # fit that machine" without touching printer.toml. The file, when present, is
    # already the default inside `checks.configurations`.
    base = None
    if args.printer:
        try:
            base = checks.printer(root, args.printer)
        except ValueError as exc:
            sys.exit(f"  {exc}")
    else:
        # A profile picked up from a file is invisible, and invisible is how two
        # machines check the same part differently for no stated reason.
        try:
            profile, source = checks.profile_choice(root)
        except ValueError:
            profile = None  # a broken file gets its real error on the first part
        if profile:
            print(f"  printer: {profile} ({source})")
    worst = 0
    for path in _resolve(root, args.part):
        configs = _configs(path, base=base)
        if not configs:
            worst = 2
        for name, overrides, ctx in configs:
            try:
                shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
                found = checks.run(shape, ctx)
            except Exception as exc:
                print(f"  {name}: {type(exc).__name__}: {exc}")
                worst = 2
                continue
            if not found:
                print(f"  {name}: clean")
                continue
            fails = sum(1 for f in found if f.severity == checks.FAIL)
            # A note is the part answering the checker, not the checker complaining, so
            # it never moves the exit code. It is still counted out loud: "0 to fix"
            # beside three findings reads like a bug in the checker unless the line
            # says where the other three went, and support material is a running cost
            # worth seeing the size of every time.
            notes = sum(1 for f in found if f.severity == checks.NOTE)
            said = f"{len(found)} finding(s), {fails} to fix"
            if notes:
                said += f", {notes} on supports"
            print(f"  {name}: {said}")
            for finding in found:
                print(f"      {finding}")
            worst = max(worst, 2 if fails else 1 if notes < len(found) else 0)
    # Project-level, after the parts: a guessed dimension produces a part that builds,
    # checks clean and prints, so the only place it can be caught is here.
    from .measurements import provisional

    for name, how in provisional(root):
        print(f"  measurement {name} is provisional: {how or 'no note'}")
        worst = max(worst, 1)

    if args.strict and worst:
        sys.exit(1)


def _collect_exports(paths):
    """Resolve every artifact name before writing any of them."""
    found, owners = [], {}
    failed = False
    for path in paths:
        configs = _configs(path)
        if not configs:
            failed = True
            continue
        for name, overrides, ctx in configs:
            if name in owners:
                print(
                    f"  duplicate export name {name!r}: "
                    f"{owners[name].name} and {path.name}"
                )
                failed = True
                continue
            owners[name] = path
            found.append((path, name, overrides, ctx))
    if failed:
        sys.exit(1)
    return found


def _standing_formats(root):
    """`[export] formats`, from the project's printer.toml, then the global config.

    A syntax error is left for checks.printer to report, which every export
    reaches on its way to a Context and which names the file and the line.
    """
    import tomllib

    from . import checks

    for file in (root / checks.PRINTER_FILE, checks.global_file()):
        if not file.is_file():
            continue
        try:
            block = tomllib.loads(file.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            continue
        formats = block.get("export", {}).get("formats")
        if formats:
            return formats
    return None


def _artifact_size(path):
    n = path.stat().st_size
    return f"{n / 1e6:.1f}MB" if n >= 1e6 else f"{n / 1e3:.0f}kB"


def cmd_export(args):
    from build123d import export_step

    from . import builder, checks, slicing

    root = project_root()
    formats = args.formats or _standing_formats(root) or list(DEFAULT_FORMATS)
    configs = _collect_exports(_resolve(root, args.part))
    out = root / "build"
    out.mkdir(exist_ok=True)
    # A 3MF can carry the print settings the part justifies, but only a slicer knows
    # this release's full config schema, so the upgrade needs one installed and a
    # printer named. Missing either is not an error: the bare file is still correct,
    # and one line says what the export is not carrying.
    kit, bare_because = None, None
    if "3mf" in formats:
        kit, bare_because = slicing.kit(root)
    if bare_because:
        print(f"  3MF will carry geometry only: {bare_because}")
    queue = list(configs)
    while queue:
        path, name, overrides, ctx = queue.pop(0)
        shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
        scene = getattr(shape, "_nurb_scene", None)
        if scene is not None:
            # A merged scene is a weld, not a part, and its obstacles were never
            # going to be printed. Named explicitly, an assembly exports the parts
            # it places instead; in a project sweep those export as themselves, so
            # it just steps aside.
            if not args.part:
                print(f"  {name}: assembly, skipped (its parts export as themselves)")
                continue
            placed = sorted(pathlib.Path(u) for u in scene.uses)
            if not placed:
                sys.exit(f"  {name} is an assembly that places no parts; nothing to print")
            print(f"  {name}: exporting the {len(placed)} part(s) it places")
            queue = [(p, p.stem, None, checks.from_card(p)) for p in placed] + queue
            continue
        for fmt in formats:
            target = out / f"{name}.{fmt}"
            said = ""
            if fmt == "3mf":
                try:
                    builder.write_3mf(shape, target)
                except builder.BuildError as exc:
                    sys.exit(f"  {exc}")
                if kit:
                    settings, notes = slicing.tuned(shape, ctx)
                    machine, process, filament, exe = kit
                    try:
                        slicing.write_project(target, target, machine, process, filament, exe, settings=settings)
                        said = f"  {', '.join(notes)}"
                    except slicing.Unavailable as exc:
                        print(f"  {name}.3mf carries geometry only: {exc}")
            elif fmt == "stl":
                builder.write_stl(shape, target)
            elif fmt == "step":
                export_step(shape, str(target))
            elif fmt == "glb":
                target.write_bytes(builder.to_glb(shape, 0.02, up=ctx.up))
            else:
                # The print used to sit outside this chain, so a typo in `--formats`
                # reported a filename that was never written and exited 0.
                sys.exit(f"  no exporter for {fmt!r}. have: {', '.join(FORMATS)}")
            note = _artifact_size(target)
            if fmt == "stl":
                note += f", {builder.stl_triangles(target):,} triangles"
            print(f"  {target.relative_to(root)}  {note}{said}")
        # A file this export did not rewrite still sits in build/ looking current,
        # and a stale STEP shared as fresh is worse than a missing one.
        for fmt in (f for f in FORMATS if f not in formats):
            stale = out / f"{name}.{fmt}"
            if stale.exists():
                print(
                    f"  {stale.relative_to(root)}  not rewritten ({fmt} is not in this "
                    f"export's formats), delete it or add the format"
                )


# What OCCT says when a chamfer will not land. A part refusing to grow in its own words
# is a design decision; refusing in these is a missing guard.
KERNEL = ("Failed creating a chamfer", "Failed creating a fillet", "BRep_API")


def _flex(path, problems):
    """Grow every count and see what breaks.

    Upward only. Growth is what catches a selector frozen against pristine geometry;
    shrinking alone passes a broken part, because a part with fewer features has fewer
    places to be wrong. A part is allowed to refuse, since a pocket row or a grid has to
    fit between the brackets, but it has to refuse in its own words.
    """
    from . import builder, registry

    declared = builder.load(path)._nurb.params
    counts = [
        name
        for name, default in declared.items()
        if isinstance(default, int) and not isinstance(default, bool)
    ]
    for name in counts:
        for grown in (declared[name] + 1, declared[name] + 2):
            try:
                shape, _, _ = builder.build(path, overrides={name: grown}, draft=False)
            except registry.Rejected:
                continue  # a guard in the part's own words is a decision, not a fault
            except ValueError as exc:
                if any(k in str(exc) for k in KERNEL):
                    problems.append(f"{name}={grown} fails in the kernel: {exc}")
                else:
                    problems.append(f"{name}={grown}: ValueError: {exc}")
                continue
            except Exception as exc:
                problems.append(f"{name}={grown}: {type(exc).__name__}: {exc}")
                continue
            if len(shape.solids()) != 1:
                problems.append(f"{name}={grown} builds {len(shape.solids())} solids")
    return counts


def cmd_verify(args):
    """The doctrine's Verification section, run.

    Two of its six items are not here and cannot be. Checking fit-critical faces by
    coordinate is per part, which is what a project's own tests are for, and looking at
    a render is the one step a machine cannot do for you.
    """
    from . import builder, card, checks

    root = project_root()
    worst = 0
    gathered = []  # what --report needs to picture: nothing is rebuilt to write it
    for path in _resolve(root, args.part):
        problems, built = [], []
        configs = _configs(path)
        if not configs:
            problems.append("the card's settings block will not parse")
        for name, overrides, ctx in configs:
            try:
                shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
            except Exception as exc:
                problems.append(f"{name}: {type(exc).__name__}: {exc}")
                continue
            # The count is the `solids` rule's job now, and it says more than a count.
            found = checks.run(shape, ctx)
            for finding in found:
                # Notes are not problems, and this is the one place that would
                # otherwise disagree with `nurb check --strict` about the same
                # geometry. `found` goes on whole to the card and to --report, which
                # do want them: the verdict describes the part, this list is a to-do.
                if finding.severity == checks.NOTE:
                    continue
                problems.append(f"{name}: {finding}")
            built.append((name, shape, ctx, found))

        counts = _flex(path, problems)

        text = ""
        md = path.with_suffix(".md")
        if md.is_file():
            text = md.read_text(encoding="utf-8")
        if built:
            _, shape, ctx, found = built[0]
            if card.MARK not in text:
                problems.append("card has no generated block yet, run `nurb card`")
            elif card.render(card.facts(shape, ctx, found, variants=built[1:])) not in text:
                problems.append("card disagrees with the geometry, run `nurb card`")
        for heading in card.thin(text):
            problems.append(f"card section is empty: {heading}")

        if problems:
            worst = 1
            print(f"  {path.stem}: {len(problems)} problem(s)")
            for line in problems:
                print(f"      {line}")
        else:
            # Naming them, because "0 flexes" reads like a pass and means the sweep
            # never ran. A part with no counts has nothing to grow, which is worth
            # seeing rather than skimming past.
            grew = f"flexed {', '.join(counts)}" if counts else "no counts to flex"
            print(f"  {path.stem}: ok, {len(configs)} configuration(s), {grew}")
        if args.report:
            gathered.append((path, built, {n: o for n, o, _ in configs}, problems))
    if args.report:
        _report(root, gathered)
        print("  Not covered: fit faces by coordinate. The renders are written; looking at them still is.")
    else:
        print("  Not covered: fit faces by coordinate, and looking at a render.")
    if worst:
        sys.exit(1)


def _report(root, gathered):
    """Write build/renders/<part>.verify.md: the verdict, and pictures of it.

    One markdown file per part, next to the renders it embeds, so the whole bundle
    travels as build/ does: an overview still and a mid-part section per configuration,
    plus one still per finding standing where the finding is. Renders need Playwright;
    without it the report is written anyway and says what is missing, because the
    verdict is the point and the pictures are its evidence.
    """
    from . import builder, render

    out = _renders(root)
    out.mkdir(parents=True, exist_ok=True)
    plans, shots = [], []
    for path, built, overrides_by, problems in gathered:
        per = []
        for name, shape, ctx, found in built:
            _prune_findings(out, name)
            overrides = overrides_by.get(name) or None
            stills = [
                {"part": path, "file": out / f"{name}.verify.png", "overrides": overrides, "check": True},
                # The opposing iso, so the report is not a claim about the half of the
                # part that happened to face the camera. One iso leaves the back, the
                # far side and the underside unseen, and a finding pins only the faces
                # that fired, so an unflagged fault there is pictured nowhere at all.
                # Two opposed corners cover every face between them by construction.
                {"part": path, "file": out / f"{name}.verify.back.png", "view": _opposed(ISO), "overrides": overrides, "check": True},
                # marks off: the findings were checked for the overview, and pins with
                # their material clipped away would float in the emptied half.
                {"part": path, "file": out / f"{name}.verify.section.png", "cut": "z", "overrides": overrides, "marks": False},
            ]
            finds = _finding_shots(out, path, name, overrides, shape, ctx, found)
            per.append((name, shape, found, finds))
            shots += stills + finds
        plans.append((path, per, problems))

    note = None
    if shots:
        try:
            render.snapshots(root, shots)
        except builder.BuildError as exc:
            note = str(exc)

    for path, per, problems in plans:
        lines = [f"# {path.stem}", ""]
        if note:
            lines += [f"No renders this time: {note}", ""]
        if problems:
            lines.append(f"{len(problems)} problem(s):")
            lines += [f"- {p}" for p in problems]
            lines.append("")
        for name, shape, found, finds in per:
            info = builder.stats(shape)
            bbox = " x ".join(str(v) for v in info["bbox"])
            lines += [f"## {name}", "", f"{bbox} mm, {info['volume']}mm3", ""]
            pictured = {s["file"].name for s in finds}
            if found:
                for i, finding in enumerate(found, 1):
                    lines.append(f"- {finding}")
                    pic = f"{name}.finding-{i}.png"
                    if pic in pictured and not note:
                        lines.append(f"  ![finding {i}]({pic})")
            else:
                lines.append("clean: no findings")
            if not note:
                lines += [
                    "",
                    f"![{name}]({name}.verify.png)",
                    "",
                    f"![{name}, from the opposite corner]({name}.verify.back.png)",
                    "",
                    f"![{name}, cut mid-part]({name}.verify.section.png)",
                ]
            lines.append("")
        target = out / f"{path.stem}.verify.md"
        target.write_text("\n".join(lines), encoding="utf-8")
        print(f"  {target.relative_to(root)}")


def cmd_extract(args):
    from . import builder, extract

    root = project_root()
    paths = builder.find_parts(root)
    if len(paths) < 2:
        sys.exit("  extract compares parts against each other, and this project has one")
    found = extract.duplication(paths)
    if not found:
        print(f"  nothing said twice across {len(paths)} parts")
        return
    for run in found:
        where = ", ".join(f"{p.stem}:{line}" for p, line, _, _ in run["sites"])
        print(f"  {run['statements']} statements, {len(run['sites'])} parts: {where}")
        path, start, end, _ = run["sites"][0]
        for line in extract.source(path, start, end).splitlines():
            print(f"      {line}")
        print()
    print(f"  {len(found)} candidate(s), longest first.")
    print("  Lift what is genuinely shared into system.py. Two parts saying the same")
    print("  thing is not yet a system; two parts that would both have to change is.")


def cmd_rules(args):
    # Explicit utf-8: the doctrine says mm², so the locale default breaks it on a machine
    # that is not utf-8, and `nurb rules` is the first command an agent runs.
    doctrine = pathlib.Path(__file__).parent / "doctrine.md"
    print(doctrine.read_text(encoding="utf-8"))


def cmd_api(args):
    """The vocabulary a part file gets, so nobody reads site-packages to find it."""
    from . import api

    for line in api.report():
        print(line)


# `render`'s iso direction at unit length, for tilting a finding camera toward it.
ISO = (0.588, -0.630, 0.504)


def _opposed(direction):
    """The camera standing at the opposite corner, as `render`'s x,y,z view string."""
    return ",".join(f"{-v:.3f}" for v in direction)


def _renders(root):
    """Where every camera-made file lands: stills, sections, finding shots, reports.

    build/ itself is the catalog of deliverables, the STL a slicer picks up, and
    pictures were drowning it. Everything made to be looked at rather than
    printed lives one level down instead.
    """
    return root / "build" / "renders"


def _prune_findings(out, name):
    """A finding still is a claim, and a stale one claims a problem that may be fixed,
    so each regeneration clears the configuration's set before writing the new one."""
    if out.is_dir():
        for old in out.glob(f"{name}.finding-*.png"):
            old.unlink()


def _finding_shots(out, path, name, overrides, shape, ctx, found):
    """One shot per finding, standing where its face can actually be seen.

    Mostly along the face's own normal, tilted a third toward iso so the picture keeps
    some depth: a camera dead-on to a flat underside reads as a 2D outline. The tilt
    collapses when normal and iso oppose, and then the normal alone is right.
    """
    from build123d import Vector

    from . import probe

    shots = []
    rows = probe.finding_faces(shape, ctx, found)
    for i, (finding, row) in enumerate(zip(found, rows), 1):
        if row is None or row["normal"] is None:
            continue
        d = row["normal"].normalized() + Vector(*ISO) * 0.35
        if d.length < 1e-3:
            d = row["normal"]
        shots.append(
            {
                "part": path,
                "file": out / f"{name}.finding-{i}.png",
                "view": f"{d.X:.3f},{d.Y:.3f},{d.Z:.3f}",
                "overrides": overrides or None,
                "check": True,
                "label": str(finding),
            }
        )
    return shots


def cmd_inspect(args):
    """Measure a built part in the units the rules report it in.

    Walks configurations like every other command, so a variant is inspected exactly
    as a part is.
    """
    from . import builder, checks, probe

    root = project_root()
    shots = []
    for path in _resolve(root, args.part):
        for name, overrides, ctx in _configs(path):
            try:
                shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
                found = checks.run(shape, ctx)
            except Exception as exc:
                print(f"  {name}: {type(exc).__name__}: {exc}")
                continue
            for line in probe.report(name, shape, ctx, found, limit=args.limit):
                print(line)
            if args.render:
                # Pruned per configuration, not per shot list: a part that just came
                # back clean still has to lose the stills of the findings it had.
                _prune_findings(_renders(root), name)
                shots += _finding_shots(_renders(root), path, name, overrides, shape, ctx, found)
    if not args.render:
        return
    if not shots:
        print("  nothing to render: no finding sits on a face a camera could be aimed at")
        return
    from . import render

    try:
        written = render.snapshots(root, shots)
    except builder.BuildError as exc:
        sys.exit(f"  {exc}")
    print()
    for shot, png in zip(shots, written):
        print(f"  {png.relative_to(root)}")
        print(f"      {shot['label']}")


def cmd_scan(args):
    """Measure a mesh, so a part can be modelled against something that already exists.

    Takes a file rather than a part name, and needs no project: the scan arrives
    before the part exists, and reading it is how the part's numbers get found.
    """
    from . import scan

    try:
        mesh, unit, source = scan.load(args.file, units=args.units)
    except ValueError as exc:
        sys.exit(f"  {exc}")
    for line in scan.report(args.file, mesh, unit, source):
        print(line)
    if not args.section:
        return
    try:
        cut = scan.section(mesh, args.section, tolerance=args.tolerance)
    except ValueError as exc:
        sys.exit(f"  {exc}")
    print()
    for line in scan.section_report(cut):
        print(line)


def cmd_compare(args):
    """Measure a part against the mesh it is remodelling, both directions.

    The target normally comes from the card, so the dev loop's ghost and this report
    read the same declaration. --against exists for the one-off question.
    """
    from . import builder, checks, compare

    root = project_root()
    named = args.part is not None
    for path in _resolve(root, args.part):
        try:
            declared = compare.setting(checks.settings(path))
        except ValueError as exc:
            sys.exit(f"  {exc}")
        if args.against:
            file, units = args.against, args.units
        elif declared:
            file, units = declared[0], args.units or declared[1]
        else:
            if named:
                sys.exit(
                    f"  {path.stem} has no target mesh. Name one in the card's ```toml"
                    f" settings block:\n      target = \"scans/original.stl\"\n"
                    f"  or ask directly: nurb compare {path.stem} --against <file>"
                )
            print(f"  {path.stem}: no target in its card")
            continue
        try:
            mesh, unit, source = compare.load(root, file, units=units)
        except ValueError as exc:
            sys.exit(f"  {exc}")
        except Exception as exc:
            # Mesh libraries can still fail after parsing; the command's surface is a
            # one-line diagnosis, never an implementation traceback.
            sys.exit(f"  {path.stem}: {type(exc).__name__}: {exc}")
        for name, overrides, _ in _configs(path):
            try:
                shape, _, _ = builder.build(
                    path, overrides=overrides or None, draft=False
                )
                metrics = compare.against(shape, mesh)
            except (ValueError, builder.BuildError) as exc:
                sys.exit(f"  {exc}")
            except Exception as exc:
                # A part can reject its own defaults, and the mesh libraries have their
                # own ideas about failure. Neither is worth a traceback.
                sys.exit(f"  {name}: {type(exc).__name__}: {exc}")
            for line in compare.report(name, file, metrics, unit, source):
                print(line)


def skill_targets():
    """The two paths nurb's install flow writes the skill to.

    skills.sh's universal directory and the Claude fallback. Shared with the dev
    server's staleness nudge so the two never check different paths.
    """
    home = pathlib.Path.home()
    return [
        home / ".agents" / "skills" / "nurb" / "SKILL.md",
        home / ".claude" / "skills" / "nurb" / "SKILL.md",
    ]


def cmd_skill(args):
    """Print the agent skill, for whatever harness the user's model lives in.

    Printed rather than installed, because every harness keeps its instructions
    somewhere else and those paths change faster than this tool should chase:
    redirect it to ~/.claude/skills/nurb/SKILL.md, a Cursor rule, or the end of an
    AGENTS.md. The file is a shim that points at `nurb rules`, so an installed copy
    does not go stale when the doctrine moves.

    `--sync` is the one exception to "printed rather than installed": the two paths
    nurb's own install flow creates (skills.sh's universal directory and the Claude
    fallback) get rewritten from the copy shipped in this package, so an installed
    skill matches the installed nurb rather than whatever version first wrote it.
    """
    skill = (pathlib.Path(__file__).parent / "skill.md").read_text(encoding="utf-8")
    if not args.sync:
        print(skill)
        return
    home = pathlib.Path.home()
    targets = skill_targets()
    seen = set()
    found = False
    for target in targets:
        if not target.is_file():
            continue
        # skills.sh symlinks each harness at its universal copy; one write is enough.
        real = target.resolve()
        if real in seen:
            continue
        seen.add(real)
        found = True
        state = "current"
        if real.read_text(encoding="utf-8") != skill:
            real.write_text(skill, encoding="utf-8")
            state = "updated"
        # as_posix so the ~/ prefix reads the same on Windows, where the
        # default separator would print ~/.agents\skills\nurb.
        print(f"  ~/{target.relative_to(home).as_posix()}: {state}")
    if not found:
        print("  no installed skill found. install one: npx skills add shpigford/nurb --skill nurb")


def cmd_update(args):
    """Upgrade nurb, then re-sync the installed skill so the two move together.

    The sync runs in a fresh process on purpose: the upgrade just replaced this
    package on disk, and it is the new install's skill that should land, not the
    one loaded into this interpreter.
    """
    import shutil
    import subprocess

    uv = shutil.which("uv")
    if uv:
        if subprocess.run([uv, "tool", "upgrade", "nurb"]).returncode != 0:
            # flush=True because the sync subprocess below shares this stdout, and
            # buffered parent lines would land after the child's.
            print("  uv could not upgrade nurb; if you installed with pip: pip install -U nurb", flush=True)
    else:
        print("  uv not found. upgrade nurb however you installed it, e.g. pip install -U nurb", flush=True)
    exe = shutil.which("nurb")
    if exe:
        subprocess.run([exe, "skill", "--sync"])
    else:
        cmd_skill(argparse.Namespace(sync=True))


def cmd_card(args):
    from . import builder, card, checks

    root = project_root()
    for path in _resolve(root, args.part):
        configs = _configs(path)
        if not configs:
            continue
        try:
            built = []
            for name, overrides, ctx in configs:
                shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
                built.append((name, shape, ctx, checks.run(shape, ctx)))
        except Exception as exc:
            print(f"  {path.stem}: {type(exc).__name__}: {exc}")
            continue
        _, shape, ctx, found = built[0]
        target, changed, thin = card.write(path, shape, ctx, found, variants=built[1:])
        state = "updated" if changed else "current"
        print(f"  {target.relative_to(root)}: {state}")
        for heading in thin:
            print(f"      empty section: {heading}")


def cmd_slice(args):
    """Hand the part to the slicer the user already has, and say what it predicts.

    The two numbers a slicer knows and nothing upstream of it does are how long the
    print takes and what it weighs, and both are design feedback while the design can
    still change. Everything else about slicing stays where it belongs.
    """
    from . import builder, checks, slicing

    root = project_root()
    out = root / "build"
    configs = _collect_exports(_resolve(root, args.part))
    # The command itself is the freshness boundary. Clear every expected G-code before
    # preflight too, so a missing slicer or printer cannot leave an older build current.
    for _, name, _, _ in configs:
        (out / f"{name}.gcode").unlink(missing_ok=True)
    worst = 0
    exe = slicing.app()
    if exe is None:
        looked = (
            "in Program Files or on PATH"
            if sys.platform == "win32"
            else "in /Applications, on PATH, or through Flatpak"
        )
        sys.exit(
            f"  no slicer found. `nurb slice` drives one you already have installed:\n"
            f"  {' or '.join(slicing.SLICERS)}, {looked}.\n"
            f"  `nurb export` writes the 3MF if you would rather open it yourself."
        )
    try:
        wanted, profile = checks.slicer_name(root, args.printer)
    except ValueError as exc:
        sys.exit(f"  {exc}")
    if not wanted:
        sys.exit(
            "  no printer chosen, and a slice is meaningless without one.\n"
            "  Name the machine once in printer.toml (`profile = \"bambu_a1_mini\"`),\n"
            f"  in ~/.config/nurb/config.toml for every project, or pass --printer.\n"
            f"  have: {', '.join(sorted(checks.profiles()))}"
        )
    vendors = slicing.vendors(exe)
    if vendors is None:
        sys.exit(
            f"  found {slicing.label(exe)} but not its profile bundle, "
            "so there is nothing to slice against"
        )

    # The ctx rides along because `tuned` reads it: the same warp and stability
    # thresholds that decide a brim in the exported 3MF decide it here, so the
    # prediction describes the file `nurb export` hands out rather than a stock slice.
    queue = list(configs)
    while queue:
        path, name, overrides, ctx = queue.pop(0)
        gcode_target = out / f"{name}.gcode"
        # Clear it before the build, profile lookup, or assembly branch: any of those
        # can fail or skip, and yesterday's printable file must not survive as current.
        gcode_target.unlink(missing_ok=True)
        shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
        scene = getattr(shape, "_nurb_scene", None)
        if scene is not None:
            # The same rule `nurb export` follows: a welded scene is not a thing to
            # print, so in a project sweep an assembly steps aside and its parts slice
            # as themselves, while naming one explicitly slices what it places rather
            # than exiting 0 having done nothing.
            if not args.part:
                print(f"  {name}: assembly, skipped (its parts slice as themselves)")
                continue
            placed = sorted(pathlib.Path(u) for u in scene.uses)
            if not placed:
                sys.exit(f"  {name} is an assembly that places no parts; nothing to slice")
            print(f"  {name}: slicing the {len(placed)} part(s) it places")
            queue = [(p, p.stem, None, checks.from_card(p)) for p in placed] + queue
            continue
        out.mkdir(exist_ok=True)
        model = out / f"{name}.stl"
        builder.write_stl(shape, model)
        settings, notes = slicing.tuned(shape, ctx)
        try:
            machine = slicing.machine(vendors, wanted, args.nozzle or slicing.NOZZLE)
            process, filament = slicing.profiles_for(machine, args.layer, args.filament)
            (seconds, grams), gcode = slicing.run(
                model, gcode_target, machine, process, filament, exe, plate=args.plate, settings=settings
            )
        except slicing.Unavailable as exc:
            print(f"  {name}: {exc}")
            worst = 1
            continue
        print(f"  {name}: {slicing.spoken(seconds)}, {slicing.weighed(grams)} of filament")
        print(f"      {profile} / {process.stem} / {filament.stem} / {args.plate} / {', '.join(notes)}")
        print(f"      {gcode.relative_to(root)}")
    if worst:
        sys.exit(worst)


def cmd_stress(args):
    from . import builder, stress

    root = project_root()

    def point(text, flag):
        try:
            v = tuple(float(x) for x in text.split(","))
            if len(v) != 3:
                raise ValueError
            return v
        except ValueError:
            sys.exit(f"{flag} takes x,y,z in mm, like --at 10,0,25")

    for path in _resolve(root, args.part):
        # A card's load coordinates describe only the source geometry. Variants can
        # move them onto unrelated faces, so variants auto-aim while retaining the
        # use case's weight and material.
        from . import checks

        try:
            card = checks.settings(path).get("stress") or {}
        except ValueError:
            card = {}
        for name, overrides, ctx in _configs(path):
            try:
                shape, _, _ = builder.build(path, overrides=overrides or None)
            except Exception as exc:
                print(f"  {name}: {type(exc).__name__}: {exc}")
                continue
            aimed = (
                card
                if not overrides
                else {key: card[key] for key in ("kg", "material") if key in card}
            )
            try:
                holds = (
                    [point(h, "--hold") for h in args.hold]
                    if args.hold
                    else [tuple(map(float, p)) for p in aimed.get("hold", [])] or None
                )
                load = (
                    point(args.at, "--at")
                    if args.at
                    else tuple(map(float, aimed["load"])) if "load" in aimed else None
                )
                guessed = holds is None or load is None
                if guessed:
                    d_holds, d_load = stress.default_spots(shape)
                    holds, load = holds or d_holds, load or d_load
                kg = args.kg if args.kg is not None else float(aimed.get("kg", 1.0))
                material = args.material or aimed.get("material", "PLA")
                out = stress.analyze(
                    shape,
                    holds,
                    load,
                    kg,
                    pitch=args.pitch,
                    material=material,
                    up=ctx.up,
                )
            except ValueError as exc:
                print(f"  {name}: {exc}")
                continue
            spot = lambda p: "(" + ", ".join(f"{v:.0f}" for v in p) + ")"
            held = ", ".join(spot(c) for c in out["hold_centers"])
            print(
                f"  {name}: {kg:g} kg on {out['material']} at "
                f"{spot(out['load_center'])}, held at {held}"
                + (
                    " (guessed; aim with --at/--hold x,y,z, or a [stress] block in the card)"
                    if guessed
                    else ""
                )
            )
            print(
                f"      peak {out['max_mpa']} MPa at {spot(out['hotspot'])}, "
                f"{out['across_mpa']} MPa pulling across layers, "
                f"sags {out['deflection_mm']} mm"
            )
            f, seam = out["factor"], out["gives"] == "layers"
            how = "splitting at the layer seams" if seam else "in the plastic itself"
            if f is None:
                print("      no stress to speak of")
            elif f < 1:
                print(f"      breaks under this, {how}: holds about {kg * f:.1f} kg")
            else:
                print(f"      holds ~{f}x this load; when it does break, it breaks {how}")


def cmd_diff(args):
    """What this part became, against what its card says it was.

    The question an edit leaves behind is whether it moved what you aimed at and
    nothing else, and neither the viewer nor the rules answer it: a chamfer that
    stopped landing takes four faces with it and leaves a part that still builds,
    still checks clean, and still looks right from wherever the camera was.
    """
    from . import builder, card, checks

    root = project_root()
    drifted = False
    for path in _resolve(root, args.part):
        was = card.recorded(path)
        if was is None:
            print(f"  {path.stem}: nothing recorded yet, run `nurb card`")
            continue
        configs = _configs(path)
        if not configs:
            continue
        try:
            built = []
            for name, overrides, ctx in configs:
                shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
                built.append((name, shape, ctx, checks.run(shape, ctx)))
        except Exception as exc:
            print(f"  {path.stem}: {type(exc).__name__}: {exc}")
            continue
        _, shape, ctx, found = built[0]
        changes = card.compare(was, card.facts(shape, ctx, found, variants=built[1:]))
        if not changes:
            print(f"  {path.stem}: unchanged since its card")
            continue
        drifted = True
        print(f"  {path.stem}: {len(changes)} change(s) since its card")
        for line in changes:
            print(f"      {line}")
    if drifted:
        print("  `nurb card` writes these back once they are the numbers you meant.")


def cmd_render(args):
    from . import builder, render

    root = project_root()
    try:
        written = render.render(
            root,
            _resolve(root, args.part),
            _renders(root),
            view=args.view,
            size=(args.width, args.height),
            chrome=args.chrome,
            cut=args.section,
        )
    except builder.BuildError as exc:
        sys.exit(f"  {exc}")
    for _, png in written:
        print(f"  {png.relative_to(root)}")


DEFAULT_PORT = 7373

# 3MF first: it carries units, and it is what Bambu Studio and Orca open natively.
# GLB is the viewer's format, so it is on request rather than written every time.
FORMATS = ("3mf", "stl", "step", "glb")
DEFAULT_FORMATS = ("3mf",)


def _is_free(port):
    import socket

    with socket.socket() as probe:
        if sys.platform == "win32":
            # Windows turns SO_REUSEADDR into permission to bind over a live
            # socket, so a probe using it reports every port as free.
            # SO_EXCLUSIVEADDRUSE restores the honest answer.
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _serving(port, root):
    """The URL of a nurb dev already serving `root` on `port`, or None.

    A taken port is two different situations: this project's own server, which is an
    answer to reuse, and any other process, which is a reason to keep walking. Asking
    the port's /api/sync for its project root tells them apart.
    """
    import json
    import urllib.request

    url = f"http://127.0.0.1:{port}"
    try:
        with urllib.request.urlopen(f"{url}/api/sync", timeout=0.5) as resp:
            payload = json.load(resp)
    except Exception:
        return None
    if payload.get("type") == "sync" and payload.get("root") == str(root):
        return url
    return None


def _pick_port(asked, root):
    """The port to serve on, checked before anything expensive happens.

    A project is any directory with a `parts/` folder, so working on two at once is
    the ordinary case rather than an advanced one, and it should not cost a flag. An
    unasked-for port walks up from the default until one is free.

    A port already serving this same project is not free and not skippable either:
    starting a second server there is how an agent that lost track of its background
    shell piles identical viewer tabs on the user (issue #102), so the answer is the
    running URL, not another instance.

    Asking explicitly means asking, so a port that is taken is an error rather than a
    suggestion: `--port 7373` picking 7374 would send you to a tab showing somebody
    else's parts.
    """
    if asked is not None:
        if _is_free(asked):
            return asked
        if url := _serving(asked, root):
            sys.exit(
                f"  nurb dev is already serving this project at {url}\n"
                f"  use that URL; a save reaches it without a restart"
            )
        sys.exit(
            f"  port {asked} is already in use, most likely by another nurb dev.\n"
            f"  leave --port off and one will be picked for you"
        )
    free = None
    for port in range(DEFAULT_PORT, DEFAULT_PORT + 40):
        if _is_free(port):
            if free is None:
                free = port
            continue
        if url := _serving(port, root):
            sys.exit(
                f"  nurb dev is already serving this project at {url}\n"
                f"  use that URL; a save reaches it without a restart"
            )
    if free is not None:
        return free
    # Forty viewers is unusual but not a reason to refuse to start (issue #55 hit
    # this wall): fall back to whatever the OS hands out, as headless renders do.
    import socket

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def cmd_dev(args):
    from .server import Server

    root = project_root()
    # Before the build, not after. Discovering the port is taken used to cost a full
    # rebuild of every part in the project first.
    port = _pick_port(args.port, root)
    server = Server(root, port=port, draft=args.draft, open_browser=args.open)
    print(f"  building {root.name}/parts")
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n  stopped")
    except OSError as exc:
        # A race: free when it was checked and taken by the time it was bound.
        if exc.errno != errno.EADDRINUSE:
            raise
        sys.exit(f"  port {port} was taken between checking it and binding it. Try again.")


LAUNCHER = "viewer.cmd" if sys.platform == "win32" else "viewer.command"


def _write_launcher(root):
    file = root / LAUNCHER
    if sys.platform == "win32":
        # cmd rather than PowerShell, because .ps1 double-clicks open an editor
        # under the default execution policy while .cmd just runs.
        file.write_text(
            "@echo off\n"
            'cd /d "%~dp0"\n'
            "nurb dev --open\n"
            "pause\n",
            encoding="utf-8",
            newline="\r\n",
        )
        return file
    # A login shell, because Finder's Terminal session does not carry the PATH a
    # profile adds, and the double-click would die on `command not found: nurb`.
    file.write_text(
        "#!/bin/zsh -l\n"
        'cd "$(dirname "$0")"\n'
        "exec nurb dev --open\n",
        encoding="utf-8",
    )
    file.chmod(0o755)
    return file


def cmd_launcher(args):
    _write_launcher(project_root())
    where = "Explorer" if sys.platform == "win32" else "Finder"
    print(f"  {LAUNCHER}: double-click in {where} to serve this project")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="nurb",
        description="agentic CAD for 3D printing",
        # The one line worth having here: an agent that meets this binary in a
        # traceback should learn where the rest of it is.
        epilog="start with `nurb rules`, which prints the design doctrine",
    )
    # The installed entry point handles a bare `nurb --version` before this
    # package loads. Keep the action here so help and programmatic calls agree.
    try:
        version = importlib.metadata.version("nurb")
    except importlib.metadata.PackageNotFoundError:
        version = "0.0.0"
    p.add_argument("--version", action="version", version=f"nurb {version}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="create a part")
    s.add_argument("name")
    s.add_argument("--root", help=argparse.SUPPRESS)
    s.add_argument(
        "--embed",
        action="store_true",
        help="seed AGENTS.md for an embedding app that owns the server and permissions",
    )
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("dev", help="watch parts and serve the viewer")
    s.add_argument("--port", type=int, help=f"default: the first free port from {DEFAULT_PORT}")
    s.add_argument("--draft", action="store_true", help="start with the polish pass off (faster)")
    s.add_argument("--open", action="store_true", help="open the viewer in a browser once serving")
    s.set_defaults(fn=cmd_dev)

    s = sub.add_parser("launcher", help=f"write {LAUNCHER}, a double-clickable `nurb dev`")
    s.set_defaults(fn=cmd_launcher)

    s = sub.add_parser("build", help="build parts once")
    s.add_argument("part", nargs="?")
    s.add_argument("--draft", action="store_true")
    s.set_defaults(fn=cmd_build)

    s = sub.add_parser("check", help="run the printability rules")
    s.add_argument("part", nargs="?")
    s.add_argument("--strict", action="store_true", help="exit non-zero on any finding")
    # Not argparse `choices`: reading them would parse the shipped profiles on every
    # `nurb --help`, and the error for an unknown name already lists what exists.
    s.add_argument("--printer", help="check against a shipped profile instead of printer.toml")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("rules", help="print the design doctrine")
    s.set_defaults(fn=cmd_rules)

    s = sub.add_parser("api", help="the vocabulary a part file gets, with signatures")
    s.set_defaults(fn=cmd_api)

    s = sub.add_parser("inspect", help="measure a built part: faces, normals, concave edges")
    s.add_argument("part", nargs="?")
    s.add_argument("--limit", type=int, default=12, help="how many faces and edges to list")
    s.add_argument(
        "--render",
        action="store_true",
        help="write build/renders/<part>.finding-<n>.png per finding, camera facing the face it fired on",
    )
    s.set_defaults(fn=cmd_inspect)

    s = sub.add_parser(
        "scan", help="measure a mesh in mm, a phone scan or a downloaded model (STL/OBJ/GLB or triangulated PLY)"
    )
    s.add_argument("file", help="the mesh: a scan app export, or a model downloaded to measure")
    s.add_argument(
        "--units",
        choices=("mm", "cm", "m", "in"),
        help="the file's units. default: declared by the format, otherwise guessed from size",
    )
    s.add_argument(
        "--section",
        metavar="AXIS[:POS]",
        help="slice a profile polyline: z is mid-mesh, z:0.7 a fraction of the span, z:40mm a coordinate in the mesh's own frame",
    )
    s.add_argument(
        "--tolerance", type=float, default=0.2,
        help="simplify the profile to this many mm (default 0.2)",
    )
    s.set_defaults(fn=cmd_scan)

    s = sub.add_parser(
        "compare", help="deviation from the part's target mesh, in both directions"
    )
    s.add_argument("part", nargs="?")
    s.add_argument(
        "--against",
        metavar="FILE",
        help="compare against this mesh instead of the card's declared target",
    )
    s.add_argument(
        "--units",
        choices=("mm", "cm", "m", "in"),
        help="the mesh file's units. default: the card's say, the format's, or a size guess",
    )
    s.set_defaults(fn=cmd_compare)

    s = sub.add_parser("skill", help="print an agent skill file for your AI harness")
    s.add_argument("--sync", action="store_true", help="rewrite installed copies from this package instead of printing")
    s.set_defaults(fn=cmd_skill)

    s = sub.add_parser("update", help="upgrade nurb and re-sync the installed skill")
    s.set_defaults(fn=cmd_update)

    s = sub.add_parser("verify", help="run the doctrine's verification list")
    s.add_argument("part", nargs="?")
    s.add_argument(
        "--report",
        action="store_true",
        help="write build/renders/<part>.verify.md, with renders of the part and each finding",
    )
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("extract", help="find duplication across parts")
    s.set_defaults(fn=cmd_extract)

    s = sub.add_parser("card", help="regenerate a part card's AUTO block")
    s.add_argument("part", nargs="?")
    s.set_defaults(fn=cmd_card)

    s = sub.add_parser("diff", help="what changed since the card was written")
    s.add_argument("part", nargs="?")
    s.set_defaults(fn=cmd_diff)

    s = sub.add_parser("slice", help="slice with the installed slicer: print time and filament")
    s.add_argument("part", nargs="?")
    s.add_argument("--printer", help="slice for a shipped profile instead of printer.toml")
    # Defaulted in the module rather than here, so `nurb --help` stays an import lighter.
    s.add_argument("--nozzle", help="nozzle size, in mm (default 0.4)")
    s.add_argument("--layer", default="0.20", help="layer height, in mm (default 0.20)")
    s.add_argument("--filament", default="PLA", help="filament to price the print in (default PLA)")
    s.add_argument("--plate", default="Textured PEI Plate", help="build plate (default Textured PEI Plate)")
    s.set_defaults(fn=cmd_slice)

    s = sub.add_parser("stress", help="static stress under a load: peak MPa, margin, hot spot")
    s.add_argument("part", nargs="?")
    s.add_argument("--kg", type=float, help="the weight pressing down (default: the card's, else 1)")
    s.add_argument("--at", help="x,y,z where the weight sits (default: the highest big upward face)")
    s.add_argument("--hold", action="append",
                   help="x,y,z of a spot that holds the part; repeat it for every mounting point "
                        "(default: its largest downward or side face)")
    s.add_argument("--pitch", type=float, help="voxel size in mm (default: sized from the part)")
    s.add_argument("--material", help="what it prints in: PLA, PETG, ABS, ASA, Nylon, PC (default: the card's, else PLA)")
    s.set_defaults(fn=cmd_stress)

    s = sub.add_parser("render", help="write a PNG of a part to build/renders/")
    s.add_argument("part", nargs="?")
    # Not argparse `choices`: reading them would mean importing the render module, and
    # every heavy import in this file is function-local so `nurb --help` stays instant.
    s.add_argument("--view", help="iso, front, back, left, right, top (default: iso, or facing the cut)")
    s.add_argument("--width", type=int, default=1200)
    s.add_argument("--height", type=int, default=900)
    s.add_argument("--chrome", action="store_true", help="keep the HUD and findings panel")
    s.add_argument(
        "--section",
        metavar="AXIS[:POS]",
        help="cut the part open: z is mid-part, z:0.7 a fraction of the span, z:4mm absolute (z measured from the bed)",
    )
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("export", help="write 3MF/STL/STEP/GLB to build/")
    s.add_argument("part", nargs="?")
    s.add_argument(
        "--formats", nargs="+", default=None,
        help=f"default: {' '.join(DEFAULT_FORMATS)}, or printer.toml's [export] formats. also: stl, step, glb",
    )
    s.set_defaults(fn=cmd_export)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
