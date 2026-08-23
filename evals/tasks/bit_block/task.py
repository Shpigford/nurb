"""The bit_block task: a bench block for driver bits, dense with chamfers.

A spec task like cable_clip, but aimed at the two abilities the first corpus never
touched. First, chamfer execution: every pocket mouth and the top perimeter get an
exact 0.8 lead-in, with 2.0 webs between pockets, so the part sits close to OCCT's
adjacent-chamfer limit and an agent that chamfers in the wrong order, or against
selectors resolved before the pockets were cut, does not build at all. Second, count
parametrization: the pocket grid is driven by an int parameter, and the flex probes
regenerate the grid at other counts, which catches a grid written out by hand.

Every scored dimension is stated in the instruction, and nothing unstated is graded.
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

ROWS = 2
WEB = 2.0  # material between pocket walls, and from outer pockets to the block's side
DEPTH = 12.0
FLOOR = 3.0
CHAM = 0.8
CLEAR = 0.3

INSTRUCTION = """\
Design a bench block that holds driver bits upright, and save it as
parts/bit_block.py.

The bits' shanks are measured at {shank} mm across; the measurement is on file as
shank_diameter in measurements.toml. Bits drop straight down into round pockets and
stand there; the block sits flat on the bench.

Requirements, all in mm:
- A grid of {count} round pockets, {cols} columns by 2 rows, opening straight up.
  Pocket diameter exactly shank_diameter + 0.3 = {pocket_d}, pocket depth exactly
  12.0, flat floors, nothing intruding into any pocket and nothing roofing them over.
- Grid pitch exactly {pitch} in both directions (2.0 of material between neighbouring
  pocket walls), and 2.0 of material from the outermost pocket walls to the block's
  sides, so the block is exactly {bbox_x} x {bbox_y}.
- The floor under the pockets is solid, exactly 3.0 thick: overall height exactly
  15.0.
- Every pocket mouth gets an exact 0.8 x 45 degree chamfer lead-in. The top outer
  perimeter gets the same 0.8 chamfer. No other edges are broken: the bottom
  perimeter stays sharp so the stated bounding box is exact.
- The part prints as it sits: flat bottom on the bed, one solid.
- No material beyond what the features above require; the grader checks total volume
  within 10% of nominal.
- Expose shank_diameter as a float parameter and columns as an int parameter
  (default {cols}), and derive the geometry from both: the block must rebuild
  correctly for nearby shank sizes and other column counts.
- nurb check must report zero findings. The grader runs the checks itself and
  ignores the card's [accepted] blocks, so fix findings in the geometry instead of
  accepting them.
"""

MEASUREMENTS = """\
[shank_diameter]
value = {shank}
unit = "mm"
how = "calipers across a bit shank, 2026-08-20"
"""


@dataclass(frozen=True)
class Instance:
    seed: int
    dims: dict
    instruction: str
    measurements: str


def _dims(shank, cols):
    pocket_d = round(shank + CLEAR, 2)
    pitch = round(pocket_d + WEB, 2)
    return {
        "shank": shank,
        "pocket_d": pocket_d,
        "cols": cols,
        "count": cols * ROWS,
        "pitch": pitch,
        "bbox_x": round(cols * pitch + WEB, 2),
        "bbox_y": round(ROWS * pitch + WEB, 2),
        "bbox_z": round(FLOOR + DEPTH, 2),
    }


def instance(seed):
    rng = random.Random(seed)
    shank = 4.0 + 0.25 * rng.randrange(17)
    cols = 4 + rng.randrange(3)
    dims = _dims(shank, cols)
    return Instance(
        seed=seed,
        dims=dims,
        instruction=INSTRUCTION.format(**dims),
        measurements=MEASUREMENTS.format(shank=dims["shank"]),
    )


def context():
    """The Context this task is graded under. Frozen here, never read from the
    candidate's card or printer.toml: a card's [accepted] block must not mute rules."""
    return checks.Context()


def _volume(dims):
    r = dims["pocket_d"] / 2
    n = dims["count"]
    block = dims["bbox_x"] * dims["bbox_y"] * dims["bbox_z"]
    pockets = n * math.pi * r**2 * DEPTH
    # The mouth chamfer ring, beyond the cylinder already subtracted.
    rings = n * math.pi * CHAM**2 * (r + CHAM / 3)
    # The perimeter chamfer prism, corners counted once.
    perimeter = CHAM**2 / 2 * 2 * (dims["bbox_x"] + dims["bbox_y"]) - 4 * CHAM**3 / 3
    return block - pockets - rings - perimeter


def _grid_centers(dims, bb):
    """Where the stated grid puts each pocket axis, from the bounding box alone."""
    r = dims["pocket_d"] / 2
    return [
        (
            bb.min.X + WEB + r + col * dims["pitch"],
            bb.min.Y + WEB + r + row * dims["pitch"],
        )
        for col in range(dims["cols"])
        for row in range(ROWS)
    ]


def misfits(shape, dims):
    """Everything wrong with the block, as (problems, checks). Translation-tolerant,
    rotation-pinned: the grid is derived from the bounding box, which the stated
    borders pin to the pockets, so every per-pocket check is against stated geometry
    rather than whatever centers the candidate chose."""
    problems = []
    checks_run = 0
    bb = shape.bounding_box()
    r = dims["pocket_d"] / 2

    for axis, want in (("X", dims["bbox_x"]), ("Y", dims["bbox_y"]), ("Z", dims["bbox_z"])):
        checks_run += 1
        got = getattr(bb.size, axis)
        if abs(got - want) > TOL:
            problems.append(f"bounding box {axis} is {got:.2f}mm, expected {want}")

    centers = _grid_centers(dims, bb)

    # The bottom: one flat rectangular face spanning the full footprint. This is what
    # keeps the bottom perimeter sharp; a bottom chamfer or feet shrink it.
    checks_run += 1
    bottom = [
        face
        for face in shape.faces()
        if abs(face.bounding_box().min.Z - bb.min.Z) < EPS
        and abs(face.bounding_box().max.Z - bb.min.Z) < EPS
    ]
    footprint = bb.size.X * bb.size.Y
    full = (
        len(bottom) == 1
        and abs(bottom[0].bounding_box().size.X - bb.size.X) < TOL
        and abs(bottom[0].bounding_box().size.Y - bb.size.Y) < TOL
        and abs(bottom[0].area - footprint) < 0.1
    )
    if not full:
        problems.append("the bottom is not one flat face spanning the full footprint")

    # Pocket floors: a circle rim of the pocket radius at floor height on every grid
    # center. The rim, not a face probe, is what pins the diameter exactly.
    checks_run += 1
    floor_z = bb.max.Z - DEPTH
    floor_rims = [
        edge
        for edge in shape.edges()
        if edge.geom_type == GeomType.CIRCLE
        and abs(edge.radius - r) < TOL
        and abs(edge.arc_center.Z - floor_z) < TOL
    ]
    placed = _matched(centers, floor_rims)
    if placed < len(centers):
        problems.append(
            f"only {placed} of {len(centers)} pockets have a {dims['pocket_d']}mm "
            f"floor rim at {DEPTH}mm depth on the stated grid"
        )

    # The mouth chamfer, pinned from both ends: the pocket radius where the chamfer
    # lands (0.8 below the top) and the widened rim at the top. Together they state
    # 0.8 x 45 exactly.
    checks_run += 1
    lands = [
        e
        for e in shape.edges()
        if e.geom_type == GeomType.CIRCLE
        and abs(e.radius - r) < TOL
        and abs(e.arc_center.Z - (bb.max.Z - CHAM)) < TOL
    ]
    mouths = [
        e
        for e in shape.edges()
        if e.geom_type == GeomType.CIRCLE
        and abs(e.radius - (r + CHAM)) < TOL
        and abs(e.arc_center.Z - bb.max.Z) < TOL
    ]
    chamfered = min(_matched(centers, lands), _matched(centers, mouths))
    if chamfered < len(centers):
        problems.append(
            f"only {chamfered} of {len(centers)} pocket mouths have the exact "
            f"{CHAM} x 45 degree lead-in chamfer"
        )

    # The perimeter chamfer: the top face shrinks by 0.8 on every side, and 45 degree
    # planar faces connect it to the sides.
    checks_run += 1
    top = [
        face
        for face in shape.faces()
        if abs(face.bounding_box().min.Z - bb.max.Z) < EPS
        and abs(face.bounding_box().max.Z - bb.max.Z) < EPS
    ]
    shrunk = any(
        abs(f.bounding_box().size.X - (bb.size.X - 2 * CHAM)) < TOL
        and abs(f.bounding_box().size.Y - (bb.size.Y - 2 * CHAM)) < TOL
        for f in top
    )
    bevels = [
        face
        for face in shape.faces()
        if face.geom_type == GeomType.PLANE
        and abs(face.normal_at(face.center()).Z - math.sin(math.pi / 4)) < 0.01
        and abs(face.bounding_box().max.Z - bb.max.Z) < EPS
        and abs(face.bounding_box().min.Z - (bb.max.Z - CHAM)) < TOL
    ]
    if not shrunk or len(bevels) < 4:
        problems.append(
            f"the top perimeter is missing its {CHAM} x 45 degree chamfer on all four sides"
        )

    # A virtual bit drives straight down into every pocket: pocket radius, full
    # depth, plus headroom above the block. Clear space here is what rejects a roofed
    # pocket, an intrusion, or a shallow pocket, as one boolean per pocket instead of
    # a point grid.
    checks_run += 1
    blocked = 0
    for cx, cy in centers:
        probe = Pos(cx, cy, (floor_z + bb.max.Z + 4.0) / 2) * Cylinder(
            r - TOL, bb.max.Z + 4.0 - floor_z
        )
        try:
            hit = shape & probe
            if (hit.volume if hit is not None else 0.0) > 0.01:
                blocked += 1
        except Exception:
            blocked += 1
    if blocked:
        problems.append(f"{blocked} of {len(centers)} pockets are not clear for a straight drop-in")

    # Solid under the floors and between the pockets: the stated material, probed
    # where neither chamfer can reach.
    checks_run += 1
    web_x = bb.min.X + WEB + r + dims["pitch"] / 2  # between the first two columns
    web_y = (bb.min.Y + bb.max.Y) / 2
    solid = all(
        shape.is_inside(Vector(cx, cy, bb.min.Z + FLOOR / 2)) for cx, cy in centers
    ) and shape.is_inside(Vector(web_x, web_y, bb.max.Z - DEPTH / 2))
    if not solid:
        problems.append("the floor under the pockets or the web between them is not solid")

    checks_run += 1
    want = _volume(dims)
    if abs(shape.volume - want) > 0.10 * want:
        problems.append(f"volume {shape.volume:.0f}mm3 is off nominal {want:.0f}mm3 by >10%")

    return problems, checks_run


def _matched(centers, edges):
    """How many stated grid centers have one of `edges` on their axis."""
    count = 0
    for cx, cy in centers:
        if any(
            abs(e.arc_center.X - cx) < TOL and abs(e.arc_center.Y - cy) < TOL for e in edges
        ):
            count += 1
    return count


def flex_probes(inst):
    """Parameter overrides and matching ground truth for the isolated build worker.
    The column probes are what catch a grid written out by hand instead of derived
    from the int parameter."""
    shank = inst.dims["shank"]
    cols = inst.dims["cols"]
    return [
        ({"params": {"shank_diameter": round(shank + 0.5, 2)}}, _dims(round(shank + 0.5, 2), cols)),
        ({"params": {"columns": cols + 1}}, _dims(shank, cols + 1)),
        (
            {"params": {"shank_diameter": round(shank + 1.0, 2), "columns": cols - 1}},
            _dims(round(shank + 1.0, 2), cols - 1),
        ),
    ]


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
