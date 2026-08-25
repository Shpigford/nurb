from math import asin, cos, hypot, sin, sqrt

from nurb import *


def _reach(edge):
    """How far an edge sits from the part's vertical centerline, at its farthest."""
    box = edge.bounding_box()
    return max(
        hypot(x, y)
        for x in (box.min.X, box.max.X)
        for y in (box.min.Y, box.max.Y)
    )


def _key(edge):
    """A positional key, so an edge picked out of one body is findable in another."""
    middle = edge.center()
    return (
        round(middle.X, 4),
        round(middle.Y, 4),
        round(middle.Z, 4),
        round(edge.length, 4),
    )


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    stem_length=measured("stem_length"),
    bore_clearance=0.65,
    knob_height=15.0,
    body_width=30.0,
    wing_reach=35.0,
    wing_root_width=18.0,
    wing_tip_width=10.0,
    wing_taper=5.0,
    root_relief=3.0,
    hollow_depth=10.0,
    wall=3.0,
    draft=False,
):
    """A two-wing replacement handle for a valve with a D-shaped stem.

    shaft_diameter: how wide the valve stem measures across its round side
    shaft_across_flat: how thick the stem measures from its flat to its round side
    stem_length: how far the stem stands proud of the valve body
    bore_clearance: how much wider the bore is than the stem, so the knob slides on
    knob_height: how tall the knob is
    body_width: how wide the round middle of the knob is
    wing_reach: how far each wing reaches out from the centre
    wing_root_width: how wide a wing is where it leaves the round middle
    wing_tip_width: how wide a wing is at its rounded end
    wing_taper: how much thinner a wing gets out at its tip
    root_relief: how much the wings are rounded into the body, where they take the load
    hollow_depth: how deep the underside is scooped out to save plastic
    wall: how much material stands around the bore and behind the outside
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} is not under the {shaft_diameter}mm "
            "diameter, so there is no flat to key on and the knob spins on the stem",
            param="shaft_across_flat",
        )
    if shaft_across_flat <= shaft_diameter / 2.0:
        reject(
            f"shaft_across_flat {shaft_across_flat} cuts past the centre of a "
            f"{shaft_diameter}mm stem: measure again from the flat to the round side",
            param="shaft_across_flat",
        )

    bore_r = (shaft_diameter + bore_clearance) / 2.0
    flat_x = (shaft_across_flat + bore_clearance) - bore_r
    bore_depth = stem_length + 0.5
    if knob_height - bore_depth < 2.0:
        reject(
            f"knob_height {knob_height} leaves {knob_height - bore_depth:.1f}mm of floor "
            f"under a {bore_depth:.1f}mm bore: raise it above {bore_depth + 2.0:.1f}",
            param="knob_height",
        )

    body_r = body_width / 2.0
    hub_r = bore_r + wall
    pocket_r = body_r - wall
    if pocket_r <= hub_r:
        reject(
            f"body_width {body_width} leaves no room for a {wall}mm wall around a "
            f"{2 * bore_r:.1f}mm bore: raise it above {2 * (hub_r + wall):.1f}",
            param="body_width",
        )
    if knob_height - hollow_depth < 2.5:
        reject(
            f"hollow_depth {hollow_depth} leaves under 2.5mm of floor in a "
            f"{knob_height}mm knob: lower it below {knob_height - 2.5:.1f}",
            param="hollow_depth",
        )

    root_r = wing_root_width / 2.0
    tip_r = wing_tip_width / 2.0
    span = wing_reach - tip_r
    if not tip_r <= root_r < body_r:
        reject(
            f"wing_root_width {wing_root_width} has to sit between wing_tip_width "
            f"{wing_tip_width} and the {body_width}mm body",
            param="wing_root_width",
        )
    if span <= root_r + 1.0:
        reject(
            f"wing_reach {wing_reach} does not clear the {body_width}mm body, so there "
            f"is nothing to grip: raise it above {body_r + tip_r:.1f}",
            param="wing_reach",
        )

    # The plan is one closed outline rather than a union of shapes: the wing sides run
    # on the tangent between a root circle and the tip circle, and a sketch boolean
    # against that tangency leaves faces unfused and volumes double counted.
    lean = asin((root_r - tip_r) / span)
    tangent_root = (-root_r * sin(lean), root_r * cos(lean))
    tangent_tip = (span - tip_r * sin(lean), tip_r * cos(lean))
    run = hypot(tangent_tip[0] - tangent_root[0], tangent_tip[1] - tangent_root[1])
    step = (
        (tangent_tip[0] - tangent_root[0]) / run,
        (tangent_tip[1] - tangent_root[1]) / run,
    )
    half = tangent_root[0] * step[0] + tangent_root[1] * step[1]
    out = -half + sqrt(
        half * half - (tangent_root[0] ** 2 + tangent_root[1] ** 2 - body_r**2)
    )
    # Where the wing side leaves the round body, and where it meets the tip arc.
    a = (tangent_root[0] + out * step[0], tangent_root[1] + out * step[1])
    b = tangent_tip
    c, d = (b[0], -b[1]), (a[0], -a[1])
    e, f = (-a[0], -a[1]), (-b[0], -b[1])
    g, h = (-b[0], b[1]), (-a[0], a[1])
    plan = make_face(
        Line(a, b)
        + ThreePointArc(b, (wing_reach, 0.0), c)
        + Line(c, d)
        + ThreePointArc(d, (0.0, -body_r), e)
        + Line(e, f)
        + ThreePointArc(f, (-wing_reach, 0.0), g)
        + Line(g, h)
        + ThreePointArc(h, (0.0, body_r), a)
    )
    body = extrude(plan, amount=knob_height)

    # The wing roots carry every bit of torque a hand puts in, so relieve them. The
    # tangent joins out at the tips read as concave too; leave those alone.
    if root_relief > 0.0:
        roots = ShapeList(
            edge for edge in concave_edges(body) if _reach(edge) < body_r + 1.0
        ).filter_by(Axis.Z)
        if roots:
            body = fillet(roots, root_relief)

    # One cone thins the wings toward their tips, starting at the rim. It leaves the
    # whole outer top as a single surface, so there is no kink edge to chamfer badly.
    if wing_taper > 0.0:
        slope = wing_taper / (wing_reach - pocket_r)
        far = wing_reach + 5.0
        body -= revolve(
            Plane.XZ
            * make_face(
                Polyline(
                    (pocket_r, knob_height),
                    (far, knob_height - slope * (far - pocket_r)),
                    (far, knob_height + 5.0),
                    (pocket_r, knob_height + 5.0),
                    close=True,
                )
            ),
            Axis.Z,
        )

    # A ring scooped out of the underside: material no hand feels and no stem touches.
    # It opens upward as the part prints, so nothing spans air.
    if hollow_depth > 0.0 and pocket_r - hub_r >= 2.0:
        body -= Pos(0.0, 0.0, knob_height - hollow_depth) * extrude(
            Circle(pocket_r) - Circle(hub_r), amount=hollow_depth + 1.0
        )

    # The D bore, flat toward +X, opening straight up out of the print.
    unbored = body
    stop = 2.0 * bore_r + 20.0
    body -= Pos(0.0, 0.0, knob_height - bore_depth) * extrude(
        Circle(bore_r) - Pos(flat_x + stop / 2.0, 0.0) * Rectangle(stop, stop),
        amount=bore_depth + 1.0,
    )
    # Exactly the edges the bore cut, so the polish pass can be told to leave the
    # mating mouth alone. A radial guess reaches the round side of the D and misses
    # the flat, which is how a bore ends up chamfered down one side only.
    mating = {_key(edge) for edge in new_edges(unbored, combined=body)}

    if draft:
        return body

    # Keep the bore and every concave corner out of the polish pass, drop the edges
    # lying in the bed face, and let `polish` take whatever else will land.
    bed = body.bounding_box().min.Z
    inside = {_key(edge) for edge in concave_edges(body)}
    keep = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > bed + 1e-6
        and _key(edge) not in mating
        and _key(edge) not in inside
    )
    return polish(body, keep, 1.0)
