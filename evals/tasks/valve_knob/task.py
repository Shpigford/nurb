"""The valve_knob task: a replacement knob for a measured D-shaft, graded by fit.

The corpus's first mating-fit task. The counterpart is not printed, it is driven: the
grader builds a virtual D-stem from the measured diameter and across-flat and pushes
it into the candidate's bore, the way bundle_holder drives a virtual M4. Fit is
graded from both sides of the tolerance band: the stem grown by the stated clearance
must pass clean through, and grown by the stated slop it must jam, so a bore that is
too tight and a bore that rattles both lose. Rotation closes the loop: the same stem
turned 20 degrees must collide, which only a bore that actually models the flat can
do; a lazy round bore fits the stem and fails the torque.

Everything is boolean intersections with the actual B-rep, no point grids: material
anywhere in a swept volume is material, no matter how it dodges a sampler.
"""

import math
import pathlib
import random
import shutil
from dataclasses import dataclass

import numpy as np
import shapely
from build123d import Box, Cylinder, GeomType, Pos, Rot

from nurb import builder, checks

EPS = 1e-3
TOL = 0.05

MIN_H = 12.0
MIN_BED = 300.0  # mm2 of flat bottom on the bed
ENGAGE = 10.0  # how deep the stem must reach into the bore
CLEAR = 0.3  # stated diametral clearance the bore must give the stem
SLOP = 1.0  # stated diametral growth that must jam
TWIST = 20.0  # degrees the stem is turned for the torque check
GRIP_MIN = 28.0  # narrowest the knob may be across at grip height
LOBE = 1.12  # widest reach over narrowest at grip height
JAM = 0.5  # mm3 of overlap that counts as a real collision, not kernel noise

INSTRUCTION = """\
Design a replacement knob for a broken valve handle, and save it as
parts/valve_knob.py.

The valve's stem is a D-shaft measured at {shaft} mm across with {flat} mm across
the flat; both are on file in measurements.toml as shaft_diameter and
shaft_across_flat. The stem stands 12.0 proud of the valve body. Model the knob
bore-up as it prints: the bore opens straight up, on the part's vertical centerline,
with the stem's flat facing +X; in use the knob flips over onto the stem. What the
knob looks like is up to you: the grader checks fit and function mechanically, and
every check it runs is listed below.

Function checks, all units mm:
- The part prints as it sits: flat on the bed with at least 300 mm2 of bottom face,
  at least 12.0 tall, one solid, support-free.
- Fit: the grader drives a virtual stem, grown by 0.3 on both the diameter and the
  across-flat, straight down the centerline to 10.0 below your top face. It must
  pass without touching your material, so leave real clearance.
- No rattle: the same stem grown by 1.0 instead must jam: if it also passes, the
  bore is too loose to steer the valve.
- Torque: the 0.3-grown stem, turned 20 degrees about its axis, must collide with
  your material. A round bore passes the stem at every angle and fails this; only a
  bore that models the flat transmits torque.
- Grip: at half the knob's height, the outside must measure at least 28.0 across at
  its narrowest, and its widest reach from the centerline must be at least 12%
  past its narrowest: lobes, flats, or a lever arm, so wet hands can turn it.
- Material economy: total volume at or below {v1} mm3 earns full marks; credit
  steps down above {v2} and again above {v3}.
- nurb check must report zero findings. The grader runs the checks itself and
  ignores the card's [accepted] blocks, so fix findings in the geometry instead of
  accepting them.
- Expose shaft_diameter and shaft_across_flat as float parameters and derive the
  bore from both: the knob must rebuild correctly for nearby stems.
"""

MEASUREMENTS = """\
[shaft_diameter]
value = {shaft}
unit = "mm"
how = "calipers across the stem, 2026-08-21"

[shaft_across_flat]
value = {flat}
unit = "mm"
how = "calipers from the flat to the round side, 2026-08-21"
"""


@dataclass(frozen=True)
class Instance:
    seed: int
    dims: dict
    instruction: str
    measurements: str


def _volume_ladder():
    """A generous reference: a solid 32 x 14 cylinder of knob."""
    ref = math.pi * 16.0**2 * 14.0
    return round(1.2 * ref), round(1.8 * ref), round(2.6 * ref)


def _dims(shaft, flat, ladder=True):
    v1, v2, v3 = _volume_ladder() if ladder else (None, None, None)
    return {"shaft": shaft, "flat": flat, "v1": v1, "v2": v2, "v3": v3}


def instance(seed):
    rng = random.Random(seed)
    shaft = 6.0 + 0.5 * rng.randrange(9)
    flat = round(shaft - 1.0 - 0.25 * rng.randrange(5), 2)
    dims = _dims(shaft, flat)
    return Instance(
        seed=seed,
        dims=dims,
        instruction=INSTRUCTION.format(**dims),
        measurements=MEASUREMENTS.format(shaft=shaft, flat=flat),
    )


def context():
    """Frozen here, never read from the candidate's card or printer.toml."""
    return checks.Context()


def _stem(shaft, flat, grow, height):
    """The virtual D-stem at the origin, axis +Z, flat facing +X, grown by `grow`
    on both measurements. One gapless solid, like bundle_holder's virtual screw."""
    radius = shaft / 2 + grow / 2
    offset = (flat - shaft / 2) + grow / 2  # the flat's distance from the axis
    body = Cylinder(radius, height)
    # The box's near face lands exactly on the flat plane.
    cut = Pos(offset + (radius + 1.0) / 2, 0, 0) * Box(
        radius + 1.0, 2 * radius + 2.0, height + 1.0
    )
    return body - cut


def _overlap(shape, tool):
    """Material the tool hits, in mm3. A failed boolean counts as a full jam for
    probes that must clear, and as no jam for probes that must collide, so a crash
    never helps the candidate; callers pick the reading."""
    hit = shape & tool
    return hit.volume if hit is not None else 0.0


def _drive(shape, bb, dims, grow, twist=0.0):
    """Overlap between the part and the grown, optionally twisted stem, driven down
    the centerline to ENGAGE below the top face, entering from above the part."""
    cx = (bb.min.X + bb.max.X) / 2
    cy = (bb.min.Y + bb.max.Y) / 2
    height = ENGAGE + 2.0
    tool = (
        Pos(cx, cy, bb.max.Z - ENGAGE + height / 2)
        * Rot(0, 0, twist)
        * _stem(dims["shaft"], dims["flat"], grow, height)
    )
    try:
        return _overlap(shape, tool)
    except Exception:
        return None


def _grip(shape, bb):
    """(narrowest across, widest over narrowest) of the outer profile at half
    height, from a meshed section: the outer ring's nearest and farthest points from
    the centerline."""
    mesh = builder.to_mesh(shape, tolerance=0.05)
    cx = (bb.min.X + bb.max.X) / 2
    cy = (bb.min.Y + bb.max.Y) / 2
    z = (bb.min.Z + bb.max.Z) / 2 + 0.013  # off any face plane
    paths = mesh.section_multiplane([0, 0, z], [0, 0, 1], [0.0])
    if not paths or paths[0] is None:
        return 0.0, 0.0
    polys = list(paths[0].polygons_full)
    if not polys:
        return 0.0, 0.0
    outer = max(polys, key=lambda p: p.area).exterior
    center = shapely.points([[cx, cy]])[0]
    nearest = shapely.distance(outer, center)
    coords = np.asarray(outer.coords)
    farthest = float(np.max(np.hypot(coords[:, 0] - cx, coords[:, 1] - cy)))
    return 2 * nearest, farthest / max(nearest, EPS)


def misfits(shape, dims):
    """Everything wrong with the knob, as (problems, total_weight). Entries are
    (message, weight): the fit band and the torque are the function and carry the
    score; height, bed contact, grip, and the volume ladder refine it."""
    problems = []
    total = 0
    bb = shape.bounding_box()

    total += 1
    if bb.size.Z < MIN_H - TOL:
        problems.append((f"only {bb.size.Z:.1f} mm tall, need {MIN_H}", 1))

    total += 1
    bed = sum(
        face.area
        for face in shape.faces()
        if face.geom_type == GeomType.PLANE
        and abs(face.bounding_box().min.Z - bb.min.Z) < EPS
        and face.bounding_box().size.Z < EPS
    )
    if bed < MIN_BED:
        problems.append((f"only {bed:.0f} mm2 of flat bottom on the bed, need {MIN_BED:.0f}", 1))

    total += 3
    fit = _drive(shape, bb, dims, CLEAR)
    if fit is None or fit > TOL:
        problems.append(
            (
                f"the stem does not fit: the {CLEAR}-grown stem hits material on its "
                f"way to {ENGAGE} below the top face",
                3,
            )
        )

    total += 2
    slop = _drive(shape, bb, dims, SLOP)
    if slop is not None and slop < JAM:
        problems.append(
            (f"the bore rattles: even the {SLOP}-grown stem passes clean through", 2)
        )

    total += 3
    jams = [_drive(shape, bb, dims, CLEAR, twist=sign * TWIST) for sign in (1, -1)]
    if any(jam is not None and jam < JAM for jam in jams):
        problems.append(
            (
                f"no torque: the stem turned {TWIST:.0f} degrees still passes, so the "
                f"bore never engages the flat",
                3,
            )
        )

    across, lobe = _grip(shape, bb)
    total += 1
    if across < GRIP_MIN - TOL:
        problems.append(
            (f"only {across:.1f} mm across at grip height, need {GRIP_MIN}", 1)
        )
    total += 2
    if lobe < LOBE - 0.005:
        problems.append(
            (
                f"nothing to grip: the profile at half height is {lobe:.2f}x its "
                f"narrowest, need {LOBE:.2f}x",
                2,
            )
        )

    # The stepped material gradient. Skipped (thresholds None) when re-asserted by
    # the flex probes: bulk is size-independent and gets charged once.
    if dims["v1"] is not None:
        for threshold in (dims["v1"], dims["v2"], dims["v3"]):
            total += 1
            if shape.volume > threshold:
                problems.append(
                    (f"volume {shape.volume:.0f} mm3 is over the {threshold} mm3 step", 1)
                )

    return problems, total


def flex_probes(inst):
    shaft, flat = inst.dims["shaft"], inst.dims["flat"]
    out = []
    for d_grow, f_grow in ((0.5, 0.5), (1.0, 0.75)):
        d, f = round(shaft + d_grow, 2), round(flat + f_grow, 2)
        out.append(
            (
                {"params": {"shaft_diameter": d, "shaft_across_flat": f}},
                _dims(d, f, ladder=False),
            )
        )
    return out


def materialize(seed, dest):
    """Write the project a model starts from: fixture, the seeded measurements, and
    the same AGENTS.md a real project gets from `nurb new`."""
    import importlib.resources

    dest = pathlib.Path(dest)
    fixture = pathlib.Path(__file__).parent / "fixture"
    shutil.copytree(fixture, dest, dirs_exist_ok=True)
    (dest / "measurements.toml").write_text(instance(seed).measurements, encoding="utf-8")
    skill = importlib.resources.files("nurb").joinpath("agents.md").read_text(encoding="utf-8")
    (dest / "AGENTS.md").write_text(skill, encoding="utf-8")
    return dest
