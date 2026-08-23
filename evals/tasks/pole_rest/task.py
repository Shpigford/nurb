"""The pole_rest task: a drying-rack rest for a measured pole, where only curvature
passes.

The second function task, and the corpus's first that a prismatic design cannot win.
The problem states an interface (the pole's axis height, so several rests hold one
pole level) and a support requirement a machinist would state: contact within 0.4 of
the pole's surface, with real material behind it, along a continuous 120 degree arc
of the circumference. A V-block touches at two lines and a square channel at three;
neither owns an arc. Only a cradle cut near the pole's own radius does, so the gate
mechanically demands the one thing the first corpus never did: curved geometry sized
to a measured curve.

Support is measured on meshed cross-sections along the pole, the same machinery as
bundle_holder: stations are feature-aware so nothing printable hides between them,
contact is a distance query against the section polygon (exact on the section, no
point grid to thread), and the backing probe stands 1.2 behind the contact so a film
that merely traces the arc counts as nothing.
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

MIN_LENGTH = 20.0
MIN_BED = 200.0  # mm2 of flat bottom on the bed
GAP_MIN = 0.1  # stated minimum clearance around the pole
CONTACT = 0.4  # stated: support counts within this of the pole's surface
BACKING = 1.2  # stated continuous material behind the contact
ARC_DEG = 120.0
COVER = 2 / 3  # fraction of the length the arc must hold along
L_REF = 20.0  # reference length for the volume ladder

# Measurement tolerances. Fit is checked 0.02 under the stated gap so kernel noise
# never charges a legitimate 0.1 clearance. Backing is measured as one continuous
# radial intersection that starts within the contact band, so a second skin across
# an air gap cannot stand in for wall thickness.
FIT_R = GAP_MIN - 0.02
STEP_DEG = 5

INSTRUCTION = """\
Design a rest that holds a freshly finished pole while it dries, and save it as
parts/pole_rest.py.

The pole is measured at {pole} mm across; the measurement is on file as
pole_diameter in measurements.toml. Several identical rests stand in a row on the
bench and the pole lies across them, so the interface is fixed: the pole runs along
Y with its axis exactly {axis_h} above the bed, centered over your part's footprint
in X. The finish is soft, so the pole must be cradled, not balanced on edges. What
the rest looks like is up to you: the grader checks function mechanically, and every
check it runs is listed below.

Function checks, all units mm:
- The part prints as it sits and is used as it prints: flat on the bed with at least
  200 mm2 of bottom face, at least 20.0 long along Y, one solid, support-free.
- Fit: with the pole's axis at the stated position, your material stays at least 0.1
  clear of the pole along the whole part.
- Support: at each cross-section, material within 0.4 of the pole's surface, itself
  backed by at least 1.2 of material behind the contact, along one continuous arc of
  at least 120 degrees of the pole's circumference. That arc must hold at
  cross-sections covering at least two thirds of the part's length. Edges and points
  of contact cannot do this; a cradle close to the pole's own radius can.
- Drop-in: the pole must lower straight down (-Z) from above into the seat without
  hitting your part on the way.
- Material economy: total volume at or below {v1} mm3 earns full marks; credit steps
  down above {v2} and again above {v3}.
- nurb check must report zero findings. The grader runs the checks itself and
  ignores the card's [accepted] blocks, so fix findings in the geometry instead of
  accepting them.
- Expose pole_diameter as a float parameter and derive the geometry from it: the
  rest must rebuild correctly for nearby pole sizes, with the axis height staying
  exactly {axis_h}.
"""

MEASUREMENTS = """\
[pole_diameter]
value = {pole}
unit = "mm"
how = "calipers across the sanded pole, 2026-08-21"
"""


@dataclass(frozen=True)
class Instance:
    seed: int
    dims: dict
    instruction: str
    measurements: str


def _volume_ladder(pole, axis_h):
    """A generous reference: a full-width block up to the axis height with the
    pole's half-cylinder taken out, at the reference length."""
    r = pole / 2 + GAP_MIN
    width = 2 * r + 4.8
    ref = L_REF * (width * axis_h - 0.5 * math.pi * r**2)
    return round(1.4 * ref), round(2.0 * ref), round(3.0 * ref)


def _dims(pole, axis_h, ladder=True):
    v1, v2, v3 = _volume_ladder(pole, axis_h) if ladder else (None, None, None)
    return {"pole": pole, "axis_h": axis_h, "v1": v1, "v2": v2, "v3": v3}


def instance(seed):
    rng = random.Random(seed)
    pole = 18.0 + 0.5 * rng.randrange(13)
    axis_h = 16.0 + 0.5 * rng.randrange(9)
    dims = _dims(pole, axis_h)
    return Instance(
        seed=seed,
        dims=dims,
        instruction=INSTRUCTION.format(**dims),
        measurements=MEASUREMENTS.format(pole=pole),
    )


def context():
    """Frozen here, never read from the candidate's card or printer.toml."""
    return checks.Context()


def _cross_sections(shape, bb):
    """(weights, material polygons) along Y, the polygons in (x, z) coordinates.
    Stations are feature-aware, not a fixed grid: every distinct mesh-vertex Y plane
    marks a feature boundary and a station lands in every gap between them, so no
    printable feature can hide between two stations. Each station carries the length
    of part it stands for."""
    mesh = builder.to_mesh(shape, tolerance=0.05)
    rot = np.array(
        [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=np.float64
    )
    mesh.apply_transform(rot)
    y0, y1 = bb.min.Y, bb.max.Y
    planes = np.unique(np.round(mesh.vertices[:, 2], 1))
    mids = (planes[:-1] + planes[1:]) / 2 + 0.011  # off any face plane
    uniform = np.arange(y0 + 0.1, y1 - 0.05, 1.0)
    stations = np.unique(np.concatenate([mids, uniform]))
    stations = stations[(stations > y0 + 0.02) & (stations < y1 - 0.02)]
    if len(stations) > 400:
        stations = stations[:: math.ceil(len(stations) / 400)]

    edges = np.concatenate([[y0], (stations[:-1] + stations[1:]) / 2, [y1]])
    weights = np.diff(edges)

    paths = mesh.section_multiplane([0, 0, 0], [0, 0, 1], stations)
    sections = []
    for path in paths:
        if path is None:
            sections.append(None)
            continue
        polys = list(path.polygons_full)
        if not polys:
            sections.append(None)
            continue
        # Snapped to a micron grid: sections of a curved cradle are near-identical
        # polygons whose iterated set operations otherwise compound vertices without
        # bound (the lesson bundle_holder's tube cradle taught).
        sections.append(shapely.set_precision(shapely.union_all(polys), 0.001))
    # The rotation maps (x, y, z) to (x, -z, y): section coordinates come out as
    # (x, -z), so flip v to keep the arc math in honest bed coordinates.
    flipped = [
        shapely.transform(m, lambda pts: pts * (1.0, -1.0)) if m is not None else None
        for m in sections
    ]
    return weights, flipped


def _support(shape, bb, pole, axis_h):
    """None if the pole is cradled as stated, else what is missing."""
    r = pole / 2
    cx = (bb.min.X + bb.max.X) / 2
    cz = bb.min.Z + axis_h
    weights, sections = _cross_sections(shape, bb)
    center = shapely.points([[cx, cz]])[0]

    angles = np.deg2rad(np.arange(0, 360, STEP_DEG))
    directions = np.stack([np.cos(angles), np.sin(angles)], axis=1)
    center_xy = np.array([cx, cz])
    starts = center_xy + (r + FIT_R) * directions
    ends = center_xy + (r + CONTACT + BACKING + TOL) * directions
    rays = shapely.linestrings(np.stack([starts, ends], axis=1))
    need = int(ARC_DEG / STEP_DEG) + 1  # consecutive samples spanning the stated arc

    span = float(weights.sum())
    held = 0.0
    for weight, material in zip(weights, sections):
        if material is None:
            continue
        # Fit is exact on the section polygon: the nearest material to the axis must
        # stay a pole radius plus the stated gap away, at every station.
        if shapely.distance(material, center) < r + FIT_R:
            return (
                f"the pole does not fit: material intrudes within {GAP_MIN} of a "
                f"{pole} mm pole at the stated axis position"
            )
        radial_material = shapely.intersection(material, rays)
        arc = np.array(
            [_has_backed_contact(hit, center_xy, r) for hit in radial_material], dtype=bool
        )
        # Longest run of supported samples, circularly: doubling the array makes a
        # wraparound arc an ordinary run.
        run = best = 0
        for hit in np.concatenate([arc, arc]):
            run = run + 1 if hit else 0
            best = max(best, run)
        if best >= min(need, len(angles)):
            held += weight
    if held + EPS < COVER * span:
        return (
            f"the pole is not cradled: a continuous {ARC_DEG:.0f} degree arc of backed "
            f"contact holds along only {held / span:.0%} of the length, need "
            f"{COVER:.0%}"
        )
    return None


def _has_backed_contact(hit, center, pole_r):
    """Whether one uninterrupted radial material span starts near the pole and is
    at least the stated backing thickness."""
    for segment in shapely.get_parts(hit):
        coords = shapely.get_coordinates(segment)
        if len(coords) < 2:
            continue
        radii = np.linalg.norm(coords - center, axis=1)
        if radii.min() <= pole_r + CONTACT + TOL and np.ptp(radii) >= BACKING - TOL:
            return True
    return False


def _drop_in(shape, bb, pole, axis_h):
    """Whether the pole can lower straight down into the seat: its swept descent,
    slightly lean so a stated-clearance cradle never collides, must clear the part.
    A failed boolean counts as a hit."""
    r = pole / 2 - TOL
    cx = (bb.min.X + bb.max.X) / 2
    cz = bb.min.Z + axis_h
    length = bb.size.Y + 2.0
    cy = (bb.min.Y + bb.max.Y) / 2
    top = bb.max.Z + 2.0
    sweep = Pos(cx, cy, cz) * Rot(90, 0, 0) * Cylinder(r, length)
    # When the axis sits above the part's top, as an open cradle's does, the descent
    # above the seat is already outside the part and needs no swept box.
    if top > cz + EPS:
        sweep += Pos(cx, cy, (cz + top) / 2) * Box(2 * r, length, top - cz)
    try:
        hit = shape & sweep
        return (hit.volume if hit is not None else 0.0) < 0.05
    except Exception:
        return False


def misfits(shape, dims):
    """Everything wrong with the rest, as (problems, total_weight). Entries are
    (message, weight): fit and the arc are the function and carry the score; length,
    bed contact, drop-in, and the volume ladder refine it."""
    problems = []
    total = 0
    bb = shape.bounding_box()

    total += 1
    if bb.size.Y < MIN_LENGTH - TOL:
        problems.append((f"only {bb.size.Y:.1f} mm long along Y, need {MIN_LENGTH}", 1))

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

    total += 6
    miss = _support(shape, bb, dims["pole"], dims["axis_h"])
    if miss:
        problems.append((miss, 6))

    total += 2
    if not _drop_in(shape, bb, dims["pole"], dims["axis_h"]):
        problems.append(("the pole cannot lower straight down into the seat", 2))

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
    out = []
    for grow in (1.5, -1.5):
        pole = round(inst.dims["pole"] + grow, 2)
        out.append(
            (
                {"params": {"pole_diameter": pole}},
                _dims(pole, inst.dims["axis_h"], ladder=False),
            )
        )
    return out


def materialize(seed, dest):
    """Write the project a model starts from: fixture, the seeded measurement, and
    the same AGENTS.md a real project gets from `nurb new`."""
    import importlib.resources

    dest = pathlib.Path(dest)
    fixture = pathlib.Path(__file__).parent / "fixture"
    shutil.copytree(fixture, dest, dirs_exist_ok=True)
    (dest / "measurements.toml").write_text(instance(seed).measurements, encoding="utf-8")
    skill = importlib.resources.files("nurb").joinpath("agents.md").read_text(encoding="utf-8")
    (dest / "AGENTS.md").write_text(skill, encoding="utf-8")
    return dest
