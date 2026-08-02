"""Build untrusted candidate code and export only its resulting B-reps.

This process owns candidate imports. The scorer never imports a submitted part, so a
part cannot replace check functions or write a forged score to the scorer's stdout.
"""

import argparse
import json
import os
import pathlib
import shutil
import sys
import threading
import time

from build123d import export_brep

from nurb import builder


def _write_manifest(path, rows):
    path.write_text(json.dumps(rows), encoding="utf-8")


def _stage(part, measurements, root):
    """measured() resolves from the part file's directory, so a probe that rewrites
    measurements builds a copy of the candidate project carrying the probe's file.
    The whole project matters: parts can import root-level helpers and local modules."""
    part = pathlib.Path(part).resolve()
    source = part.parent.parent if part.parent.name == "parts" else part.parent
    shutil.copytree(source, root, dirs_exist_ok=True, symlinks=True)
    target = root / part.relative_to(source)
    (root / "measurements.toml").write_text(measurements, encoding="utf-8")
    return target


def _die_when_orphaned():
    """Exit as soon as the grading stack above is gone.

    This process runs in its own session so the scorer can kill it selectively, which
    also means nothing kills it automatically when the scorer dies first (an
    interrupted test run, the outer grade timeout racing the inner one). On a hanging
    part that leftover spins forever; a session was found carrying twenty of them."""
    parent = os.getppid()
    while True:
        now = os.getppid()
        if now == 1 or now != parent:
            os._exit(1)
        time.sleep(1.0)


def main():
    threading.Thread(target=_die_when_orphaned, daemon=True).start()
    ap = argparse.ArgumentParser(description="build isolated eval candidate shapes")
    ap.add_argument("part")
    ap.add_argument("request")
    ap.add_argument("out")
    args = ap.parse_args()

    requests = json.loads(pathlib.Path(args.request).read_text(encoding="utf-8"))
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "manifest.json"
    rows = []

    for index, request in enumerate(requests):
        try:
            path = args.part
            if request.get("measurements") is not None:
                path = str(_stage(args.part, request["measurements"], out / f"stage_{index}"))
            shape, _, build_ms = builder.build(path, overrides=request.get("params") or None)
            target = out / f"{index}.brep"
            if not export_brep(shape, target):
                raise RuntimeError("BREP export failed")
            rows.append({"error": None, "build_ms": round(build_ms, 1)})
        except BaseException as exc:
            rows.append({"error": f"{type(exc).__name__}: {exc}", "build_ms": None})
        _write_manifest(manifest, rows)

    # Straight out, running no exit hooks: candidate code has already run in this
    # process, and an atexit hook registered from a part file can rewrite the exported
    # B-reps after the last build (a verification pass scored exactly that at 1.0).
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
