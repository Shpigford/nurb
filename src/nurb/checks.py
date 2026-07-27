"""Printability rules, run against the solid rather than against an export.

Checking the B-rep instead of an STL means real faces with exact areas and normals
instead of triangles, which is what makes most of these rules cheap and exact.

A rule takes the shape and a Context and yields Findings. Rules compose: they never
see each other, and `run` gathers them.
"""

import pathlib
from dataclasses import dataclass, field, replace
from math import asin, degrees

from build123d import Axis, CenterOf, GeomType, Vector

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
    """
    up = Vector(*ctx.up).normalized()
    bed, _ = _span(shape, up)
    solid = shape.solids()[0] if shape.solids() else None
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
        if crossing is None and _reach(face, up) <= ctx.overhang_reach:
            continue  # a ledge too shallow to droop, whatever its angle or length
        if crossing is not None:
            found.append(
                Finding(
                    "overhang",
                    WARN,
                    f"{crossing:.0f}mm bridge over {face.area:.1f}mm2, "
                    f"past the {ctx.bridge_limit:.0f}mm this printer spans",
                    value=round(crossing, 1),
                    where=tuple(round(v, 2) for v in face.center()),
                )
            )
        else:
            found.append(
                Finding(
                    "overhang",
                    FAIL,
                    f"{worst:.0f}deg unsupported over {face.area:.1f}mm2, "
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
    return _apply(base or Context(), settings(part_path), card.name)


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

    def fresh():
        return _apply(replace(base) if base else Context(), block, card.name)

    out = [(stem, {}, fresh())]
    for name, variant in block.get("variants", {}).items():
        extra = set(variant) - {"params", "accepted", "part", "printer"}
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

    What separates them is how far the face reaches, and a chamfer's reach is its size
    exactly. Measured: 1.00, 2.00 and 3.00mm for bottom chamfers of those sizes, against
    4.29mm for the corbel. The limit is three times the polish size because the largest
    chamfer this doctrine puts anywhere is the 3mm structural relief, and the smallest
    corbel it describes starts with a 4 to 6mm vertical tip, so there is a whole
    millimetre of daylight between the two. Width does not separate them: the same faces
    measure 3.25 and 3.43mm.
    """
    up = Vector(*ctx.up).normalized()
    bed, _ = _span(shape, up)
    found = []
    for face in shape.faces():
        if _span(face, up)[0] > bed + 1e-4:
            continue  # does not reach the plate
        if _reach(face, up) > 3 * ctx.cosmetic_chamfer:
            continue  # too far to be a chamfer band, so it is structure
        for normal in _sample_normals(face):
            tilt = abs(normal.dot(up))
            if 0.03 < tilt < 0.97:  # neither lying on the plate nor standing on it
                found.append(
                    Finding(
                        "bed_bevel",
                        WARN,
                        f"{degrees(asin(min(1.0, tilt))):.0f}deg face meets the build "
                        f"plate over {face.area:.1f}mm2, which is polish on the first layer",
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


@rule("min_wall")
def min_wall(shape, ctx):
    """The thinnest section in the solid, by shooting inward and seeing what it hits.

    This is a ray cast, not an inscribed sphere, and it is the weakest rule here. It is
    exact on the flat parallel walls that make up most of a printed part. It is wrong in
    two directions everywhere else, and both showed up on the first run against this
    library:

    - It reads a taper as a wall. The shelf's mouth rims are knife edges by design, and
      near the tip of a wedge any straight line across it is short. 0.76mm there is a
      true measurement of something that is not a wall.
    - It reads a relief as a wall. The calibration coupon's raised label is 0.5mm proud,
      and that is what the ray finds.

    Neither is a defect and all three parts print. So the number a part is allowed lives
    on its card next to the reason, and the default is what the printer manages rather
    than what a textbook says. It also misses the case an inscribed sphere would catch,
    a thin spot in an inside corner, where the smallest sphere that fits is smaller than
    any straight line across. Treat a clean result as "no thin walls found", not as
    "no thin walls".
    """
    thinnest, spot = None, None
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
                if (hit - point).dot(inward) > ctx.min_wall * 0.01
                and hit_normal.dot(inward) > 0.3
            ]
            if not reach:
                continue
            near = min(reach)
            if thinnest is None or near < thinnest:
                thinnest, spot = near, point
    # Slack, because a card declaring the value it measured should not then fail on
    # the last bit of a float.
    if thinnest is None or thinnest >= ctx.min_wall - 1e-3:
        return []
    return [
        Finding(
            "min_wall",
            WARN,
            f"{thinnest:.2f}mm section, under the {ctx.min_wall:.2f}mm this printer "
            f"lays down reliably (ray cast, so corners may be thinner still)",
            value=round(thinnest, 3),
            where=tuple(round(v, 2) for v in spot),
        )
    ]
