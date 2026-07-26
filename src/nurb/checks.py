"""Printability rules, run against the solid rather than against an export.

Checking the B-rep instead of an STL means real faces with exact areas and normals
instead of triangles, which is what makes most of these rules cheap and exact.

A rule takes the shape and a Context and yields Findings. Rules compose: they never
see each other, and `run` gathers them.
"""

from dataclasses import dataclass, field
from math import asin, degrees

from build123d import CenterOf, GeomType, Vector

FAIL = "fail"  # this will not print, or will not work
WARN = "warn"  # this needs attention, most often support


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str
    value: float | None = None
    where: tuple | None = None

    def __str__(self):
        spot = f"  at ({self.where[0]:.1f}, {self.where[1]:.1f}, {self.where[2]:.1f})" if self.where else ""
        return f"{self.severity:4}  {self.rule:20} {self.message}{spot}"


@dataclass
class Context:
    """What a rule needs to know beyond the geometry itself.

    `up` is the build direction, and it is not the model's z. A part is modelled on
    whatever datums make its function readable and printed on whatever face keeps it
    off supports, and those are rarely the same. Notch parts hang from a slab top at
    z=0 and print on their backs, so every overhang question about them is asked
    about -x. Getting this wrong does not error, it just reports confident nonsense.
    """

    bed: tuple = (256.0, 256.0, 256.0)
    up: tuple = (0.0, 0.0, 1.0)
    overhang_limit: float = 45.0  # degrees away from the build direction
    sliver_area: float = 1.0
    accepted: dict = field(default_factory=dict)  # rule -> how many are already known


RULES = {}


def rule(name):
    def register(fn):
        RULES[name] = fn
        return fn

    return register


def run(shape, ctx=None, only=None):
    ctx = ctx or Context()
    found = []
    for name, fn in RULES.items():
        if only and name not in only:
            continue
        found.extend(fn(shape, ctx))
    return sorted(found, key=lambda f: (f.severity != FAIL, f.rule))


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
            value=round(worst.area, 3),
            where=tuple(round(v, 2) for v in worst.center()),
        )
    ]


@rule("build_volume")
def build_volume(shape, ctx):
    """Does it fit on the printer at all."""
    size = shape.bounding_box().size
    got = sorted([size.X, size.Y, size.Z], reverse=True)
    fits = sorted(ctx.bed, reverse=True)
    if all(g <= b for g, b in zip(got, fits)):
        return []
    return [
        Finding(
            "build_volume",
            FAIL,
            f"{size.X:.0f} x {size.Y:.0f} x {size.Z:.0f}mm does not fit "
            f"{ctx.bed[0]:.0f} x {ctx.bed[1]:.0f} x {ctx.bed[2]:.0f}mm in any orientation",
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

    Exact for an axis-aligned build direction, which is what a part placed on a bed
    has. Conservative otherwise.
    """
    box = shape.bounding_box()
    corners = [
        Vector(x, y, z)
        for x in (box.min.X, box.max.X)
        for y in (box.min.Y, box.max.Y)
        for z in (box.min.Z, box.max.Z)
    ]
    reach = [c.dot(up) for c in corners]
    return min(reach), max(reach)


@rule("overhang")
def overhang(shape, ctx):
    """Downward faces steeper than the printer will bridge.

    Angle is measured from the build direction, so a vertical wall is 0 and a flat
    ceiling is 90. Faces sitting on the bed are skipped: they are the first layer,
    not an overhang.
    """
    up = Vector(*ctx.up).normalized()
    bed, _ = _span(shape, up)
    found = []
    for face in shape.faces():
        if _span(face, up)[1] <= bed + 1e-4:
            continue  # grounded, so it is the first layer rather than an overhang
        worst = max(
            degrees(asin(max(-1.0, min(1.0, -n.dot(up))))) for n in _sample_normals(face)
        )
        if worst > ctx.overhang_limit + 1e-6:
            found.append(
                Finding(
                    "overhang",
                    WARN if worst < 90 else FAIL,
                    f"{worst:.0f}deg overhang over {face.area:.1f}mm2, "
                    f"limit {ctx.overhang_limit:.0f}deg",
                    value=round(worst, 1),
                    where=tuple(round(v, 2) for v in face.center()),
                )
            )
    return found


@rule("stability")
def stability(shape, ctx):
    """Will it stand on the bed, or tip while printing."""
    up = Vector(*ctx.up).normalized()
    bed, _ = _span(shape, up)
    footing = [f for f in shape.faces() if _span(f, up)[1] <= bed + 1e-4]
    if not footing:
        return [Finding("stability", FAIL, "nothing flat to stand on")]
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
                    where=tuple(round(v, 2) for v in com),
                )
            ]
    return []
