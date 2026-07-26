"""nurb command line."""

import argparse
import asyncio
import pathlib
import sys

PART_TEMPLATE = '''from nurb import *


@part
def {name}(width=40, depth=30, height=20, wall=2, draft=False):
    body = Box(width, depth, height)
    if not draft:
        body = chamfer(body.edges().filter_by(Axis.Z), length=1)
    return body
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
    print(f"  {py.relative_to(root)}\n  {md.relative_to(root)}")


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


def cmd_build(args):
    from . import builder

    root = project_root()
    for path in _resolve(root, args.part):
        try:
            shape, params, ms = builder.build(path, draft=args.draft)
            info = builder.stats(shape)
            bbox = " x ".join(str(v) for v in info["bbox"])
            print(f"  {path.stem}: {bbox} mm  {ms:.0f}ms")
        except Exception as exc:
            print(f"  {path.stem}: {type(exc).__name__}: {exc}")


def cmd_check(args):
    from . import builder, checks

    root = project_root()
    worst = 0
    for path in _resolve(root, args.part):
        try:
            shape, _, _ = builder.build(path, draft=False)
            found = checks.run(shape, checks.from_card(path))
        except Exception as exc:
            print(f"  {path.stem}: {type(exc).__name__}: {exc}")
            worst = 2
            continue
        if not found:
            print(f"  {path.stem}: clean")
            continue
        fails = sum(1 for f in found if f.severity == checks.FAIL)
        print(f"  {path.stem}: {len(found)} finding(s), {fails} to fix")
        for finding in found:
            print(f"      {finding}")
        worst = max(worst, 2 if fails else 1)
    if args.strict and worst:
        sys.exit(1)


def cmd_export(args):
    from build123d import export_step, export_stl

    from . import builder

    root = project_root()
    out = root / "build"
    out.mkdir(exist_ok=True)
    for path in _resolve(root, args.part):
        shape, _, _ = builder.build(path, draft=False)
        for fmt in args.formats:
            target = out / f"{path.stem}.{fmt}"
            if fmt == "stl":
                export_stl(shape, str(target))
            elif fmt == "step":
                export_step(shape, str(target))
            elif fmt == "glb":
                target.write_bytes(builder.to_glb(shape, 0.02))
            print(f"  {target.relative_to(root)}")


def cmd_rules(args):
    # Explicit utf-8: the doctrine says mm², so the locale default breaks it on a machine
    # that is not utf-8, and `nurb rules` is the first command an agent runs.
    doctrine = pathlib.Path(__file__).parent / "doctrine.md"
    print(doctrine.read_text(encoding="utf-8"))


def cmd_card(args):
    from . import builder, card, checks

    root = project_root()
    for path in _resolve(root, args.part):
        try:
            shape, _, _ = builder.build(path, draft=False)
            ctx = checks.from_card(path)
            found = checks.run(shape, ctx)
        except Exception as exc:
            print(f"  {path.stem}: {type(exc).__name__}: {exc}")
            continue
        target, changed, thin = card.write(path, shape, ctx, found)
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


def cmd_dev(args):
    from .server import Server

    root = project_root()
    server = Server(root, port=args.port, draft=not args.polish)
    print(f"  building {root.name}/parts")
    server.rebuild_all()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n  stopped")


def main(argv=None):
    p = argparse.ArgumentParser(prog="nurb", description="agentic CAD for 3D printing")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="create a part")
    s.add_argument("name")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("dev", help="watch parts and serve the viewer")
    s.add_argument("--port", type=int, default=7373)
    s.add_argument("--polish", action="store_true", help="build full quality (slower)")
    s.set_defaults(fn=cmd_dev)

    s = sub.add_parser("build", help="build parts once")
    s.add_argument("part", nargs="?")
    s.add_argument("--draft", action="store_true")
    s.set_defaults(fn=cmd_build)

    s = sub.add_parser("check", help="run the printability rules")
    s.add_argument("part", nargs="?")
    s.add_argument("--strict", action="store_true", help="exit non-zero on any finding")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("rules", help="print the design doctrine")
    s.set_defaults(fn=cmd_rules)

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
    s.add_argument("--formats", nargs="+", default=["stl", "step"])
    s.set_defaults(fn=cmd_export)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
