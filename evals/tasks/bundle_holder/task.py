"""The bundle_holder task: the corpus's first function task.

It states the problem, the measured interfaces, and the printer, never the geometry:
a wall-mounted holder for a measured cable bundle, one M4 pan-head screw, printed as
it sits. What the holder looks like is the model's call; the grader checks function.
Functional gates are mechanical facts of the B-rep (the bundle has a place to sit and
cannot fall out of it, the screw has a bore, a seat, and driver access), and material
economy is a stepped gradient, so a cleverer design legitimately wins without a human
deciding it was clever.

Retention is checked the way a machinist would fixture it: cross-sections of the part
along the bundle axis, eroded by the bundle radius, tell exactly where a cylinder of
the measured diameter can sit and whether moving it down or away from the wall drives
it into material. Point-membership probes on the B-rep would need a position grid two
orders of magnitude too slow to be fair to curved cradles.

Misfit entries are (message, weight): functional gates outweigh fit-and-finish, and
the flex probes re-assert function but not the volume ladder, so a size-independent
design flaw is charged twice (the recorded stage-overlap rule) while mere bulk is
charged once.
"""

import math
import pathlib
import random
import shutil
from dataclasses import dataclass

import numpy as np
import shapely
from build123d import Cylinder, GeomType, Pos, Rot, Vector

from nurb import builder, checks

EPS = 1e-3
TOL = 0.05

PLATE = 2.4  # stated minimum material behind the screw head
CLEAR = 0.4  # stated minimum clearance around the bundle
HOLE_R = 2.2  # M4 clearance bore, 4.4 diameter
HEAD_R = 4.2  # M4 pan head plus driver, 8.4 diameter
SHIFT = 1.0  # how far the grader tries to move the bundle out of the holder
MIN_LENGTH = 10.0
MIN_BACK = 100.0  # mm2 of flat contact against the wall
L_REF = 12.0  # the reference design's length, used only to size the volume ladder

# Retention search and blocking tolerances. The fit erosion grows the radius so mesh
# chords cannot fake a fit; the penetration erosion shrinks it so only a real overlap
# counts as blocking, not a graze. Blocking material must survive a morphological
# opening of FOIL (unprintable film cannot hold a bundle) and must block along at
# least HOLD of the part's length (one fingernail is not a holder).
FIT_SLACK = 0.05
PEN_DEPTH = 0.30
FOIL = 0.4  # opening radius: features thinner than 0.8 vanish before blocking counts
# A third of the length, not half: a real codex trial cut its head-clearance slot
# through the lip's middle and held the bundle with two honest 3.3mm end fingers,
# 44% of the part, which a user would accept. The cheat this rule kills held with
# a single 1.4mm fingernail, 12%.
HOLD = 1 / 3
SHANK_R = 2.0  # the virtual M4's shank, 4.0 across
HEAD_TEST_R = HEAD_R - 0.15  # the virtual head, slightly lean to absorb seat quantization
# Coexistence: once mounted, only the shank and the real pan head remain (the driver
# corridor is needed before the bundle goes in, holders are screwed down first). The
# installed screw may dent the bundle's nominal cylinder by DENT where they meet,
# because bundles squish, but a screw through the seat is not a holder: a fresh
# verification pass scored exactly that part 1.0 before this check existed.
HEAD_H = 3.2
DENT = 2.0

INSTRUCTION = """\
Design a wall-mounted holder for a cable bundle and save it as parts/bundle_holder.py.

The bundle is measured at {bundle} mm across; the measurement is on file as
bundle_diameter in measurements.toml. It runs horizontally along a wall, and the
holder screws to that wall with one M4 pan-head screw. What the holder looks like is
up to you: the grader checks function mechanically, and every check it runs is listed
below. Retention and mounting dominate the score; material economy refines it.

Orientation contract, all units mm:
- The part prints flat as it sits (Z up on the bed) and mounts in that same
  orientation: its back, the flat face at the part's minimum X, goes against the
  wall, so down stays -Z when mounted. The bundle runs along Y, and the part must be
  at least 10.0 long along Y with at least 100 mm2 of flat back face on the wall.

Function checks:
- Retention: there must be a position where a {bundle} diameter cylinder, running the
  full part length along Y with a clear run at every cross-section, sits in free
  space and cannot move 1.0 straight down (-Z) or 1.0 straight away from the wall
  (+X) without hitting your part. The wall itself blocks the bundle toward -X; your
  part must block down and away, and the blocking material must do it along at least
  a third of the part's length and be at least 0.8 wide (film too thin to print does
  not count as holding anything). Leave at least 0.4 of clearance where the bundle sits
  ({channel} across) so it actually fits. A closed tunnel is fine; bundles thread
  along Y.
- Mounting: a 4.4 diameter through-bore for the screw, axis along X, opening on the
  back face, with at least 2.4 of material along the bore before the head seats and
  solid material around the bore at the seat. The grader drives a virtual M4 along
  the axis: a 4.0 shank from the wall to the seat and a {head} head-and-driver
  cylinder from the seat until it leaves the part in +X, as one continuous solid
  that must clear your material entirely. The screw and the bundle must also
  coexist: with the screw installed (its shank plus a 3.2 tall head), the bundle's
  retained position may overlap it by at most 2.0. A screw through the bundle's
  seat is not a holder.
- Material economy: total volume at or below {v1} mm3 earns full marks; credit steps
  down above {v2} and again above {v3}.
- One solid, and nurb check must report zero findings (it prints support-free as it
  sits, off the bed). The grader runs the printability checks itself and ignores the
  card's [accepted] blocks, so fix findings in the geometry instead of accepting
  them.
- Expose bundle_diameter as a float parameter and derive the geometry from it: the
  holder must rebuild correctly for nearby bundle sizes.
"""

MEASUREMENTS = """\
[bundle_diameter]
value = {bundle}
unit = "mm"
how = "calipers across the taped cable bundle, 2026-08-02"
"""


@dataclass(frozen=True)
class Instance:
    seed: int
    dims: dict
    instruction: str
    measurements: str


def _volume_ladder(bundle):
    """A generous reference volume: back plate tall enough for the cradle plus the
    screw zone, a shelf, and a lip, all PLATE thick at the reference length."""
    channel = bundle + CLEAR
    plate_h = bundle + 12.0
    shelf_w = channel + 2 * PLATE
    lip_h = bundle / 2 + 2.0
    ref = PLATE * L_REF * (plate_h + shelf_w + lip_h)
    return round(1.4 * ref), round(2.0 * ref), round(3.0 * ref)


def _dims(bundle, ladder=True):
    v1, v2, v3 = _volume_ladder(bundle) if ladder else (None, None, None)
    return {
        "bundle": bundle,
        "channel": round(bundle + CLEAR, 2),
        "head": 2 * HEAD_R,
        "v1": v1,
        "v2": v2,
        "v3": v3,
    }


def instance(seed):
    bundle = 6.0 + 0.5 * random.Random(seed).randrange(13)
    dims = _dims(bundle)
    return Instance(
        seed=seed,
        dims=dims,
        instruction=INSTRUCTION.format(**dims),
        measurements=MEASUREMENTS.format(bundle=bundle),
    )


def context():
    """Frozen here, never read from the candidate's card or printer.toml."""
    return checks.Context()


def _cross_sections(shape, bb):
    """(stations, weights, material polygons) along Y, the polygons in (u, v) =
    (x, -z) coordinates so +u is away from the wall and +v is down: the two
    directions the holder must block. The rotation takes Y to +Z so trimesh slices
    horizontally; for a +Z normal its planar transform is a pure translation, so 2D
    coordinates are the rotated x and y axes exactly.

    Stations are feature-aware, not a fixed grid: every distinct mesh-vertex Y plane
    marks a feature boundary, and a station lands at the midpoint of every gap
    between them, so no printable feature can hide between two stations the way an
    adversarial pass hid a tunnel septum. Each station carries the length of part it
    stands for, which is what lets retention demand blocking along a fraction of the
    part instead of at a single lucky slice."""
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
            sections.append(None)  # no material at this station: entirely free
            continue
        polys = list(path.polygons_full)
        if not polys:
            sections.append(None)
            continue
        # Snapped to a micron grid, three orders below every scored tolerance:
        # sections of a curved surface are near-identical polygons whose iterated
        # intersections otherwise compound new vertices without bound (a real tube
        # cradle reached 1.2 million, and grading it blew the one-minute cap).
        sections.append(shapely.set_precision(shapely.union_all(polys), 0.001))
    return stations, weights, sections


def _coexists(u, v, r, back, installs):
    """Whether a bundle at (u, v) tolerates some installed screw: perpendicular
    cylinders intersect exactly when their axis distance is under the radius sum,
    so the dent depth is that sum minus the distance, counted only where the screw's
    x extent actually reaches the bundle."""
    if not installs:
        return True
    z_b = -v
    for yc, zc, depth in installs:
        pieces = (
            (SHANK_R, back - 0.5, back + depth),
            (HEAD_TEST_R, back + depth, back + depth + HEAD_H),
        )
        dented = False
        for radius, x0, x1 in pieces:
            reach = min(x1, u + r) - max(x0, u - r)
            dent = (r + radius) - abs(z_b - zc)
            if reach > 0.1 and dent > DENT:
                dented = True
                break
        if not dented:
            return True
    return False


def _retention(shape, bb, bundle, installs=()):
    """None if a bundle cylinder has a retained place to sit, else what is missing.

    Fit is strict on the raw sections: the cylinder needs a clear run at every
    station. Blocking is judged on morphologically opened sections (erode then
    dilate by FOIL), so a film too thin to print cannot hold the bundle, and it
    must hold along at least HOLD of the part's length, so one fingernail of
    material straddling a lucky station cannot either. Both cheats are from a real
    adversarial pass."""
    r = bundle / 2
    margin = bundle + 4.0
    window = shapely.box(
        bb.min.X - margin, -(bb.max.Z + margin), bb.max.X + margin, -bb.min.Z + margin
    )
    _, weights, sections = _cross_sections(shape, bb)
    fits, pens = [], []
    for material in sections:
        free = window if material is None else window.difference(material)
        fits.append(free.buffer(-(r + FIT_SLACK)))
        if material is None:
            solid = None
        else:
            solid = material.buffer(-FOIL).buffer(FOIL)
            solid = None if solid.is_empty else solid
        free_solid = window if solid is None else window.difference(solid)
        pens.append(free_solid.buffer(-(r - PEN_DEPTH)))

    # Candidate centers stay within a radius of the part: a retained cylinder must
    # touch it, and clipping here keeps the sampler away from the window's own
    # eroded rim, which would otherwise read as phantom blocking material.
    allowed = shapely.box(
        bb.min.X + r - FIT_SLACK, -(bb.max.Z + r), bb.max.X + r, -bb.min.Z + r
    )
    region = allowed
    for fit in fits:
        region = region.intersection(fit)
        if region.is_empty:
            return (
                f"the bundle has nowhere to sit: no clear run for a {bundle} mm "
                f"cylinder along the full part"
            )

    span = float(weights.sum())

    # Each polygon's representative point is guaranteed interior, which is what
    # finds the sliver of fit region a snug tunnel leaves; the grid covers the rest.
    parts = list(getattr(region, "geoms", [region]))
    candidates = [(p.x, p.y) for p in (poly.representative_point() for poly in parts)]
    u0, v0, u1, v1 = region.bounds
    step = 0.25
    candidates += [
        (u, v)
        for u in np.arange(u0, u1 + step, step)
        for v in np.arange(v0, v1 + step, step)
    ]

    # The same candidates, predicates, and order as the point-at-a-time search this
    # replaces, batched: an open curved design (a tube cradle) makes the fit region
    # large and every section polygon curve-heavy at once, and the per-point loop
    # spent minutes of CPU where the grader allows one, zeroing legitimate parts.
    coords = np.asarray(candidates, dtype=np.float64)
    shapely.prepare(region)
    inside = shapely.contains(region, shapely.points(coords))
    held = np.zeros((2, len(coords)))
    for shifted, axis in ((coords + (0.0, SHIFT), 0), (coords + (SHIFT, 0.0), 1)):
        points = shapely.points(shifted)
        blocked = np.zeros(len(coords))
        for weight, pen in zip(weights, pens):
            shapely.prepare(pen)
            blocked += weight * ~shapely.contains(pen, points)
        held[axis] = blocked / span
    retained = inside & (held[0] >= HOLD - 1e-6) & (held[1] >= HOLD - 1e-6)

    screwed_out = False
    for keep, (u, v) in zip(retained, candidates):
        if keep:
            if _coexists(u, v, r, bb.min.X, installs):
                return None
            screwed_out = True
    if screwed_out:
        return (
            "every place the bundle is retained is occupied by the installed screw: "
            "it cannot hold the bundle and take the screw at once"
        )
    return (
        f"the bundle is not retained: nowhere it fits does printable material block "
        f"a {SHIFT} mm move down and away from the wall along a third of the length"
    )


def _bore_candidates(shape):
    """Hole axes as (Y, Z) centers, from circular edges of the bore radius lying in
    Y-Z planes. The bore surface always owns such a circle even when the polish pass
    chamfers the rims: the chamfer-to-bore junction is one."""
    centers = []
    for edge in shape.edges():
        if edge.geom_type != GeomType.CIRCLE or abs(edge.radius - HOLE_R) > TOL:
            continue
        # The circle's own plane normal, not its bounding box: once the retention
        # check has tessellated the shape, edge bounding boxes come from the mesh
        # and a chord-sagitta artifact widens an exact Y-Z circle to ~0.9 in X.
        if abs(edge.normal().X) < 0.99:
            continue
        center = (round(edge.arc_center.Y, 1), round(edge.arc_center.Z, 1))
        if center not in centers:
            centers.append(center)
    return centers


def _ring(shape, x, yc, zc, radius):
    """How many of eight probe points around the axis sit in material."""
    return sum(
        shape.is_inside(
            Vector(x, yc + radius * math.cos(a), zc + radius * math.sin(a))
        )
        for a in (k * math.tau / 8 for k in range(8))
    )


def _screw(back, depth, yc, zc, out_to):
    """The virtual M4 as one gapless solid: a SHANK_R shank from behind the wall to
    the seat depth, and the head-and-driver cylinder from there out of the part.
    Because the shank spans every depth the head has not reached, there is no seam
    between the two for a membrane to hide in, which is exactly how an adversarial
    pass beat the point probes this replaces."""
    shank = (
        Pos(back + (depth - 0.5) / 2, yc, zc) * Rot(0, 90, 0) * Cylinder(SHANK_R, depth + 0.5)
    )
    head_len = out_to - (back + depth)
    if head_len <= 0.05:  # a seat past the part's front is no seat at all
        return shank
    head = (
        Pos(back + depth + head_len / 2, yc, zc)
        * Rot(0, 90, 0)
        * Cylinder(HEAD_TEST_R, head_len)
    )
    return shank + head


def _clear_of(shape, tool):
    """Whether the tool solid passes through the part without hitting material.
    A failed boolean counts as a hit: cheaters do not get to crash their way in."""
    try:
        hit = shape & tool
        return (hit.volume if hit is not None else 0.0) < 0.05
    except Exception:
        return False


def _mount(shape, bb):
    """(bore_ok, seat_ok, head_ok, installs) for the best screw-hole candidate.
    installs lists every workable (yc, zc, depth): where a screw would actually sit
    once driven, which is what the retention check holds the bundle against."""
    ring_r = (HOLE_R + HEAD_R) / 2
    best = (False, False, False)
    installs = []
    back = bb.min.X
    for yc, zc in _bore_candidates(shape):
        # Walk into the part from the back until the material around the bore ends:
        # that is where the head seats. The walk itself is the seat-material check.
        seat_x = None
        depths = np.arange(back + 0.3, back + 15.0, 0.1)
        for x in depths:
            if _ring(shape, x, yc, zc, ring_r) < 6:
                seat_x = x
                break
        if seat_x is None:
            seat_x = float(depths[-1])

        # The stated 4.4mm bore must clear through the seat depth, then the whole
        # screw must clear at some seat depth. Boolean intersection with the actual
        # B-rep, not point probes: material anywhere in the swept volume is material,
        # no matter how it dodges a grid.
        bore_depth = max(PLATE, seat_x - back)
        bore_clearance = (
            Pos(back + (bore_depth - 0.5) / 2, yc, zc)
            * Rot(0, 90, 0)
            * Cylinder(HOLE_R - TOL, bore_depth + 0.5)
        )
        bore_ok = _clear_of(shape, bore_clearance)
        head_ok = False
        if bore_ok:
            for depth in np.arange(PLATE, min(15.0, bb.max.X - back) + 0.01, 0.25):
                if _clear_of(shape, _screw(back, depth, yc, zc, bb.max.X + 1.0)):
                    head_ok = True
                    installs.append((yc, zc, float(depth)))
                    break
        seat_ok = bore_ok and seat_x - back >= PLATE - 0.25
        candidate = (bore_ok, seat_ok, head_ok)
        if sum(candidate) > sum(best):
            best = candidate
    return (*best, installs)


def misfits(shape, dims):
    """Everything wrong with the holder, as (problems, total_weight). Entries are
    (message, weight): retention and the screw mount are the function and carry the
    score; back contact, length, and the volume ladder refine it."""
    problems = []
    total = 0
    bb = shape.bounding_box()

    total += 1
    if bb.size.Y < MIN_LENGTH - TOL:
        problems.append((f"only {bb.size.Y:.1f} mm long along Y, need {MIN_LENGTH}", 1))

    total += 1
    back = sum(
        face.area
        for face in shape.faces()
        if face.geom_type == GeomType.PLANE
        and abs(face.bounding_box().min.X - bb.min.X) < EPS
        and face.bounding_box().size.X < EPS
    )
    if back < MIN_BACK:
        problems.append(
            (f"only {back:.0f} mm2 of flat back face against the wall, need {MIN_BACK:.0f}", 1)
        )

    bore_ok, seat_ok, head_ok, installs = _mount(shape, bb)

    total += 4
    miss = _retention(shape, bb, dims["bundle"], installs)
    if miss:
        problems.append((miss, 4))

    total += 3
    if not bore_ok:
        problems.append(("no clear 4.4 mm screw bore along X opening on the back face", 3))
    total += 1
    if not seat_ok:
        problems.append(
            (f"less than {PLATE} mm of material along the bore before the head seats", 1)
        )
    total += 2
    if not head_ok:
        problems.append(
            (f"the {2 * HEAD_R} mm head-and-driver clearance past the seat is blocked", 2)
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
    out = []
    for grow in (1.0, 2.0):
        bundle = round(inst.dims["bundle"] + grow, 2)
        out.append(({"params": {"bundle_diameter": bundle}}, _dims(bundle, ladder=False)))
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
