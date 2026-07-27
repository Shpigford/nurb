"""nurb command line."""

import argparse
import asyncio
import errno
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


# Harness files an agent reads without being told to. The first one that already
# exists is left alone and gets a nudge instead, since it is the user's file.
HARNESS = ("AGENTS.md", "CLAUDE.md")


def _seed_agents(root):
    """Put a pointer to `nurb rules` where an agent will find it on day one.

    Everything an agent needs is already reachable: `nurb --help` lists the commands and
    `nurb rules` prints the doctrine. What was missing is any reason to type `nurb` at
    all. A fresh project is two files that look like an ordinary build123d script, so an
    agent reads them as one, writes generic geometry, and never learns the tool exists.

    This is not an init step. It is the command you were already running, it is skipped
    when the project has a harness file of its own, and `nurb new` prints everything it
    writes either way.
    """
    from . import __file__ as pkg

    shim = (pathlib.Path(pkg).parent / "agents.md").read_text(encoding="utf-8")
    for name in HARNESS:
        here = root / name
        if not here.is_file():
            continue
        # The one this command wrote on a previous run is not news.
        if here.read_text(encoding="utf-8") == shim:
            return None, None
        return None, name
    target = root / HARNESS[0]
    target.write_text(shim, encoding="utf-8")
    return target, None


def cmd_new(args):
    root = project_root()
    parts = root / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    name = args.name.replace("-", "_")
    py, md = parts / f"{name}.py", parts / f"{name}.md"
    if py.exists():
        sys.exit(f"{py} already exists")
    py.write_text(PART_TEMPLATE.format(name=name))
    md.write_text(CARD_TEMPLATE.format(name=name))
    written = [py, md]
    seeded, already = _seed_agents(root)
    if seeded:
        written.append(seeded)
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
    from . import builder

    root = project_root()
    for path in _resolve(root, args.part):
        for name, overrides, _ in _configs(path):
            try:
                shape, _, ms = builder.build(path, overrides=overrides or None, draft=args.draft)
                info = builder.stats(shape)
                bbox = " x ".join(str(v) for v in info["bbox"])
                print(f"  {name}: {bbox} mm  {ms:.0f}ms")
            except Exception as exc:
                print(f"  {name}: {type(exc).__name__}: {exc}")


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
            print(f"  {name}: {len(found)} finding(s), {fails} to fix")
            for finding in found:
                print(f"      {finding}")
            worst = max(worst, 2 if fails else 1)
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


def cmd_export(args):
    from build123d import export_step, export_stl

    from . import builder

    root = project_root()
    configs = _collect_exports(_resolve(root, args.part))
    out = root / "build"
    out.mkdir(exist_ok=True)
    for path, name, overrides, _ in configs:
        shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
        for fmt in args.formats:
            target = out / f"{name}.{fmt}"
            if fmt == "stl":
                export_stl(shape, str(target))
            elif fmt == "step":
                export_step(shape, str(target))
            elif fmt == "glb":
                target.write_bytes(builder.to_glb(shape, 0.02))
            else:
                # The print used to sit outside this chain, so a typo in `--formats`
                # reported a filename that was never written and exited 0.
                sys.exit(f"  no exporter for {fmt!r}. have: {', '.join(FORMATS)}")
            print(f"  {target.relative_to(root)}")


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
    from . import builder

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
            except ValueError as exc:
                if any(k in str(exc) for k in KERNEL):
                    problems.append(f"{name}={grown} fails in the kernel: {exc}")
                continue  # a guard in the part's own words is a decision, not a fault
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
            if len(shape.solids()) != 1:
                problems.append(f"{name} is {len(shape.solids())} solids, not one")
            found = checks.run(shape, ctx)
            for finding in found:
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
    print("  Not covered: fit faces by coordinate, and looking at a render.")
    if worst:
        sys.exit(1)


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


def cmd_render(args):
    from . import builder, render

    root = project_root()
    try:
        written = render.render(
            root,
            _resolve(root, args.part),
            root / "build",
            view=args.view,
            size=(args.width, args.height),
            chrome=args.chrome,
        )
    except builder.BuildError as exc:
        sys.exit(f"  {exc}")
    for _, png in written:
        print(f"  {png.relative_to(root)}")


DEFAULT_PORT = 7373

# GLB is the viewer's format, so it is on request rather than written every time.
FORMATS = ("stl", "step", "glb")
DEFAULT_FORMATS = ("stl", "step")


def _is_free(port):
    import socket

    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _pick_port(asked):
    """The port to serve on, checked before anything expensive happens.

    A project is any directory with a `parts/` folder, so working on two at once is
    the ordinary case rather than an advanced one, and it should not cost a flag. An
    unasked-for port walks up from the default until one is free.

    Asking explicitly means asking, so a port that is taken is an error rather than a
    suggestion: `--port 7373` picking 7374 would send you to a tab showing somebody
    else's parts.
    """
    if asked is not None:
        if _is_free(asked):
            return asked
        sys.exit(
            f"  port {asked} is already in use, most likely by another nurb dev.\n"
            f"  leave --port off and one will be picked for you"
        )
    for port in range(DEFAULT_PORT, DEFAULT_PORT + 40):
        if _is_free(port):
            return port
    sys.exit(f"  nothing free between {DEFAULT_PORT} and {DEFAULT_PORT + 40}")


def cmd_dev(args):
    from .server import Server

    root = project_root()
    # Before the build, not after. Discovering the port is taken used to cost a full
    # rebuild of every part in the project first.
    port = _pick_port(args.port)
    server = Server(root, port=port, draft=not args.polish)
    print(f"  building {root.name}/parts")
    server.rebuild_all()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n  stopped")
    except OSError as exc:
        # A race: free when it was checked and taken by the time it was bound.
        if exc.errno != errno.EADDRINUSE:
            raise
        sys.exit(f"  port {port} was taken between checking it and binding it. Try again.")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="nurb",
        description="agentic CAD for 3D printing",
        # The one line worth having here: an agent that meets this binary in a
        # traceback should learn where the rest of it is.
        epilog="start with `nurb rules`, which prints the design doctrine",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="create a part")
    s.add_argument("name")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("dev", help="watch parts and serve the viewer")
    s.add_argument("--port", type=int, help=f"default: the first free port from {DEFAULT_PORT}")
    s.add_argument("--polish", action="store_true", help="build full quality (slower)")
    s.set_defaults(fn=cmd_dev)

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

    s = sub.add_parser("verify", help="run the doctrine's verification list")
    s.add_argument("part", nargs="?")
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("extract", help="find duplication across parts")
    s.set_defaults(fn=cmd_extract)

    s = sub.add_parser("card", help="regenerate a part card's AUTO block")
    s.add_argument("part", nargs="?")
    s.set_defaults(fn=cmd_card)

    s = sub.add_parser("render", help="write a PNG of a part to build/")
    s.add_argument("part", nargs="?")
    # Not argparse `choices`: reading them would mean importing the render module, and
    # every heavy import in this file is function-local so `nurb --help` stays instant.
    s.add_argument("--view", default="iso", help="iso, front, back, left, right, top")
    s.add_argument("--width", type=int, default=1200)
    s.add_argument("--height", type=int, default=900)
    s.add_argument("--chrome", action="store_true", help="keep the HUD and findings panel")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("export", help="write STL/STEP/GLB to build/")
    s.add_argument("part", nargs="?")
    s.add_argument(
        "--formats", nargs="+", default=list(DEFAULT_FORMATS),
        help=f"default: {' '.join(DEFAULT_FORMATS)}. also: glb",
    )
    s.set_defaults(fn=cmd_export)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
