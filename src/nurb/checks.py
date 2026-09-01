"""Printability rules, run against the solid rather than against an export.

Checking the B-rep instead of an STL means real faces with exact areas and normals
instead of triangles, which is what makes most of these rules cheap and exact.

A rule takes the shape and a Context and yields Findings. Rules compose: they never
see each other, and `run` gathers them.
"""

import pathlib
from dataclasses import dataclass, field, replace
from math import asin, atan2, cos, degrees, pi, sin

from build123d import Axis, CenterOf, GeomType, Plane, Vector

from . import supports

FAIL = "fail"  # this will not print, or will not work
WARN = "warn"  # this needs attention, most often support
NOTE = "note"  # accounted for: a cost this part has chosen, not a defect to fix

# Findings sort by this, worst first. Note that it is also how far a severity gets to
# push the exit code around: `nurb check --strict` and `nurb verify` both ignore notes,
# because a note is the user telling the checker something rather than the other way.
# Four characters each, which is what `Finding.__str__` pads to, so the columns line up.
RANK = {FAIL: 0, WARN: 1, NOTE: 2}

# What each rule is called to somebody who owns a printer rather than to whoever wrote
# the rule. A rule's name is an identifier: it is stable, it is what the CLI prints, and
# it is what an agent matches on, so it never changes. But the person reading the viewer
# came here to get a part printed, and `concave_cosmetic` tells them nothing they can
# act on. Both are true at once, which is why this is a translation and not a rename.
# Kept short because the panel gives them a fixed column: a label that wraps puts two
# ragged lines next to a message that is already wrapping. LABEL_WIDTH is what fits.
LABEL_WIDTH = 14
LABELS = {
    # Covers both of this rule's states, which is why it is not "loose pieces": the
    # same rule fires on a part that came apart and on one that built nothing at all.
    "solids": "not one piece",
    "overhang": "steep slope",
    "floating": "starts on air",
    "hole_ceiling": "hole on air",
    "min_wall": "thin wall",
    "sliver": "tiny detail",
    "concave_cosmetic": "inside corner",
    "bed_bevel": "poor bed grip",
    "warp_risk": "corners lift",
    "pin": "skinny pin",
    "stability": "tips over",
    "projection_ratio": "long reach",
    "build_volume": "too big",
}


def label(rule):
    """What to call a rule on screen. Falls back to the identifier, which is honest:
    a rule with no label is a gap to fill, not a reason to show nothing."""
    return LABELS.get(rule, rule)


@dataclass(frozen=True)
class Finding:
    """What a rule found, said twice.

    `message` is written for whoever is going to fix it: exact, dense, and in the
    vocabulary of the doctrine, because an agent reads it and then edits geometry.
    `plain` is the same fact for whoever is looking at the part, who came here to print
    something and has never needed the word "facet".

    Two strings rather than one because the audiences want opposite things. "1.4mm strip
    sitting in a concave junction over 42.4mm2" is the right sentence for the reader who
    is about to move that face, and the wrong one for the reader deciding whether to
    press print. Where a message is already plain, `plain` stays None and both get it.
    """

    rule: str
    severity: str
    message: str
    value: float | None = None
    where: tuple | None = None
    plain: str | None = None

    @property
    def label(self):
        return label(self.rule)

    @property
    def said(self):
        """The sentence to show a person."""
        return self.plain or self.message

    def __str__(self):
        spot = f"  at ({self.where[0]:.1f}, {self.where[1]:.1f}, {self.where[2]:.1f})" if self.where else ""
        return f"{self.severity:4}  {self.rule:20} {self.message}{spot}"


@dataclass
class Context:
    """What a rule needs to know beyond the geometry itself.

    `up` is the build direction, which is the model's z only when a part is printed
    the way it is modelled. Notch parts are, so +z is right for them. Nothing
    guarantees that in general, and getting it wrong does not error: it reports
    confident nonsense about every face in the part.
    """

    bed: tuple = (256.0, 256.0, 256.0)
    up: tuple = (0.0, 0.0, 1.0)
    overhang_limit: float = 45.0  # degrees away from the build direction
    bridge_limit: float = 30.0  # how far this printer will span unsupported
    overhang_reach: float = 1.0  # a ledge shorter than this cannot droop enough to matter
    forward: tuple | None = None  # which way a wall-mounted part cantilevers, if it does
    projection_limit: float = 2.5  # reach over height, past which height is the fix
    cosmetic_chamfer: float = 1.0  # the size the polish pass uses
    min_wall: float = 1.0  # what this printer lays down reliably; per part, per card
    sliver_area: float = 1.0
    warp_area: float = 20000.0  # first-layer mm2 past which contraction peels sharp corners
    warp_radius: float = 8.0  # a plan corner rounded under this is still a peel point
    material: str | None = None  # what this prints in; scales warp_area, see SHRINK
    accepted: dict = field(default_factory=dict)  # rule -> how many are already known
    # The whole part prints on support material, by the user's choice. `supported()` in
    # the part file is the narrower way to say the same thing about one feature, and is
    # what the doctrine sends you to first; this is for the part that is all overhang.
    # A card's decision, never a machine's, which is why `printer()` refuses it.
    supports: bool = False


RULES = {}


def rule(name):
    def register(fn):
        RULES[name] = fn
        return fn

    return register


def run(shape, ctx=None, only=None, stop=None):
    # An assembly's compound carries its recorded joints, and motion is the only
    # thing worth judging about it: overhang and min_wall on an assembled scene
    # would report confident nonsense about parts that each checked clean alone.
    scene = getattr(shape, "_nurb_scene", None)
    if scene is not None:
        from .assembly import sweep

        return sweep(scene, stop)
    ctx = ctx or Context()
    found = []
    for name, fn in RULES.items():
        if only and name not in only:
            continue
        found.extend(fn(shape, ctx))
    # A part in pieces gets judged on whichever piece the kernel listed first, so the
    # rest of the report is true of a fragment and misleading about the part. The
    # `solids` docstring has the whole argument; this is where it takes effect.
    apart = [f for f in found if f.rule == "solids"]
    if apart:
        return apart
    return sorted(found, key=lambda f: (RANK[f.severity], f.rule))


# --- geometry helpers --------------------------------------------------------


def edge_faces(shape):
    """Every edge mapped to the faces sharing it."""
    out = {}
    for face in shape.faces():
        for edge in face.edges():
            out.setdefault(edge, []).append(face)
    return out


PROBE = 1e-3


def _into_face(face, point, tangent):
    """The direction leaving `point` across the face, perpendicular to the edge.

    Which of the two candidates is the right one gets settled by stepping and asking
    the face, rather than by trusting a winding convention. Aiming at the centroid
    instead is tempting and wrong: a face that is L-shaped or has the rest of the part
    merged into it puts its centroid somewhere that has nothing to do with which side
    of this edge the material is on. That mistake showed up as convex slab edges
    reported concave.
    """
    across = tangent.cross(face.normal_at(point)).normalized()
    forward = face.distance_to(point + across * PROBE)
    backward = face.distance_to(point - across * PROBE)
    return across if forward <= backward else -across


def is_convex(edge, f1, f2):
    """True if the material folds away from itself across this edge.

    The test is `n1 . u2`: does the second face extend in the direction the first
    face's outward normal points? If it does, the solid is folding back on itself and
    the edge is concave.

    The obvious alternative, offsetting the edge along the averaged face normals and
    asking whether that point is inside the solid, is recorded in the Fusion notes as
    failing. It cannot work: at a concave edge the averaged normal points into open
    space just as it does at a convex one, so both answer the same. What separates
    them is where the faces go, not where they face, which is why this uses a
    direction along the face and not the normal.
    """
    point = edge.center()
    tangent = edge.tangent_at(0.5)
    return f1.normal_at(point).dot(_into_face(f2, point, tangent)) < 0


def concave_edges(shape):
    """Every concave edge, which is where polish is forbidden and stress collects."""
    out = []
    for edge, faces in edge_faces(shape).items():
        if len(faces) != 2:
            continue  # seam or free edge, nothing to be convex about
        if not is_convex(edge, faces[0], faces[1]):
            out.append(edge)
    return out


# --- rules -------------------------------------------------------------------


@rule("solids")
def solids(shape, ctx):
    """A part that came apart, or never came together.

    The doctrine's first line about printability is to return one solid, and until now
    nothing enforced it: two loose bodies report a plausible bounding box, export
    happily, and reach the plate as two pieces nobody asked for. The near miss is worse
    than the obvious one. A shelf that only touches its post along a tangent line reads
    as joined in the viewer from every angle, and the kernel quietly keeps it as two.

    What makes this the one rule that silences the others is that every rule after it
    reads `shape.solids()[0]`. On a part in pieces they all describe whichever fragment
    the kernel happened to list first, so the report fills with overhangs and floating
    tips that are true of that fragment and beside the point. One finding that names the
    real fault beats five that describe its symptoms.

    The strays are reported smallest last and located, because the gap is at the join
    and the join is what has to move.
    """
    bodies = shape.solids()
    if len(bodies) == 1:
        return []
    if not bodies:
        return [Finding("solids", FAIL, "builds no solid at all, so there is nothing to print", value=0)]
    ordered = sorted(bodies, key=lambda s: -s.volume)
    main, stray = ordered[0], ordered[-1]
    return [
        Finding(
            "solids",
            FAIL,
            f"{len(bodies)} separate pieces, not one part: {main.volume:.0f}mm3 "
            f"and {len(ordered) - 1} more down to {stray.volume:.0f}mm3",
            plain=f"this came out as {len(bodies)} separate pieces instead of one. "
            "Whatever should join them is touching at a point, or missing",
            value=len(bodies),
            where=tuple(round(v, 2) for v in stray.center()),
        )
    ]


@rule("sliver")
def sliver(shape, ctx):
    """Faces too small to print as anything but a smear.

    Chamfers meeting at a corner legitimately make a few, so a part declares how many
    it has earned. A count above the baseline is a regression; at or below it is
    silence. The count is the assertion, not the individual faces, because which face
    is which shifts as soon as anything upstream of the polish pass moves.
    """
    small = [f for f in shape.faces() if f.area < ctx.sliver_area]
    allowed = ctx.accepted.get("sliver", 0)
    if len(small) <= allowed:
        return []
    worst = min(small, key=lambda f: f.area)
    return [
        Finding(
            "sliver",
            WARN,
            f"{len(small)} faces under {ctx.sliver_area}mm2, {allowed} accounted for",
            plain=f"{len(small) - allowed} detail{'' if len(small) - allowed == 1 else 's'} "
            "too small to print cleanly, coming out as smears rather than shapes",
            value=round(worst.area, 3),
            where=tuple(round(v, 2) for v in worst.center()),
        )
    ]


@rule("build_volume")
def build_volume(shape, ctx):
    """Does it fit on the printer at all."""
    size = shape.bounding_box().size
    up = Vector(*ctx.up).normalized()
    if _standing(shape, up) is None:
        got = sorted([size.X, size.Y, size.Z], reverse=True)
        fits = all(g <= b for g, b in zip(got, sorted(ctx.bed, reverse=True)))
        if not fits:
            # The box is the wrong question for a part that fits turned on the
            # plate: issue #55's 364mm tray sits on a 350mm bed at 36 degrees.
            fits = _fits_rotated(shape, ctx.bed)
        orientation = "in any orientation"
    else:
        # A stance facet fixes the build direction. The part may turn on the plate,
        # but rolling it onto another axis would put the facet in the air again.
        bed, top = _span(shape, up)
        height = top - bed
        footprint = sorted(
            _span(shape, axis)[1] - _span(shape, axis)[0]
            for axis in _bed_axes(up)
        )
        plate = sorted(ctx.bed[:2])
        got = [height, *footprint]
        fits = height <= ctx.bed[2] and (
            all(got <= available for got, available in zip(footprint, plate))
            or _fits_rotated(shape, ctx.bed, up)
        )
        orientation = "in its fixed build orientation"
    if fits:
        return []
    return [
        Finding(
            "build_volume",
            FAIL,
            f"{size.X:.0f} x {size.Y:.0f} x {size.Z:.0f}mm does not fit "
            f"{ctx.bed[0]:.0f} x {ctx.bed[1]:.0f} x {ctx.bed[2]:.0f}mm {orientation}",
            value=round(max(got), 1),
        )
    ]


def _sample_normals(face, grid=5):
    """Outward normals across a face.

    A planar face has one and it is exact. A curved face does not, and the sampling
    has to reach the ends of its parameter range: sampling cell midpoints instead
    walks a cylinder round at 45, 135, 225 and 315 degrees and never once looks
    straight down, which is the only normal an overhang check cares about. Endpoints
    included, the same grid hits 270 exactly.

    Still an approximation on a curved face, bounded by the grid spacing. Planar
    faces, which is nearly all of this library, are exact.
    """
    if face.geom_type == GeomType.PLANE:
        return [face.normal_at(face.center())]
    out = []
    for i in range(grid):
        for j in range(grid):
            try:
                spot = face.position_at(i / (grid - 1), j / (grid - 1))
                out.append(face.normal_at(spot))
            except Exception:
                continue
    return out or [face.normal_at(face.center())]


def _span(shape, up):
    """How far a shape reaches along the build direction, as (lowest, highest).

    Off the bounding box, not off the vertices. A curved face has vertices only where
    its seam is, so a cylinder's lowest vertex sits at its middle: measuring from
    vertices put the bed 8mm above the actual bottom of a cylinder, marked every face
    grounded, and turned the overhang rule off without any sign that it had happened.

    A bounding box only answers exactly along its own axes. For any other build
    direction, first put the shape into a coordinate system whose Z is `up`; its local
    Z bounds are then the exact projection rather than the conservative projection of
    the world-axis box.
    """
    if max(abs(up.X), abs(up.Y), abs(up.Z)) < 1.0 - 1e-9:
        local = Plane(origin=(0, 0, 0), z_dir=up).to_local_coords(shape)
        box = local.bounding_box()
        return box.min.Z, box.max.Z
    box = shape.bounding_box()
    corners = [
        Vector(x, y, z)
        for x in (box.min.X, box.max.X)
        for y in (box.min.Y, box.max.Y)
        for z in (box.min.Z, box.max.Z)
    ]
    reach = [c.dot(up) for c in corners]
    return min(reach), max(reach)


def _bed_axes(up):
    """Two perpendicular directions across the build plate."""
    guide = Vector(1, 0, 0) if abs(up.X) < 0.9 else Vector(0, 1, 0)
    first = up.cross(guide).normalized()
    return first, up.cross(first).normalized()


def _hull(points):
    """Convex hull of 2d points, by monotone chain."""
    pts = sorted({(round(float(x), 2), round(float(y), 2)) for x, y in points})
    if len(pts) <= 2:
        return pts

    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    out = []
    for chain in (pts, reversed(pts)):
        base = len(out)
        for p in chain:
            while len(out) - base >= 2 and turn(out[-2], out[-1], p) <= 0:
                out.pop()
            out.append(p)
        out.pop()
    return out


def _rotated_spans(points, angle):
    c, s = cos(angle), sin(angle)
    xs = [x * c - y * s for x, y in points]
    ys = [x * s + y * c for x, y in points]
    return max(xs) - min(xs), max(ys) - min(ys)


def _footprint_fits(points, plate):
    """Whether a 2d footprint fits a rectangular plate at some rotation.

    Between orientations parallel to hull edges, the vertices supporting each side
    of the bounding box stay fixed. The worst normalized span can reach its minimum
    only at one of those boundaries or where the two normalized spans cross, so those
    finite candidates give the exact answer without an angle grid.
    """
    hull = _hull(points)
    if not hull:
        return False

    quarter = pi / 2
    cuts = {0.0, quarter}
    if len(hull) > 1:
        for p, q in zip(hull, hull[1:] + hull[:1]):
            edge = atan2(q[1] - p[1], q[0] - p[0])
            cuts.add((-edge) % quarter)
    cuts = sorted(cuts)
    candidates = list(cuts)
    orientations = (plate, plate[::-1])

    for low, high in zip(cuts, cuts[1:]):
        if high - low <= 1e-12:
            continue
        mid = (low + high) / 2
        c, s = cos(mid), sin(mid)

        def x_at(p):
            return p[0] * c - p[1] * s

        def y_at(p):
            return p[0] * s + p[1] * c

        x_high, x_low = max(hull, key=x_at), min(hull, key=x_at)
        y_high, y_low = max(hull, key=y_at), min(hull, key=y_at)
        dx, dy = x_high[0] - x_low[0], x_high[1] - x_low[1]
        ex, ey = y_high[0] - y_low[0], y_high[1] - y_low[1]

        for across, deep in orientations:
            cos_term = deep * dx - across * ey
            sin_term = -deep * dy - across * ex
            if abs(cos_term) + abs(sin_term) <= 1e-12:
                continue
            crossing = atan2(-cos_term, sin_term) % pi
            if low < crossing < high:
                candidates.append(crossing)

    for angle in candidates:
        width, depth = _rotated_spans(hull, angle)
        if any(
            width <= across + 1e-6 and depth <= deep + 1e-6
            for across, deep in orientations
        ):
            return True
    return False


def _fits_rotated(shape, bed, up=None):
    """Whether the part fits the plate turned about some build axis.

    The slow path, reached only after the bounding box has already failed. The
    footprint is the hull of a tessellation rather than of the B-rep's own
    vertices, because a curved outline has vertices only at its seams.
    """
    from . import builder

    verts = builder.to_mesh(shape, 0.1).vertices
    if up is not None:
        first, second = _bed_axes(up)

        def projected(point):
            point = Vector(*point)
            return point.dot(first), point.dot(second)

        footprint = [projected(point) for point in verts]
        return _footprint_fits(footprint, bed[:2])

    for axis in range(3):
        if verts[:, axis].max() - verts[:, axis].min() > bed[2] + 1e-6:
            continue
        flat = [c for c in range(3) if c != axis]
        if _footprint_fits(verts[:, flat], bed[:2]):
            return True
    return False


def _reach(face, up):
    """How far a face protrudes, which is the smallest of its horizontal extents.

    What makes an unsupported ledge droop is how far out it goes, not how much of it
    there is. A 0.5mm ledge prints cleanly at any length, which is why raised lettering
    is not a hundred overhang failures.
    """
    across = [
        _span(face, axis)[1] - _span(face, axis)[0]
        for axis in (Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1))
        if abs(axis.dot(up)) < 0.9
    ]
    return min(across) if across else 0.0


# Height over stance width past which first-layer adhesion is holding a lever and a
# part needs fins. Provisional, sitting between a 30mm bracket on a 2mm facet that
# prints clean and a 60mm bar that does not survive without one. `stand()` grows its
# fins at the same number, so the rule and the remedy cannot drift apart.
LEVERAGE = 20


def _standing(shape, up):
    """The supported footprint width when a part stands rather than sits.

    A part printed diagonally does not have a bottom face: it stands on a deliberate
    narrow flat, the facet `stand()` cuts across its down corner, plus the pads of
    any fins it grew. Several rules were calibrated on parts that sit, and a stance
    is the case that breaks them: there is no bottom whose rim a bed bevel could
    dress, and the centre of mass is always outside a 2mm strip.

    Aspect ratio alone cannot identify it: a normally seated 4mm wall also has a long,
    narrow bottom. The cut facet has two long edges against sloped body faces which
    continue into other nonvertical faces; a bottom bevel instead ends at the vertical
    wall it dresses. Once found, all real bed faces count toward support, so generated
    fin pads widen the returned footprint. Returns None for a sitting part.
    """
    FACET = 5.0
    bed, _ = _span(shape, up)
    footing = [
        f for f in shape.faces() if _span(f, up)[1] <= bed + 1e-4 and f.area >= 4.0
    ]
    if not footing:
        return None
    neighbours = None
    facet = None
    long_edge = None
    for face in footing:
        edges = list(face.edges())
        if not edges:
            continue
        longest = max(edges, key=lambda edge: edge.length)
        length = longest.length
        if length <= 0:
            continue
        width = face.area / length
        if width > FACET or length < 3 * width:
            continue
        if neighbours is None:
            neighbours = edge_faces(shape)
        stance_edges = 0
        for edge in edges:
            if edge.length < max(2 * width, 0.8 * length):
                continue
            pair = neighbours.get(edge, [])
            if len(pair) != 2:
                continue
            other = pair[1] if pair[0] == face else pair[0]
            tilt = abs(other.normal_at(edge.center()).dot(up))
            if not 1e-4 < tilt < 0.9999:
                continue
            continues = False
            for far_edge in other.edges():
                if far_edge == edge or far_edge.length < 0.8 * edge.length:
                    continue
                far_pair = neighbours.get(far_edge, [])
                if len(far_pair) != 2:
                    continue
                beyond = far_pair[1] if far_pair[0] == other else far_pair[0]
                if beyond == face:
                    continue
                beyond_tilt = abs(beyond.normal_at(far_edge.center()).dot(up))
                if 1e-4 < beyond_tilt < 0.9999:
                    continues = True
                    break
            if continues:
                stance_edges += 1
        if stance_edges >= 2:
            facet, long_edge = face, longest
            break
    if facet is None:
        return None

    along = long_edge.tangent_at(0)
    along = (along - up * along.dot(up)).normalized()
    across = up.cross(along).normalized()

    def footprint(axis):
        spans = [_span(face, axis) for face in footing]
        return max(high for _, high in spans) - min(low for low, _ in spans)

    # Leverage acts across the facet, in the direction of the lean. Its length along
    # the corner already carries the first layer; fins extend support across it.
    return footprint(across)


def _bridged(solid, face, up, ctx):
    """The shortest span this face is supported across, or None if it is cantilevered.

    A downward face with material on both sides of it is a bridge, and a printer walks
    across a short one without help. A face with material on one side only is a
    cantilever and needs support. Both are 90 degrees to the build direction and
    nothing about the normal tells them apart, which is why the overhang angle alone
    reports a channel roof and a shelf underside as the same problem.

    Both sides get probed just outside the face and just below it, which is the same
    containment test the convexity work was checked against.
    """
    below = face.center() - up * PROBE
    best = None
    for axis in (Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1)):
        if abs(axis.dot(up)) > 0.9:
            continue
        low, high = _span(face, axis)
        here = below.dot(axis)
        ends = [
            below + axis * (low - here - PROBE),
            below + axis * (high - here + PROBE),
        ]
        if all(solid.is_inside((p.X, p.Y, p.Z)) for p in ends):
            reach = high - low
            best = reach if best is None else min(best, reach)
    return best


@rule("overhang")
def overhang(shape, ctx):
    """Downward faces the printer cannot lay down unaided.

    Angle is measured from the build direction, so a vertical wall is 0 and a flat
    ceiling is 90. Two things are deliberately not findings: a face on the bed, which
    is the first layer, and a short bridge, which a printer spans on its own. Warning
    about either is how a checker gets switched off.

    A third thing is a finding but not a fault. Where the part says it prints on
    support material, either by wrapping the feature in `supported()` or by declaring
    the whole part in its card, the finding drops to a note: still on screen, still
    carrying the angle and the area so the user can see what the supports are costing,
    but no longer something to fix. Unlike the sliver baseline, which deletes what it
    excuses, this keeps the finding, because the whole reason to say it out loud is
    that support material is a real price paid on every print rather than a one-time
    edit.

    A mark that excused nothing gets a note of its own. It means either the geometry
    was fixed and the mark outlived it, or the mark stopped landing where it used to,
    and the two are worth telling apart before somebody trusts a feature that is not
    actually covered.
    """
    up = Vector(*ctx.up).normalized()
    bed, _ = _span(shape, up)
    solid = shape.solids()[0] if shape.solids() else None
    marks = () if ctx.supports else supports.regions(shape)
    used = set()
    found = []
    for face in shape.faces():
        if _span(face, up)[1] <= bed + 1e-4:
            continue  # grounded, so it is the first layer rather than an overhang
        worst = max(
            degrees(asin(max(-1.0, min(1.0, -n.dot(up))))) for n in _sample_normals(face)
        )
        if worst <= ctx.overhang_limit + 1e-6:
            continue
        crossing = _bridged(solid, face, up, ctx) if solid else None
        if crossing is not None and crossing <= ctx.bridge_limit:
            continue  # a bridge this printer walks across
        # A polish chamfer that a diagonal stand turns to face the bed is a strip
        # `size * 1.42` wide, the same figure concave_cosmetic uses, and it prints:
        # the flanks close over it at 45 degrees. Measured at 1.32mm on a stood
        # bracket whose flat print is clean.
        droop = max(ctx.overhang_reach, 1.42 * 1.15 * ctx.cosmetic_chamfer)
        if crossing is None and _reach(face, up) <= droop:
            continue  # a ledge too shallow to droop, whatever its angle or length
        # The polish pass moves faces near a mark's edges by about a chamfer, so the
        # mark is grown by one before asking whether this face is inside it.
        spot = tuple(face.center())
        mark = supports.covering(marks, spot, ctx.cosmetic_chamfer)
        if mark is not None:
            used.add(id(mark))
        carried = ctx.supports or mark is not None
        # A marked feature quotes its own reason back, because a note the reader cannot
        # trace to a decision is one they have to go looking for the decision behind.
        on = f"on supports: {mark.why}" if mark is not None else "on supports"
        if crossing is not None:
            severity, value = (NOTE if carried else WARN), crossing
            if carried:
                message = f"{crossing:.0f}mm bridge over {face.area:.1f}mm2, {on}"
                plain = (
                    f"a {crossing:.0f}mm gap, held up by support material you break "
                    "off after printing"
                )
            else:
                message = (
                    f"{crossing:.0f}mm bridge over {face.area:.1f}mm2, "
                    f"past the {ctx.bridge_limit:.0f}mm this printer spans"
                )
                plain = (
                    f"a {crossing:.0f}mm gap to cross in mid-air; this printer "
                    f"holds a span up to {ctx.bridge_limit:.0f}mm"
                )
        else:
            severity, value = (NOTE if carried else FAIL), worst
            if carried:
                message = f"{worst:.0f}deg over {face.area:.1f}mm2, {on}"
                plain = (
                    f"an underside leaning {worst:.0f} degrees out, held up by support "
                    "material you break off after printing"
                )
            else:
                message = (
                    f"{worst:.0f}deg unsupported over {face.area:.1f}mm2, "
                    f"limit {ctx.overhang_limit:.0f}deg"
                )
                plain = (
                    f"an underside leaning {worst:.0f} degrees out. Past "
                    f"{ctx.overhang_limit:.0f} it droops as it prints"
                )
        found.append(
            Finding(
                "overhang",
                severity,
                message,
                plain=plain,
                value=round(value, 1),
                where=tuple(round(v, 2) for v in face.center()),
            )
        )
    for mark in marks:
        if id(mark) in used:
            continue
        low, high = mark.box()
        middle = tuple((low[i] + high[i]) / 2 for i in range(3))
        found.append(
            Finding(
                "overhang",
                NOTE,
                f"nothing here needed supports: {mark.why}",
                plain=f"marked as needing support material, but nothing under it does: "
                f"{mark.why}",
                where=tuple(round(v, 2) for v in middle),
            )
        )
    return found


@rule("floating")
def floating(shape, ctx):
    """A region whose first layer would be laid on air.

    The overhang rule judges faces one at a time by angle, and a floating region can
    present nothing steeper than the limit: stand an L on the end of one leg and the
    other leg's tip hangs in space with every face at exactly 45 degrees. What gives
    it away is the shape of the low point: a vertex above the bed with every edge
    rising away from it. Somewhere to sit is what a first layer needs, and angle
    cannot measure it.

    Supported means one of two things, and both are needed. An edge running further
    down: the second-lowest corner of a stood slab has air straight below it, but its
    silhouette descends to the facet and every layer rests on the one before. Or
    material straight below: the calipers holder's corbel corner has every edge
    rising away from it and sits directly on the body underneath, which is what
    flagged the edge test as insufficient when this rule first ran on the catalog.
    The face gate mirrors the overhang rule's: a low point whose downward faces are
    all chamfer-band strips is a polish artifact, not a region.
    """
    up = Vector(*ctx.up).normalized()
    bed, _ = _span(shape, up)
    droop = max(ctx.overhang_reach, 1.42 * 1.15 * ctx.cosmetic_chamfer)

    def key(p):
        return (round(p.X, 4), round(p.Y, 4), round(p.Z, 4))

    # Directions leaving each vertex, off the edge tangents rather than the chords,
    # keyed by position: the kernel hands back fresh objects on every call, so
    # identity would never match anything.
    leaving = {}
    for edge in shape.edges():
        try:
            ends = (edge.position_at(0), edge.position_at(1))
            tangents = (edge.tangent_at(0), -edge.tangent_at(1))
        except Exception:
            continue
        for point, tangent in zip(ends, tangents):
            leaving.setdefault(key(point), []).append(tangent)
    faces_at = {}
    for face in shape.faces():
        for v in face.vertices():
            faces_at.setdefault(key(Vector(v.X, v.Y, v.Z)), []).append(face)
    solid = shape.solids()[0] if shape.solids() else None
    found = []
    for spot, directions in leaving.items():
        here = Vector(*spot)
        rise = here.dot(up) - bed
        if rise <= 1e-4:
            continue  # on the bed, which is the one place a low point belongs
        if any(d.dot(up) < -1e-6 for d in directions):
            continue  # material runs further down, so this is not the low point
        below = here - up * 0.5
        if solid and solid.is_inside((below.X, below.Y, below.Z)):
            continue  # sitting on material, which is support however the edges run
        # A bead anchored on both sides at its own layer is a bridge, and a fin's
        # tine is exactly one: it starts in air and prints anyway, walked across
        # from the part to the fin. Probed a bead out each way, just above the low
        # point, so a floating tip, anchored on one side at best, stays a finding.
        level = here + up * 0.15
        horiz = [a for a in (Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1)) if abs(a.dot(up)) < 0.9]
        def held(p):
            return solid.is_inside((p.X, p.Y, p.Z))

        if solid and any(held(level + d * 1.2) and held(level - d * 1.2) for d in horiz):
            continue
        wide = [
            f
            for f in faces_at.get(spot, [])
            if min(n.dot(up) for n in _sample_normals(f)) < -0.03 and _reach(f, up) > droop
        ]
        if not wide:
            continue
        found.append(
            Finding(
                "floating",
                FAIL,
                f"a region's first layer sits on air, {rise:.1f}mm up with nothing below",
                value=round(rise, 1),
                where=tuple(round(v, 2) for v in here),
            )
        )
    return found


@rule("hole_ceiling")
def hole_ceiling(shape, ctx):
    """A blind hole's flat ceiling with a smaller hole continuing through it.

    The counterbore case: a screw pocket printed mouth-down floats the shelf its head
    bears on, and the through hole's first rim is a circle drawn on air. The overhang
    rule cannot see it, deliberately: a ceiling with material all around reads as a
    bridge, and a bridge the printer walks across is not a finding. What a bridge
    cannot carry cleanly is a hole rim inside it, laid on sagging lines with nothing
    under the perimeter, which is why this looks for the piercing rather than the span.

    Found on the B-rep directly: a horizontal downward face with an inner wire is a
    pierced ceiling. The one thing the wire alone cannot tell is what pierced it, so
    the probe above settles it: void continuing up is a hole and a finding; material
    is a boss hanging through, which carries its own rim. The remedy is `counterbore()`,
    which steps the transition so each layer bridges only what the one before it laid,
    and whose own stepped stack leaves no pierced ceiling for this rule to find.
    """
    up = Vector(*ctx.up).normalized()
    bed, _ = _span(shape, up)
    solid = shape.solids()[0] if shape.solids() else None
    found = []
    for face in shape.faces():
        if face.geom_type != GeomType.PLANE:
            continue
        if face.normal_at(face.center()).dot(up) > -0.97:
            continue  # not a flat ceiling
        if _span(face, up)[0] <= bed + 1e-4:
            continue  # the first layer, where every mouth belongs
        for wire in face.inner_wires():
            # The box centre, not wire.center(): a curve's own centre is its centre
            # of mass, which for a circle is a point on the rim, not the middle.
            centre = wire.bounding_box().center()
            width = min(
                _span(wire, axis)[1] - _span(wire, axis)[0]
                for axis in (Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1))
                if abs(axis.dot(up)) < 0.9
            )
            # Probe just inside the wire rather than at its box centre. A hollow boss
            # carries the rim as surely as a solid one, but its centre is still void
            # and looks exactly like a hole. `_into_face` finds the material side of
            # the boundary, so its opposite is the region the wire encloses.
            carried = []
            if solid:
                step = min(0.05, width / 4)
                for edge in wire.edges():
                    try:
                        point = edge.position_at(0.5)
                        inward = -_into_face(face, point, edge.tangent_at(0.5))
                        above = point + inward * step + up * 0.02
                        carried.append(solid.is_inside((above.X, above.Y, above.Z)))
                    except Exception:
                        continue
            if carried and all(carried):
                continue  # a solid or hollow boss through the ceiling, not a hole
            found.append(
                Finding(
                    "hole_ceiling",
                    WARN,
                    f"a {width:.1f}mm hole rim would print on air over the opening "
                    f"below; stepped bridging layers are the fix",
                    plain=f"the top of a {width:.1f}mm hole starts in mid-air, with the "
                    "pocket open underneath it",
                    value=round(width, 1),
                    where=tuple(round(v, 2) for v in centre),
                )
            )
    return found


@rule("stability")
def stability(shape, ctx):
    """Will it stand on the bed, or tip while printing."""
    up = Vector(*ctx.up).normalized()
    bed, top = _span(shape, up)
    footing = [f for f in shape.faces() if _span(f, up)[1] <= bed + 1e-4]
    if not footing:
        return [Finding("stability", FAIL, "nothing flat to stand on")]
    stance = _standing(shape, up)
    if stance is not None:
        # Standing on a facet, the centre of mass is always outside it and the part
        # is held by first-layer adhesion, not balance. What adhesion cannot hold is
        # leverage; fins widen the stance, which is how growing them clears this.
        if top - bed > LEVERAGE * stance:
            return [
                Finding(
                    "stability",
                    WARN,
                    f"stands {top - bed:.0f}mm tall on a {stance:.1f}mm facet, "
                    "more than adhesion holds; a support fin is the fix",
                    plain=f"{top - bed:.0f}mm tall balanced on a {stance:.1f}mm strip. "
                    "It will come off the plate mid-print",
                    value=round((top - bed) / stance, 1),
                )
            ]
        return []
    com = shape.center(CenterOf.MASS)
    axes = [a for a in (Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1)) if abs(a.dot(up)) < 0.9]
    for axis in axes:
        reach = [end for f in footing for end in _span(f, axis)]
        here = com.dot(axis)
        if not min(reach) <= here <= max(reach):
            return [
                Finding(
                    "stability",
                    WARN,
                    "center of mass falls outside the footprint, it will tip",
                    plain="top-heavy: its weight sits outside what it stands on, "
                    "so it tips over",
                    where=tuple(round(v, 2) for v in com),
                )
            ]
    return []


def _sharp_plan_corners(face, up, radius):
    """Where a face's outline turns a corner's worth too fast for a `radius` round.

    Sharpness here is turn per length of perimeter, not vertex angle, because a 1mm
    polish chamfer is still the corner it dresses: the outline turns its full 90
    degrees within a couple of millimetres either way. Sampled as a polyline so a
    true vertex, a chamfered corner and an undersized fillet all answer the same
    question. The window is the perimeter a `radius` round spends turning 60
    degrees, so anything rounded at least that generously stays under the bar
    exactly. Concave corners turn against the outline's orientation and are
    skipped: an inside corner has material outboard of it holding it down.
    """
    first, second = _bed_axes(up)
    wire = face.outer_wire()
    n = max(int(wire.length), 24)
    pts = [wire.position_at(i / n) for i in range(n)]
    flat = [(p.dot(first), p.dot(second)) for p in pts]
    spacing = wire.length / n
    turns = []
    for i in range(n):
        ax, ay = flat[i]
        bx, by = flat[(i + 1) % n]
        cx, cy = flat[(i + 2) % n]
        ux, uy = bx - ax, by - ay
        vx, vy = cx - bx, cy - by
        turns.append(atan2(ux * vy - uy * vx, ux * vx + uy * vy))
    orient = 1.0 if sum(turns) >= 0 else -1.0
    corner = pi / 3
    window = max(1, round(radius * corner / spacing))
    hits = [
        i
        for i in range(n)
        if orient * sum(turns[(i + j) % n] for j in range(window)) >= corner - 1e-9
    ]
    if not hits:
        return []
    # Consecutive windows over one corner are one corner. Clusters are gaps wider
    # than the window itself, and the last cluster can wrap into the first.
    clusters = [[hits[0]]]
    for i in hits[1:]:
        if i - clusters[-1][-1] <= window:
            clusters[-1].append(i)
        else:
            clusters.append([i])
    if len(clusters) > 1 and (hits[0] + n) - clusters[-1][-1] <= window:
        clusters[0] = clusters.pop() + clusters[0]
    out = []
    for cluster in clusters:
        peak = max(
            (j % n for i in cluster for j in range(i, i + window)),
            key=lambda j: orient * turns[j],
        )
        out.append(pts[(peak + 1) % n])
    return out


# Cooling contraction by material, in percent. `warp_area` was calibrated on a PLA
# plate, so PLA is the unit: a plastic that contracts five times as much peels the same
# corners off a fifth of the area. The figures are the guides' (Prusa's material pages
# put ABS at 1-2% shrink and flatly refuse bed-covering ABS, ASA or PC parts; Hubs
# gives 0.2-1% across materials), rounded to one calibration point per family.
SHRINK = {
    "pla": 0.3,
    "petg": 0.3,
    "abs": 1.5,
    "asa": 1.5,
    "pc": 2.0,
    "pp": 2.0,
}


@rule("warp_risk")
def warp_risk(shape, ctx):
    """A first layer big enough for cooling contraction to peel its corners.

    Every layer shrinks as it cools and pulls toward the middle of the part. On a
    small part first-layer adhesion wins. On a big flat plate the accumulated pull
    beats it, and it lets go where the pull concentrates: a sharp plan corner,
    farthest from the middle and holding on at a point. The design-side fixes are in
    the outline, which is why this is a CAD finding and elephant's foot is not:
    round the vertical corners past `warp_radius` so the peel front is a curve, and
    prefer a ribbed floor to a solid slab, which halves what contracts. The brim is
    the slicer's share and the message says so, but a brim on sharp corners is
    treating the symptom.

    Only faces that are themselves plate-sized get their corners read: the ribs
    under a properly ribbed floor are skinny rectangles full of sharp corners, and
    each pulls far too little to peel.
    """
    up = Vector(*ctx.up).normalized()
    bed, _ = _span(shape, up)
    footing = [f for f in shape.faces() if _span(f, up)[1] <= bed + 1e-4]
    area = sum(f.area for f in footing)
    pull = SHRINK[(ctx.material or "pla").lower()] / SHRINK["pla"]
    if area * pull <= ctx.warp_area:
        return []
    sharp = [
        point
        for face in footing
        if face.area * pull >= ctx.warp_area / 2
        for point in _sharp_plan_corners(face, up, ctx.warp_radius)
    ]
    if not sharp:
        return []
    centre = sum((f.center() * f.area for f in footing), Vector(0, 0, 0)) / area
    worst = max(sharp, key=lambda point: (point - centre).length)
    count = len(sharp)
    made_of = f" in {ctx.material.upper()}, which contracts {pull:.0f}x what PLA does" if pull > 1 else ""
    plastic = ctx.material.upper() if pull > 1 else "The plastic"
    return [
        Finding(
            "warp_risk",
            WARN,
            f"{count} sharp corner{'' if count == 1 else 's'} on a {area:.0f}mm2 "
            f"first layer{made_of}; contraction peels them as the print cools. Round "
            f"plan corners past {ctx.warp_radius:.0f}mm, rib the floor instead of a "
            f"solid slab, and print with a brim",
            plain=f"a big flat base with sharp corners. {plastic} shrinks as it "
            "cools and curls them off the bed; rounded corners and a brim keep it down",
            value=count,
            where=tuple(round(v, 2) for v in worst),
        )
    ]


def _pins(shape, up):
    """Free-standing vertical cylinders, as (diameter, height, top_centre) each.

    Faces are grouped by axis and radius because a boolean routinely splits one
    cylinder into two half faces, and only a group whose faces close the full circle
    is a pin: anything merged into a wall loses part of its wrap to the join, and a
    fillet or a rounded corner never had it. A hole is the same surface with its
    normal pointing inward, so a group with any inward face is not a pin either.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    groups = {}
    for face in shape.faces():
        if face.geom_type != GeomType.CYLINDER:
            continue
        surf = BRepAdaptor_Surface(face.wrapped)
        cyl = surf.Cylinder()
        axis = Vector(cyl.Axis().Direction().X(), cyl.Axis().Direction().Y(), cyl.Axis().Direction().Z())
        if abs(axis.dot(up)) < 0.99:
            continue  # lying down, printed as solid strands rather than stacked rings
        spot = cyl.Location()
        point = Vector(spot.X(), spot.Y(), spot.Z())
        foot = point - up * point.dot(up)
        key = (round(foot.X, 2), round(foot.Y, 2), round(foot.Z, 2), round(cyl.Radius(), 3))
        sample = face.position_at(0.5, 0.5)
        radial = sample - foot - up * sample.dot(up)
        low, high = _span(face, up)
        wrap = abs(surf.LastUParameter() - surf.FirstUParameter())
        entry = groups.setdefault(
            key,
            {
                "wrap": 0.0,
                "low": low,
                "high": high,
                "out": True,
                "foot": foot,
                "radius": cyl.Radius(),
            },
        )
        entry["wrap"] += wrap
        entry["low"] = min(entry["low"], low)
        entry["high"] = max(entry["high"], high)
        entry["out"] &= face.normal_at(sample).dot(radial) > 0
    first, second = _bed_axes(up)
    out = []
    for entry in groups.values():
        if not entry["out"] or entry["wrap"] < 2 * pi - 0.05:
            continue
        radius = entry["radius"]
        top = entry["foot"] + up * entry["high"]
        # A standoff between two bodies has the same full cylindrical wrap as a pin,
        # but opens into material beyond its radius instead of ending in a free tip.
        above = top + up * PROBE
        if any(
            shape.is_inside(above + across * (radius + PROBE))
            for across in (first, -first, second, -second)
        ):
            continue
        out.append((2 * radius, entry["high"] - entry["low"], top))
    return out


@rule("pin")
def pin(shape, ctx):
    """A free-standing pin too thin to be more than perimeters.

    Under 5mm across there is no room inside the perimeters for infill, so a pin is
    walls with nothing between them, loaded in bending at the one place FDM is
    weakest, its base weld. Under 3mm the nozzle is re-melting what it laid one ring
    ago and the pin may not survive its own printing. Only slender pins are the
    problem: a stub no taller than twice its diameter has nothing to lever with,
    which is why a chamfered boss or a locating nub never fires this.
    """
    up = Vector(*ctx.up).normalized()
    found = []
    for dia, height, top in _pins(shape, up):
        if dia >= 5.0 or height < 2 * dia:
            continue
        if dia < 3.0:
            severity, because = FAIL, "under 3mm it may not print at all"
        else:
            severity, because = WARN, "perimeter-only, weakest at its base weld"
        found.append(
            Finding(
                "pin",
                severity,
                f"a {dia:.1f}mm pin standing {height:.0f}mm, {because}. Thicken it "
                f"past 5mm, or model the hole and press in a metal pin",
                plain=f"a printed peg only {dia:.1f}mm across. It prints as a thin "
                "tube and snaps off at the base",
                value=round(dia, 1),
                where=tuple(round(v, 2) for v in top),
            )
        )
    return found


# --- printer profiles --------------------------------------------------------

PRINTERS = pathlib.Path(__file__).parent / "printers.toml"
PRINTER_FILE = "printer.toml"  # optional, at the project root, like measurements.toml


def global_file():
    """~/.config/nurb/config.toml, the machine's standing answers.

    A printer is a fact about the workshop, not the project, so it is named once
    here instead of in every printer.toml. Same schema as printer.toml, read fresh
    each call because tests move it with XDG_CONFIG_HOME.

    Deliberately ~/.config on Windows too, rather than %APPDATA%: the desktop
    app's sandbox and docs both point here, and one location on every platform
    beats the native convention.
    """
    import os

    base = os.environ.get("XDG_CONFIG_HOME") or pathlib.Path.home() / ".config"
    return pathlib.Path(base) / "nurb" / "config.toml"


def _read_toml(file, label):
    import tomllib

    if not file.is_file():
        return {}
    try:
        return tomllib.loads(file.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{label}: not valid TOML ({exc})") from exc


def profile_choice(root):
    """The profile a project resolves to and where it was named: the project's
    printer.toml, then the global config. (None, None) when neither says."""
    block = _read_toml(pathlib.Path(root) / PRINTER_FILE, PRINTER_FILE)
    if block.get("profile"):
        return block["profile"], PRINTER_FILE
    home = _read_toml(global_file(), str(global_file()))
    if home.get("profile"):
        return home["profile"], "global"
    return None, None


def profiles():
    """The shipped printer profiles: machine facts, keyed by name."""
    import tomllib

    return tomllib.loads(PRINTERS.read_text(encoding="utf-8"))


def choose_profile(root, name):
    """Name this project's machine in its printer.toml, and say where it landed.

    The viewer asks for this when a print estimate needs a machine and the project
    has never named one: a picker beats printing what the user should have written,
    and the choice belongs on disk where every other command reads it from.

    Only the `profile` line is touched. A printer.toml is often hand-written with
    comments explaining a bed size, so this rewrites an existing line in place and
    otherwise inserts one above the first table, never appending, which would put a
    top-level key inside whatever table happens to be last.
    """
    import re

    have = profiles()
    if name not in have:
        raise ValueError(f"no printer profile called {name!r}. have: {', '.join(sorted(have))}")
    target = pathlib.Path(root) / PRINTER_FILE
    line = f'profile = "{name}"'
    text = target.read_text(encoding="utf-8") if target.is_file() else ""
    found = re.search(r"(?m)^[ \t]*profile[ \t]*=.*$", text)
    if found:
        text = text[: found.start()] + line + text[found.end() :]
    elif not text.strip():
        text = line + "\n"
    else:
        table = re.search(r"(?m)^[ \t]*\[", text)
        at = table.start() if table else len(text)
        head, tail = text[:at].rstrip("\n"), text[at:]
        text = f"{head}\n\n{line}\n" + (f"\n{tail}" if tail else "")
    target.write_text(text, encoding="utf-8")
    return target


# Keys a shipped profile carries that are facts about the machine rather than settings
# a rule reads. Named once because `_apply` deliberately refuses a key the Context does
# not have, which is what catches a typo, and an exclusion spelled in two places is how
# that protection quietly stops covering one of them.
NOT_SETTINGS = ("slicer",)

# Settings a card may set and a machine may not. `supports` says this part is worth
# printing on support material and cleaning up afterwards, which is a judgement about
# one part and never a fact about the printer. Allowed machine-wide it would excuse
# every cantilever in every project on the machine, from a file that nothing prints the
# contents of, so the guard is worth the asymmetry with `min_wall`: a tighter min_wall
# machine-wide only makes the rules stricter, and this only makes them looser.
PART_ONLY = ("supports",)


def machine_only(block):
    """A profile with the non-setting facts removed, ready for `_apply`."""
    return {k: v for k, v in block.items() if k not in NOT_SETTINGS}


def slicer_name(root, name=None):
    """What a slicer calls this project's machine, and the nurb profile it came from.

    Separate from `printer` because a Context is check settings and this is neither a
    setting nor a check; it is the one fact about the machine that only `nurb slice`
    needs. (None, None) when no profile is chosen, which is a question to ask rather
    than a default to invent: slicing the wrong machine's bed is worse than not slicing.
    """
    name = name or profile_choice(root)[0]
    if not name:
        return None, None
    have = profiles()
    if name not in have:
        raise ValueError(f"no printer profile called {name!r}. have: {', '.join(sorted(have))}")
    return have[name].get("slicer"), name


def _project_root(part_path):
    """The project a part belongs to, by the same rule the builder uses."""
    path = pathlib.Path(part_path).resolve()
    return path.parent.parent if path.parent.name == "parts" else path.parent


def printer(root, name=None):
    """The machine's Context: a shipped profile, then the global config, then the
    project's printer.toml.

    A bed size belongs to the machine, not to a part, so it is picked once here
    rather than written onto every card. Either file names a shipped profile and can
    override any check setting machine-wide; the project's wins over the global's,
    and a card still wins for what its part has justified, because `_apply` runs the
    card on top of this.
    """
    ctx = Context()
    home = _read_toml(global_file(), str(global_file()))
    block = _read_toml(pathlib.Path(root) / PRINTER_FILE, PRINTER_FILE)
    name = name or block.get("profile") or home.get("profile")
    if name:
        have = profiles()
        if name not in have:
            raise ValueError(
                f"no printer profile called {name!r}. have: {', '.join(sorted(have))}"
            )
        _apply(ctx, {"printer": machine_only(have[name])}, f"profile {name!r}")
    # profile is resolved above; export is a workflow preference cmd_export reads
    for settings_block, where in ((home, str(global_file())), (block, PRINTER_FILE)):
        facts = {k: v for k, v in settings_block.items() if k not in ("profile", "export")}
        # Checked here rather than in `_apply`, which is also what a card goes through
        # and where the key is legal. `_apply` merges [printer] and [part] into one
        # dict, so by the time it runs there is nothing left to tell them apart.
        for key in PART_ONLY:
            if key in facts:
                raise ValueError(
                    f"{where}: {key} is a decision about one part, not about the "
                    f"machine. Put it in that part's card, under [part]."
                )
        _apply(ctx, {"printer": facts}, where)
    return ctx


# --- per part settings -------------------------------------------------------

CARD_SETTINGS = "toml"  # the fence a card uses to carry them


def settings(part_path):
    """The card's settings block, parsed. An empty dict when there is none."""
    import tomllib

    card = pathlib.Path(part_path).with_suffix(".md")
    if not card.is_file():
        return {}
    text = card.read_text(encoding="utf-8")  # cards say mm², so never the locale default
    opening = f"```{CARD_SETTINGS}"
    if opening not in text:
        return {}
    block = text.split(opening, 1)[1].split("```", 1)[0]
    try:
        return tomllib.loads(block)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{card.name}: settings block is not valid TOML ({exc})") from exc


def _apply(ctx, block, where):
    ctx.accepted = {**ctx.accepted, **block.get("accepted", {})}
    tunables = {**block.get("printer", {}), **block.get("part", {})}
    for field_name, value in tunables.items():
        if not hasattr(ctx, field_name):
            raise ValueError(
                f"{where}: no printer setting called {field_name!r}. "
                f"have: {', '.join(sorted(vars(Context())))}"
            )
        setattr(ctx, field_name, tuple(value) if isinstance(value, list) else value)
    if ctx.material is not None:
        ctx.material = str(ctx.material).lower()
        if ctx.material not in SHRINK:
            raise ValueError(
                f"{where}: no material called {ctx.material!r}. "
                f"have: {', '.join(sorted(SHRINK))}"
            )
    # Every other setting is a number the rules compare against, so a wrong type gives
    # itself away the moment one runs. This one is only ever tested for truth, and TOML
    # will hand over the string "false" as readily as the boolean, which would switch
    # the overhang rule off while looking in the card like it was switched on.
    if not isinstance(ctx.supports, bool):
        raise ValueError(
            f"{where}: supports is true or false, not {ctx.supports!r}."
        )
    return ctx


def from_card(part_path, base=None):
    """Read a part's check settings out of its card.

    The card is where a part records what it has already justified, so a known
    finding stays silent and a new one is a regression. It lives with the design
    notes rather than in a file of its own, because the number is only meaningful
    next to the sentence explaining why it is allowed.

    A card with no settings block is normal and means no findings are excused.
    """
    card = pathlib.Path(part_path).with_suffix(".md")
    base = base or printer(_project_root(part_path))
    return _apply(base, settings(part_path), card.name)


def configurations(part_path, base=None):
    """Every configuration a part ships, as (name, overrides, ctx).

    The first is always the part itself at its declared defaults. The rest come from
    `[variants.<name>]` blocks in the card, each carrying the overrides that make it
    and whatever it has justified on its own.

    Variants exist because four Notch catalog entries are one part flexed, not new
    geometry: the utility hooks are the scissors hook with a wider cradle, and two of
    the three gridfinity shelves are the archetype at another grid size. Copying the
    function into a file per catalog entry would put the same geometry in four places
    and let them drift. A variant is a name, some overrides, and its own baselines,
    which is all a catalog entry ever was.
    """
    stem = pathlib.Path(part_path).stem
    card = pathlib.Path(part_path).with_suffix(".md")
    block = settings(part_path)
    base = base or printer(_project_root(part_path))

    def fresh():
        return _apply(replace(base), block, card.name)

    out = [(stem, {}, fresh())]
    for name, variant in block.get("variants", {}).items():
        extra = set(variant) - {"params", "accepted", "part", "printer", "note"}
        if extra:
            raise ValueError(
                f"{card.name}: variant {name} has {', '.join(sorted(extra))} at the top "
                f"level. Parameter overrides go under [variants.{name}.params]."
            )
        out.append((name, dict(variant.get("params", {})), _apply(fresh(), variant, card.name)))
    return out


def projection(shape, ctx):
    """How far a part reaches out, how much back it hangs on, and the ratio. None if it
    is not cantilevered off a wall, which a part declares by naming which way it reaches.

    Public because the card prints this number and the rule judges it. Computing it twice
    would leave a card and a check that agree today and drift later.
    """
    if ctx.forward is None:
        return None
    low, high = _span(shape, Vector(*ctx.forward).normalized())
    floor, ceiling = _span(shape, Vector(*ctx.up).normalized())
    reach, height = high - low, ceiling - floor
    if height <= 0:
        return None
    return reach, height, reach / height


@rule("projection_ratio")
def projection_ratio(shape, ctx):
    """How far a wall-mounted part reaches out against how much wall it hangs on.

    Past a point the fix is a taller back, not a bigger gusset: the load is levering
    against the mount and no amount of bracing under the shelf changes that. Only
    meaningful for something cantilevered off a wall, so a part opts in by saying
    which way it reaches.
    """
    reaching = projection(shape, ctx)
    if reaching is None:
        return []
    reach, height, ratio = reaching
    if ratio <= ctx.projection_limit:
        return []
    return [
        Finding(
            "projection_ratio",
            WARN,
            f"reaches {reach:.0f}mm on a {height:.0f}mm back, ratio {ratio:.2f}. "
            f"past {ctx.projection_limit:.1f} the fix is a taller back, not more gusset",
            plain=f"sticks out {reach:.0f}mm from a mount only {height:.0f}mm tall. "
            "That leverage sags under load, or snaps",
            value=round(ratio, 2),
        )
    ]


@rule("bed_bevel")
def bed_bevel(shape, ctx):
    """Polish laid on the edges that meet the build plate.

    A chamfer down there buys nothing and costs a mess: it turns the first layer into
    a knife edge that squashes, and on a mount-facing part it stops the thing sitting
    flat.

    A tilted face touching the bed is not always a bevel, which this rule assumed and
    the calipers holder disproved. The doctrine's corbel is a 45 degree underside, and
    where it lands on the plate rather than dying into the body it is exactly such a
    face: structure, prescribed, and 46mm2 of it.

    What separates them is how far the face rises off the bed, and a bottom chamfer's
    rise is its size exactly. Measured: 1.00, 2.00 and 3.00mm for chamfers of those
    sizes, against 4.29mm for the corbel. Rise is independent of the edge's path: a 1mm
    chamfer around a 20mm cylinder is still 1mm high even though its plan-view bounding
    box is 20mm in both directions. The limit is three times the polish size because the
    largest chamfer this doctrine puts anywhere is the 3mm structural relief, and the
    smallest corbel starts with a 4 to 6mm vertical tip.
    """
    up = Vector(*ctx.up).normalized()
    bed, _ = _span(shape, up)
    if _standing(shape, up) is not None:
        # Standing on a facet, so every face at the plate is deliberately tilted and
        # there is no bottom whose rim a bevel could dress. A 4mm wall stood at 45
        # rises 2.83mm, square in the chamfer band, and prints fine: rise cannot tell
        # it from a bevel, but the stance can.
        return []
    found = []
    for face in shape.faces():
        low, high = _span(face, up)
        if low > bed + 1e-4:
            continue  # does not reach the plate
        if high - low > 3 * ctx.cosmetic_chamfer:
            continue  # rises too far to be a chamfer band, so it is structure
        for normal in _sample_normals(face):
            tilt = abs(normal.dot(up))
            if 0.03 < tilt < 0.97:  # neither lying on the plate nor standing on it
                found.append(
                    Finding(
                        "bed_bevel",
                        WARN,
                        f"{degrees(asin(min(1.0, tilt))):.0f}deg face meets the build "
                        f"plate over {face.area:.1f}mm2, which is polish on the first layer",
                        plain=f"a chamfer along {face.area:.0f}mm2 of the bottom edge, "
                        "where it costs the first layer its grip on the plate",
                        value=round(face.area, 2),
                        where=tuple(round(v, 2) for v in face.center()),
                    )
                )
                break
    return found


@rule("concave_cosmetic")
def concave_cosmetic(shape, ctx):
    """Polish laid into an inside corner instead of across an outside one.

    A cosmetic chamfer belongs on a convex edge, where it takes a sharp corner off. Run
    over a concave one it does the opposite: it adds a thin wedge into the corner,
    which prints as a feather edge and collects stress where the part is already
    weakest. A concave junction that needs relieving wants a deliberate structural
    chamfer sized for the load, not the polish pass.

    Found by shape rather than by trying to identify chamfers: a strip about as wide as
    the polish pass makes, whose long edges are all concave, is one. Width comes from
    area over perimeter, which is the honest measure for a strip and does not care how
    the strip is oriented.

    **About as wide as the polish pass makes, not merely narrow.** A chamfer of length s
    across a right-angled corner leaves a strip s * sqrt(2) wide, so the window is that
    figure with a little headroom, and the limit was twice it until two parts showed
    what twice costs. A 2mm structural chamfer, which is what the doctrine prescribes
    for a concave junction in thin material, leaves a 2.6mm strip; the 2mm of wall left
    standing between two of them measures 1.9mm. Both sat under a 2.8mm limit, so the
    rule fired six times at `mount_tape_measure` and again at `mount_akrobin_rail`, at
    the exact geometry its own message tells you to use. A deliberate relief is bigger
    than polish, and being bigger is the only thing that distinguishes it.

    The cost is a polish chamfer in a shallow concave junction, past about 105 degrees,
    where the strip a 1mm chamfer leaves is wide enough to read as deliberate. That is
    the right way round to be wrong: `polish_edges` vetoes concave edges outright, so
    this rule is the backstop for a part that rolls its own selector, and a backstop
    that cries wolf at correct geometry gets switched off.
    """
    neighbours = edge_faces(shape)
    limit = ctx.cosmetic_chamfer * 1.42 * 1.15
    found = []
    for face in shape.faces():
        if face.geom_type != GeomType.PLANE:
            continue
        perimeter = sum(e.length for e in face.edges())
        if perimeter <= 0:
            continue
        width = 2 * face.area / perimeter
        if width > limit:
            continue
        long_edges = [e for e in face.edges() if e.length > width * 1.5]
        if len(long_edges) < 2:
            continue
        here = face.normal_at(face.center())
        verdicts, oblique = [], []
        for edge in long_edges:
            pair = neighbours.get(edge, [])
            if len(pair) != 2:
                continue
            verdicts.append(is_convex(edge, *pair))
            # Compared by topology, not by `is`: shape.faces() hands back fresh
            # objects each call, so identity would always pick this face itself and
            # every junction would look oblique.
            other = pair[1] if pair[0] == face else pair[0]
            # A bevel leans against what it joins. A pocket floor is square to its
            # walls, and a pocket is not polish however narrow it is.
            oblique.append(abs(here.dot(other.normal_at(edge.center()))) > 0.3)
        if verdicts and not any(verdicts) and oblique and all(oblique):
            found.append(
                Finding(
                    "concave_cosmetic",
                    WARN,
                    f"{width:.1f}mm strip sitting in a concave junction over "
                    f"{face.area:.1f}mm2, which is polish where a structural chamfer belongs",
                    plain=f"a {width:.1f}mm cosmetic chamfer tucked into an inside "
                    "corner, where it thins the joint instead of tidying an edge",
                    value=round(width, 2),
                    where=tuple(round(v, 2) for v in face.center()),
                )
            )
    return found


def _probes(face, grid=2):
    """Points across a face with the outward normal at each."""
    spots = [face.center()]
    if face.geom_type != GeomType.PLANE or face.area > 25:
        # Inset from the boundary on purpose. A probe sitting on a face's own edge
        # measures the distance to whatever is around the corner, which is not a wall.
        for i in range(grid):
            for j in range(grid):
                try:
                    spots.append(
                        face.position_at((i + 1) / (grid + 1), (j + 1) / (grid + 1))
                    )
                except Exception:
                    continue
    out = []
    for spot in spots:
        try:
            out.append((spot, face.normal_at(spot)))
        except Exception:
            continue
    return out


def _sphere_at(shape, point, outward, chord):
    """The largest sphere tangent to the solid at `point`, as a diameter, or None.

    The shrinking ball: start at half the ray's chord, ask the kernel for the nearest
    boundary point to the center, and where something is nearer than the radius, shrink
    to the sphere through it. Distances are exact B-rep queries, so this stays a check
    on the solid rather than on a mesh, and it converges in a handful of steps because
    the tangency update jumps straight to the answer rather than bisecting toward it.

    None means the far contact was a graze rather than a wall. The contact normal comes
    free, as (q - c) / r, and it gets the same 0.3 floor the ray's exit filter uses,
    with the same meaning: a measurement has to leave through a surface facing back at
    it. Without this, a shallow depression reads as a thin section of whatever it is
    pressed into: the scraper's detent dimple measured 1.07mm sitting in a 2.3mm web,
    between two surfaces bounding the same air.
    """
    inward = -outward
    r = chord / 2
    w = None
    for _ in range(12):
        center = point + inward * r
        d, q, _ = shape.distance_to_with_closest_points(center)
        if d >= r - 1e-5:
            break
        w = point - q
        if w.length < 1e-6:
            return None  # pinned at the tangent point, which is curvature, not a wall
        denom = 2 * w.dot(outward)
        if denom <= 1e-9:
            return None  # the contact is behind the tangent plane, nothing to measure
        grown = w.dot(w) / denom
        if grown >= r - 1e-6:
            break
        r = grown
    if w is not None and w.dot(w) / (2 * r * r) - 1 <= 0.3:
        return None
    return 2 * r


@rule("min_wall")
def min_wall(shape, ctx):
    """The thinnest section in the solid: a ray cast, corrected by an inscribed sphere
    wherever the correction could change the verdict.

    The ray is exact on the flat parallel walls that make up most of a printed part,
    and an overestimate everywhere else: through a skewed wall it measures the slant,
    up to 1/0.3 of the true section at its own exit filter's floor. So any chord thin
    enough that the true section might still be under `min_wall` gets refined by
    `_sphere_at`, which measures the way a wall is actually thin, perpendicular to
    nothing in particular. The gate follows from the filter rather than being tuned: an
    accepted chord leaves within the 0.3 cosine floor, so a chord past `min_wall / 0.3`
    cannot be hiding a failing section, and the sphere is only paid for where it could
    matter. That also prices `min_wall = 0`, the card's way of saying "this rule cannot
    measure this part", at nothing.

    Two caveats survive the correction, and live on cards rather than in code:

    - A taper reads as a wall. Near the tip of a designed knife edge every section is
      short, sphere and chord alike. The gridfinity shelves' sockets measure 0.84mm
      where their 45 degree walls meet, and their cards allow 0.7 next to the sentence
      saying why.
    - A relief reads as a wall. The calibration coupon's raised label is 0.5mm proud,
      and that is what gets measured, so its card sets `min_wall = 0`.

    Probes sample faces, so a pinch nothing lands near is still missed. Treat a clean
    result as "no thin walls found", not as "no thin walls".
    """
    thinnest, spot = None, None
    floor = ctx.min_wall * 0.01
    for face in shape.faces():
        if face.area < ctx.sliver_area:
            continue  # a face this small has no wall to speak of
        for point, normal in _probes(face):
            inward = -normal
            hits = shape.find_intersection_points(Axis(point + inward * PROBE, inward))
            # Only count a surface the ray leaves through: its outward normal points
            # along the way the ray is going. A hit facing back at the ray means the
            # ray had already left the material and struck something across a gap,
            # which is how a chamfer two corners away reads as a thin wall.
            reach = [
                (hit - point).length
                for hit, hit_normal in hits
                if (hit - point).dot(inward) > floor
                and hit_normal.dot(inward) > 0.3
            ]
            if not reach:
                continue
            near = min(reach)
            if near * 0.3 < ctx.min_wall:
                # The sphere starts from the first boundary crossing rather than from
                # the accepted chord, because half of that is guaranteed to sit inside
                # the material, and the shrink only ever moves down from there.
                first = min(
                    (hit - point).length for hit, _ in hits if (hit - point).length > floor
                )
                section = _sphere_at(shape, point, normal, first)
                if section is not None and floor < section < near:
                    near = section
            if thinnest is None or near < thinnest:
                thinnest, spot = near, point
    # Slack, because a card declaring the value it measured should not then fail on the
    # last bit of a float. One percent rather than a micron: the same solid measures
    # 0.500 against one OCCT build and 0.498 against another, and a threshold tight
    # enough to see that turns a card into a claim about which machine wrote it. A card
    # can also set `min_wall = 0` to say the rule cannot measure this part at all, which
    # is honest for anything whose thinnest apparent section is not a wall.
    if thinnest is None or thinnest >= ctx.min_wall * 0.99 - 1e-3:
        return []
    return [
        Finding(
            "min_wall",
            WARN,
            f"{thinnest:.2f}mm section, under the {ctx.min_wall:.2f}mm this printer "
            f"lays down reliably",
            value=round(thinnest, 3),
            where=tuple(round(v, 2) for v in spot),
        )
    ]
