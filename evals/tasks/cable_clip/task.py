"""The cable_clip task: a screw-down clip for a measured cable bundle.

Task modules own everything the scorer needs: the seeded instance (dims, instruction,
measurements file), the frozen check Context, the dimensional assertions, and the flex
probes. The scorer never reads the candidate's card or the fixture's printer.toml, so
nothing the model writes can change what it is graded against.

Every scored dimension is stated in the instruction, and nothing unstated is scored.
"""

import math
import pathlib
import random
import shutil
from dataclasses import dataclass

from build123d import Cylinder, GeomType, Pos, Vector

from nurb import checks

EPS = 1e-3
TOL = 0.05  # stated dimensions are exact; this absorbs kernel noise, not design slack

WALL = 2.4
BASE = 3.0
LENGTH = 12.0
TAB = 10.0
HOLE_R = 2.1

INSTRUCTION = """\
Design a screw-down cable clip and save it as parts/cable_clip.py.

It holds a cable bundle measured at {bundle} mm across; the measurement is on file as
bundle_diameter in measurements.toml.

Requirements, all in mm:
- An open-top channel runs the full part along Y (the cable lies along Y).
- Channel inner width exactly bundle_diameter + 0.4 = {channel}; channel depth exactly
  bundle_diameter = {depth}. Square corners: the channel floor stays one flat face the
  full channel width, with no fillets or chamfers inside the channel.
- Channel walls 2.4 thick. Base under the channel 3.0 thick. Part length along Y
  exactly 12.0.
- A flat mounting tab 10.0 long extends along X from the outside of one wall, 3.0
  thick and flush with the bottom, with a vertical 4.2 diameter through-hole centered
  in the tab.
- The part prints as it sits: flat bottom on the bed, one solid, overall bounding box
  {bbox_x} x 12.0 x {bbox_z}.
- No material beyond what the features above require; the grader checks total volume
  within 10% of nominal.
- Expose bundle_diameter as a float parameter and derive the geometry from it: the
  clip must rebuild correctly for nearby bundle sizes.
- nurb check must report zero findings. The grader runs the checks itself and
  ignores the card's [accepted] blocks, so fix findings in the geometry instead of
  accepting them.
"""

MEASUREMENTS = """\
[bundle_diameter]
value = {bundle}
unit = "mm"
how = "calipers across the taped cable bundle, 2026-08-01"
"""


@dataclass(frozen=True)
class Instance:
    seed: int
    dims: dict
    instruction: str
    measurements: str


def _dims(bundle):
    channel = round(bundle + 0.4, 2)
    return {
        "bundle": bundle,
        "channel": channel,
        "depth": bundle,
        "bbox_x": round(2 * WALL + channel + TAB, 2),
        "bbox_y": LENGTH,
        "bbox_z": round(BASE + bundle, 2),
    }


def instance(seed):
    bundle = 6.0 + 0.5 * random.Random(seed).randrange(13)
    dims = _dims(bundle)
    return Instance(
        seed=seed,
        dims=dims,
        instruction=INSTRUCTION.format(**dims),
        measurements=MEASUREMENTS.format(bundle=dims["bundle"]),
    )


def context():
    """The Context this task is graded under. Frozen here, never read from the
    candidate's card or printer.toml: a card's [accepted] block must not mute rules."""
    return checks.Context()


def _volume(dims):
    body = (2 * WALL + dims["channel"]) * LENGTH * (BASE + dims["depth"])
    cut = dims["channel"] * LENGTH * dims["depth"]
    tab = TAB * LENGTH * BASE
    hole = math.pi * HOLE_R**2 * BASE
    return body - cut + tab - hole


def misfits(shape, dims):
    """Everything wrong with the clip, as (problems, checks). Empty problems means
    every stated dimension is there. Translation-tolerant, rotation-pinned: spans and
    bed-relative heights, never absolute coordinates."""
    problems = []
    checks_run = 0
    bb = shape.bounding_box()

    for axis, want in (("X", dims["bbox_x"]), ("Y", dims["bbox_y"]), ("Z", dims["bbox_z"])):
        checks_run += 1
        got = getattr(bb.size, axis)
        if abs(got - want) > TOL:
            problems.append(f"bounding box {axis} is {got:.2f}mm, expected {want}")

    # The channel floor: a flat face at bed + BASE spanning the full channel width
    # and length. The length assertion is what rejects a channel blocked at one end.
    # Interior in X, which is what tells it apart from the tab's top face (the tab
    # always reaches the bounding box edge; at bundle 9.6 their spans are both 10.0).
    checks_run += 1
    floor_z = bb.min.Z + BASE
    floor_candidates = []
    floors = []
    for face in shape.faces():
        box = face.bounding_box()
        if abs(box.min.Z - floor_z) < EPS and abs(box.max.Z - floor_z) < EPS:
            interior = box.min.X > bb.min.X + 0.5 and box.max.X < bb.max.X - 0.5
            if interior and abs(box.size.X - dims["channel"]) < TOL:
                floor_candidates.append(face)
                if abs(box.size.Y - LENGTH) < TOL:
                    floors.append(face)
    if not floors:
        problems.append(
            f"no channel floor: need a {dims['channel']} x {LENGTH}mm flat face "
            f"at {BASE}mm above the bed"
        )

    # Wall thickness, probed at mid-channel height where a broken outside edge cannot
    # reach: material just inside each wall's outer plane, air just beyond it. Face
    # spans would re-measure the chamfer, not the wall, and every stated dimension
    # here survives the doctrine's polish pass.
    checks_run += 1
    y_mid = (bb.min.Y + bb.max.Y) / 2
    if floor_candidates:
        floor_box = floor_candidates[0].bounding_box()
        z_mid = floor_z + dims["depth"] / 2
        walls_ok = all(
            shape.is_inside(Vector(inside, y, z_mid))
            and not shape.is_inside(Vector(outside, y_mid, z_mid))
            for inside, outside in (
                (floor_box.min.X - WALL + 0.1, floor_box.min.X - WALL - 0.1),
                (floor_box.max.X + WALL - 0.1, floor_box.max.X + WALL + 0.1),
            )
            for y in (bb.min.Y + 1.5, y_mid, bb.max.Y - 1.5)
        )
        # Both walls reach full channel depth: probed on the channel side just below
        # the top, where neither the tab nor an outer chamfer can reach. Without this
        # a wall lopped to half height hides inside the volume band while the other
        # wall satisfies the bounding box (a verification pass scored exactly that
        # cheat 1.0).
        z_top = floor_z + dims["depth"] - 0.5
        tall = all(
            shape.is_inside(Vector(x, y_mid, z_top))
            for x in (floor_box.min.X - 0.1, floor_box.max.X + 0.1)
        )
        if not walls_ok or not tall:
            problems.append(f"channel walls are not both {WALL}mm thick and {dims['depth']}mm tall")

    # The tab: TAB long from the outside of a wall to the bounding-box edge, BASE
    # thick, flush with the bed, running the full length. Probed inside its perimeter
    # (clear of edge breaks and of the screw hole), with the air probe above proving
    # the thickness. The matched span's center is the required screw-hole center.
    checks_run += 1
    if floor_candidates:
        floor_box = floor_candidates[0].bounding_box()
        spans = [
            (bb.min.X, floor_box.min.X - WALL),
            (floor_box.max.X + WALL, bb.max.X),
        ]
    else:
        spans = [(bb.min.X, bb.min.X + TAB), (bb.max.X - TAB, bb.max.X)]
    tab_span = None
    for lo, hi in spans:
        if abs((hi - lo) - TAB) > TOL:
            continue
        xs = (lo + 1.5, hi - 1.5)
        ys = (bb.min.Y + 1.5, bb.max.Y - 1.5)
        solid = all(
            shape.is_inside(Vector(x, y, bb.min.Z + z))
            for x in xs
            for y in ys
            for z in (0.1, BASE - 0.1)
        )
        air_above = not any(
            shape.is_inside(Vector(x, y, bb.min.Z + BASE + 0.1)) for x in xs for y in ys
        )
        if solid and air_above:
            tab_span = (lo, hi)
            break
    if tab_span is None:
        problems.append(f"no {TAB} x {LENGTH}mm mounting tab, {BASE}mm thick and flush with the bed")

    # A through-hole needs paired rims on the tab's center plus empty space through
    # its thickness. Unrelated circles and blind pockets do not count.
    checks_run += 1
    circles = [
        edge
        for edge in shape.edges()
        if edge.geom_type == GeomType.CIRCLE and abs(edge.radius - HOLE_R) < TOL
    ]
    hole_ok = False
    if tab_span is not None:
        center_x = (tab_span[0] + tab_span[1]) / 2
        centered = [
            edge
            for edge in circles
            if abs(edge.arc_center.X - center_x) < TOL
            and abs(edge.arc_center.Y - y_mid) < TOL
        ]
        bottom = any(abs(edge.arc_center.Z - bb.min.Z) < TOL for edge in centered)
        top = any(abs(edge.arc_center.Z - (bb.min.Z + BASE)) < TOL for edge in centered)
        clearance = (
            Pos(center_x, y_mid, bb.min.Z + BASE / 2)
            * Cylinder(HOLE_R - TOL, BASE + 0.2)
        )
        try:
            blocked = shape & clearance
            clear = (blocked.volume if blocked is not None else 0.0) < 0.01
        except Exception:
            clear = False
        hole_ok = bottom and top and clear
    if not hole_ok:
        problems.append(
            f"no centered {2 * HOLE_R}mm through-hole through the full mounting tab"
        )

    # Open at the top: nothing hangs over the channel opening. Without this a closed
    # tunnel scores perfectly (floor present, bbox right, a 1mm roof hides inside the
    # volume band), and a cable can never be laid into a tunnel. A face roofs the
    # channel when it tilts downward and overlaps a floor face from above; the 1mm
    # overlap margin keeps a neighbouring feature that merely touches the channel's
    # edge, like overhang.py's ledge, out of this check's verdict.
    checks_run += 1
    for floor in floor_candidates:
        fbox = floor.bounding_box()
        for face in shape.faces():
            box = face.bounding_box()
            if box.min.Z <= floor_z + EPS:
                continue
            if face.normal_at(face.center()).Z >= -0.5:
                continue
            over_x = min(box.max.X, fbox.max.X) - max(box.min.X, fbox.min.X)
            over_y = min(box.max.Y, fbox.max.Y) - max(box.min.Y, fbox.min.Y)
            if over_x > 1.0 and over_y > 1.0:
                problems.append("the channel is roofed over: it must stay open at the top")
                break
        else:
            continue
        break

    checks_run += 1
    want = _volume(dims)
    if abs(shape.volume - want) > 0.10 * want:
        problems.append(f"volume {shape.volume:.0f}mm3 is off nominal {want:.0f}mm3 by >10%")

    return problems, checks_run


def flex_probes(inst):
    """Parameter overrides and matching ground truth for the isolated build worker."""
    out = []
    for grow in (1.0, 2.0):
        bundle = round(inst.dims["bundle"] + grow, 2)
        out.append(({"params": {"bundle_diameter": bundle}}, _dims(bundle)))
    return out


def materialize(seed, dest):
    """Write the project a model starts from: fixture, the seeded measurement, and the
    same AGENTS.md a real project gets from `nurb new`, so the model designs with the
    shipped skill in front of it exactly the way a user's session would."""
    import importlib.resources

    dest = pathlib.Path(dest)
    fixture = pathlib.Path(__file__).parent / "fixture"
    shutil.copytree(fixture, dest, dirs_exist_ok=True)
    (dest / "measurements.toml").write_text(instance(seed).measurements, encoding="utf-8")
    skill = importlib.resources.files("nurb").joinpath("agents.md").read_text(encoding="utf-8")
    (dest / "AGENTS.md").write_text(skill, encoding="utf-8")
    return dest
