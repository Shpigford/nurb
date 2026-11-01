"""Headless PNG of a part, so an agent can see its own work.

No browser and no server. The stills come out of the same numpy rasterizer that draws
build results in the tool loop, so what a still shows and what the agent already sees
mid-loop are the same picture, made the same way. That removes the optional browser
download, the private port, and the wait for a page to paint.

The rasterizer draws geometry and nothing else, so a finding still carries its evidence
by where the camera stands rather than by a pin painted on the guilty face.
"""

import math
import pathlib
import re

from . import raster
from .builder import BuildError

VIEWS = tuple(raster.VIEWS)

# The grammar for a section cut: an axis, optionally with a position in millimetres.
# Checked here so a typo is an error naming the grammar instead of a PNG of an uncut
# part. The trailing `mm` is optional because the number is always millimetres.
CUT = re.compile(r"^[xyz](:-?\d*\.?\d+(mm)?)?$")


def _view(view):
    """A named view, or an `x,y,z` direction a caller computed from the geometry."""
    if view in raster.VIEWS:
        return view
    try:
        parts = [float(p) for p in str(view).split(",")]
    except ValueError:
        parts = []
    if len(parts) == 3 and any(parts) and all(math.isfinite(p) for p in parts):
        return tuple(parts)
    raise BuildError(f"no view called {view!r}. have: {', '.join(VIEWS)}")


def _cut(cut):
    """`z` (mid-part) or `z:4mm` (an absolute coordinate), as the rasterizer wants it."""
    if not cut:
        return None
    if not CUT.match(cut):
        raise BuildError(f"no cut like {cut!r}. want axis[:position]: z, z:4, or z:4mm")
    axis, _, position = cut.partition(":")
    return (axis, float(position.removesuffix("mm")) if position else None)


def _up(root, path):
    """The part's print direction, which is how the viewer stands it up too.

    A bad card is reported by the check pass and must not cost the picture, so a card
    that will not read leaves the part standing on the model's own z.
    """
    from . import checks

    try:
        return checks.from_card(path, base=checks.printer(root)).up
    except Exception:
        return (0.0, 0.0, 1.0)


def snapshots(root, shots, timeout=None):
    """Write one PNG per shot. Returns the written paths, in shot order.

    A shot is a dict: `part` (the file) and `file` (the target PNG), plus optional
    `view` (a name or an `x,y,z` direction), `size`, `overrides` (parameter values, so
    a variant can sit for its own picture), and `cut` (a section, in CUT's grammar).

    `check` and `marks` are read and ignored: the rasterizer paints no findings, so a
    finding still is aimed at the face by its caller's `view` and carries no pin.
    `timeout` is ignored too, and kept so callers that pass one still work: nothing
    here waits on anything.
    """
    for shot in shots:  # every typo before the first build, which is the expensive part
        _view(shot.get("view", "iso"))
        _cut(shot.get("cut"))

    from . import builder

    glbs = {}  # (name, overrides) -> the GLB, so a run of shots of one part builds once
    written = []
    for shot in shots:
        path = pathlib.Path(shot["part"])
        name = path.stem
        overrides = shot.get("overrides") or None
        key = (name, tuple(sorted(overrides.items())) if overrides else None)
        if key not in glbs:
            try:
                shape, _, _ = builder.build(path, overrides=overrides)
                glbs[key] = builder.to_glb(shape, up=_up(root, path))
            except Exception as exc:
                raise BuildError(f"{name}: {exc}") from exc

        width, height = shot.get("size") or (1200, 900)
        try:
            png = raster.render(
                glbs[key],
                width=width,
                height=height,
                view=_view(shot.get("view", "iso")),
                cut=_cut(shot.get("cut")),
            )
        except raster.Unrenderable as exc:
            raise BuildError(f"{name}: {exc}") from exc

        target = pathlib.Path(shot["file"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(png)
        written.append(target)
    return written


def render(root, paths, out_dir, view=None, size=(1200, 900), timeout=None, cut=None):
    """Write a PNG per part. Returns [(part_path, png_path)].

    A section render and a non-iso view each get their own filename, so cutting a part
    open or looking at it from the top never overwrites the picture of it whole. A
    named view is its own suffix; an x,y,z direction is `.view`. No view gymnastics for
    a cut: the camera looks into the cross-section, so any view arrives facing it.
    """
    if view is None:
        view = "iso"
    out_dir = pathlib.Path(out_dir)
    suffix = "" if view == "iso" else ("." + view if view in VIEWS else ".view")
    if cut:
        suffix += ".section"
    shots = [
        {
            "part": path,
            "file": out_dir / f"{pathlib.Path(path).stem}{suffix}.png",
            "view": view,
            "size": size,
            "cut": cut,
        }
        for path in paths
    ]
    return list(zip(paths, snapshots(root, shots, timeout=timeout)))
