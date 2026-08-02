"""The crown pass: one smooth round bead along a variable-height rim.

Issue #55's largest problem was conceptually one sentence, "round the top of this
variable-height wall", and cost a 689-line part file eight manual steps. Filleting the
roofline directly dies in OCCT's corner capping: bumps where wall sections join, missing
roundovers on short segments, spherical patches at corners. The insight that makes the
problem tractable is that for a wall of constant thickness t, a fully round rim is
exactly the wall unioned with a pipe of radius t/2 swept along the wall's top
centreline. A smooth path makes the pipe inherently smooth and tangent everywhere, so no
corner cap is ever asked for, and the whole problem collapses into building one smooth
closed 3D path.

The path is a periodic spline through samples of the plan midline lifted to the wall's
top surface, so the bead follows the roofline within sampling tolerance rather than
exactly. For a printed part that is fine, and it is what buys the corner handling: a
spline has no corners to cap.

Every tolerance here was measured, not reasoned about:

- build123d's `sweep` walks its path with a corrected Frenet frame, and Build() fails
  erratically on these paths (a flat rounded rectangle worked at 60 samples and failed
  at 200). A circular profile cannot show frame twist, so a fixed binormal frame is
  geometrically identical and never wobbles. That is why the sweep drops to OCP.
- A bead exactly flush with the wall faces is tangent to both along its whole length,
  and OCCT's fuse returns garbage on that contact (measured: volume -82, invalid).
  WELD of interference makes every contact a real crossing. The lip it leaves is a
  quarter of a bed's positioning accuracy and prints as nothing.
- Sampling at SPACING keeps the spline within about SPACING^2 / (8 * radius) of the
  true midline, under WELD for any corner the curvature gate admits, so no strip of the
  top face is left showing beside the bead. Measured at 0.5mm: zero sliver faces.
- Roofline ramps at 45 and 60 degrees sweep cleanly (worst sample slope 1.74); a sheer
  step measures around 40 and produces an invalid solid. SLOPE is the gate between
  them.
- Where the roofline slopes across the wall rather than along it, the top face tilts
  and one top edge rides higher than the other. The bead centres between the two edges
  and widens just past flush until it swallows both; the widening is capped at a fifth
  of the radius, where the lip under the bead still meets the bed rule's 45 degrees
  with room to spare, and a tilt past that cap is refused.
"""

import math

from build123d import Axis, Circle, Kind, Plane, Solid, Spline, Vector, Wire, section

SPACING = 0.5  # mm between path samples
WELD = 0.05  # minimum mm of bead past a flush wall face: the union needs interference
SLOPE = 2.0  # rise over run between samples; 60 degree ramps measure 1.74
INSET = 0.05  # how far inside each wall face the top-edge probes run

__all__ = ["crown"]


def _refuse(what, advice):
    return ValueError(what + "\n\n" + "\n".join(f"  {line}" for line in advice) + "\n")


def _loop(wall, z0):
    """The wall's outer and inner boundary at z0, or a doctrine-grade refusal."""
    sk = section(wall, Plane.XY, height=z0)
    faces = sk.faces()
    if len(faces) != 1 or len(faces[0].wires()) != 2:
        shape = (
            f"{len(faces)} regions with {sum(len(f.wires()) for f in faces)} boundaries"
        )
        raise _refuse(
            f"crown needs one closed wall loop and the slice at z={z0:.1f} has {shape}.",
            [
                "Crown the bare perimeter wall, before it is unioned with a floor or",
                "anything else: a tray's slice is one solid region, so there is no loop",
                "for the bead to follow. Build the wall, crown it, then add the rest.",
            ],
        )
    face = faces[0]
    outer = face.outer_wire()
    inner = next(w for w in face.wires() if not w.is_same(outer))
    return outer, inner


def _thickness(outer, inner):
    """The wall's thickness, as a corner-proof median.

    Sampled outer to inner, where a sharp corner measures the diagonal rather than the
    wall, so the median is the estimate and constancy is judged later from the midline,
    whose nearest-point distances are perpendicular even at a corner.
    """
    spans = sorted(inner.distance_to(outer.position_at(i / 32)) for i in range(32))
    return spans[len(spans) // 2]


def _constant(plan, outer, inner, t):
    """Refuse a wall that tapers in plan: no one path a flush bead could follow."""
    spans = [
        outer.distance_to(p) + inner.distance_to(p) for p in plan[:: max(1, len(plan) // 32)]
    ]
    if max(spans) - min(spans) > 0.1 * t:
        raise _refuse(
            f"crown needs a wall of near-constant thickness and this one runs "
            f"{min(spans):.2f} to {max(spans):.2f}mm.",
            [
                "A flush bead follows one centreline, and a tapering wall does not have",
                "one. Even the thickness first, or crown a constant-thickness wall and",
                "union the tapered geometry afterwards.",
            ],
        )


def _midline(outer, inner, t):
    # Which offset direction is inward depends on the wire's orientation, so measure
    # instead of assuming. The midline runs t/2 from the inner boundary, stretching to
    # about 0.7t where a corner leaves only the diagonal; the outward offset never
    # comes nearer than 1.5t, so the gap between them is wide.
    for sign in (-1, 1):
        try:
            mid = outer.offset_2d(sign * t / 2, kind=Kind.INTERSECTION)
        except Exception:
            continue
        if inner.distance_to(mid.position_at(0)) < 1.2 * t:
            return mid if isinstance(mid, Wire) else Wire([mid])
    raise _refuse(
        "crown could not offset the wall's outline to a centreline.",
        [
            "This usually means the plan pinches somewhere tighter than half the wall",
            "thickness. Open the tight spot up, or round it with a plan fillet.",
        ],
    )


def _circumradius(a, b, c):
    ab, bc, ca = (b - a).length, (c - b).length, (a - c).length
    s = (ab + bc + ca) / 2
    area_sq = max(s * (s - ab) * (s - bc) * (s - ca), 0.0)
    if area_sq < 1e-18:
        return math.inf
    return ab * bc * ca / (4 * math.sqrt(area_sq))


def crown(wall, radius=None):
    """Round the top of a closed perimeter wall with one smooth bead.

    The bead is a pipe swept along the wall's top centreline, so it rises and falls
    with the roofline and the crowned wall stands `radius` prouder than it was built.
    `radius` defaults to half the measured wall thickness, which makes the bead flush
    with both faces; smaller leaves a flat shoulder either side, and larger is refused
    because it would overhang the faces.

    The wall must be the bare perimeter loop of near-constant thickness, crowned before
    it is unioned with a floor or anything else. Plan corners need to be rounded to at
    least the bead radius, so a wall of thickness t wants plan fillets of t or more.
    Roofline transitions hold to 60 degrees or shallower and run along the walls, not
    across them: a transition crossing a wall tilts its top, and the bead widens a
    touch past flush to swallow the higher edge, up to a cap. Each refusal names its
    own fix. Skip the crown when `draft` is true, the same way a part skips polish.
    """
    bb = wall.bounding_box()
    z0 = bb.min.Z + 0.05 * (bb.max.Z - bb.min.Z)
    outer, inner = _loop(wall, z0)
    t = _thickness(outer, inner)
    if radius is None:
        radius = t / 2
    if radius <= 0:
        raise ValueError(f"crown radius must be positive, not {radius!r}")
    if radius > t / 2 + 1e-6:
        raise _refuse(
            f"crown radius {radius:g} is wider than half this {t:.2f}mm wall.",
            [
                "A bead wider than its wall hangs a lip over both faces. Thicken the",
                "wall or shrink the radius; flush is the default when radius is left",
                "unset.",
            ],
        )

    mid = _midline(outer, inner, t)
    n = min(4000, max(64, round(mid.length / SPACING)))
    plan = [mid.position_at(i / n) for i in range(n)]

    tightest, where = math.inf, plan[0]
    for i in range(n):
        r = _circumradius(plan[i - 1], plan[i], plan[(i + 1) % n])
        if r < tightest:
            tightest, where = r, plan[i]
    if tightest < radius - 0.05:
        raise _refuse(
            f"the plan turns tighter ({tightest:.1f}mm around ({where.X:.0f}, "
            f"{where.Y:.0f})) than the crown is round ({radius:g}mm), so the bead "
            f"would fold into itself there.",
            [
                f"Give the wall plan fillets of at least {radius + t / 2:g}mm, which",
                f"keeps the centreline no tighter than the bead. Issue #55's tray",
                f"needed exactly this and 3mm fillets fixed it.",
            ],
        )
    # After the corner gate: a sub-radius corner would pollute these samples with
    # diagonal distances and read as taper.
    _constant(plan, outer, inner, t)

    # The top of the wall at each sample, probed at both edges rather than on the
    # midline: where the roofline slopes across the wall the top face tilts, one edge
    # rides higher than the other, and a bead centred on either would leave the other
    # showing. The bead centres between them, and the tilt decides the weld below.
    def top_at(x, y, p):
        hits = wall.intersect(Axis((x, y, bb.min.Z - 1), (0, 0, 1)))
        tops = [v.Z for h in hits or [] for v in h.vertices()]
        if not tops:
            raise ValueError(
                f"crown found no wall above the centreline at ({p.X:.1f}, {p.Y:.1f})"
            )
        return max(tops)

    reach = t / 2 - INSET
    path_pts, tilt = [], 0.0
    for i in range(n):
        p = plan[i]
        ahead, behind = plan[(i + 1) % n], plan[i - 1]
        along = (ahead - behind).normalized()
        nx, ny = -along.Y, along.X
        a = top_at(p.X + nx * reach, p.Y + ny * reach, p)
        b = top_at(p.X - nx * reach, p.Y - ny * reach, p)
        tilt = max(tilt, abs(a - b))
        path_pts.append(Vector(p.X, p.Y, (a + b) / 2))

    for i in range(n):
        a, b = path_pts[i], path_pts[(i + 1) % n]
        run = math.hypot(b.X - a.X, b.Y - a.Y)
        if abs(b.Z - a.Z) > SLOPE * max(run, 1e-9):
            raise _refuse(
                f"the roofline steps {abs(b.Z - a.Z):.1f}mm over a {run:.1f}mm run "
                f"near ({a.X:.0f}, {a.Y:.0f}), too sheer for the bead to follow.",
                [
                    "Ramp or curve the transition instead; 60 degrees and shallower is",
                    "measured to crown cleanly. The spline would round a sheer step on",
                    "its own, but the wall's square shoulders would poke through it.",
                ],
            )

    # Enough interference to swallow the higher top edge on the worst tilt, never less
    # than the union needs, capped where the lip would start to read as a feature.
    # The probes run INSET inside each face, so the tilt they see is scaled out to the
    # faces; the 0.06 covers roofline curvature between probe and edge, measured on a
    # sine whose crests bend at a 2.85mm radius.
    tilt *= t / (t - 2 * INSET)
    weld = max(WELD, math.hypot(radius, tilt / 2 + 0.06) - radius)
    if weld > 0.2 * radius:
        raise _refuse(
            f"the roofline tilts {tilt:.1f}mm across the {t:.1f}mm wall, more than a "
            f"{radius:g}mm bead can swallow.",
            [
                "This happens where a roofline transition crosses a wall instead of",
                "running along it, so one top edge rides higher than the other. Run",
                "the rise and fall along the walls, make the transition gentler, or",
                "thicken the wall so the same slope tilts it less.",
            ],
        )
    flush = radius > t / 2 - WELD
    bead = _pipe(Spline(*path_pts, periodic=True), radius + weld if flush else radius)
    out = wall + bead
    if not out.is_valid or out.volume <= wall.volume:
        raise _refuse(
            "the crown bead built but would not weld onto the wall.",
            [
                "This is the kernel refusing, not the part, and it usually means the",
                "geometry is right at one of the limits above. Nudge the plan fillets",
                "or the roofline transitions away from the edge and rebuild.",
            ],
        )
    return out


def _pipe(path, radius):
    """A circle swept along `path` on a fixed vertical binormal frame."""
    from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
    from OCP.gp import gp_Dir
    from OCP.TopoDS import TopoDS

    profile = Plane(origin=path.position_at(0), z_dir=path.tangent_at(0)) * Circle(radius)
    builder = BRepOffsetAPI_MakePipeShell(Wire([path]).wrapped)
    builder.SetMode(gp_Dir(0, 0, 1))
    builder.Add(profile.wires()[0].wrapped)
    builder.Build()
    if not builder.IsDone() or not builder.MakeSolid():
        raise _refuse(
            "the crown bead would not sweep.",
            [
                "The path passed the corner and slope gates, so this is the kernel",
                "refusing at geometry right on a limit. Round the plan corners a",
                "little further, or ease the steepest roofline transition.",
            ],
        )
    return Solid(TopoDS.Solid_s(builder.Shape()))
