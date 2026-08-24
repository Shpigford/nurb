from nurb import *

CHANNEL_CLEARANCE = 0.4  # gap beyond the bundle so it drops into the channel without binding
EPS = 1e-4
OVERSHOOT = 1.0  # extra reach on cutting tools so boolean faces never land exactly coincident


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    wall_thickness=2.4,
    base_thickness=3.0,
    part_length=12.0,
    tab_length=10.0,
    hole_diameter=4.2,
    chamfer_size=1.0,
    draft=False,
):
    """A screw-down clip that grips a cable bundle in an open channel.

    bundle_diameter: the cable bundle's measured diameter, which the channel is sized around
    wall_thickness: how thick each wall beside the channel is
    base_thickness: how thick the solid floor under the channel is
    part_length: how long the clip is along the cable (Y)
    tab_length: how far the mounting tab reaches out from the wall
    hole_diameter: the screw's through-hole diameter in the tab
    chamfer_size: the cosmetic edge chamfer, applied everywhere polish is allowed to land
    """
    if hole_diameter >= min(tab_length, part_length):
        raise ValueError(
            f"a {hole_diameter}mm hole does not fit centered in a {tab_length}x{part_length}mm "
            f"tab. Shrink hole_diameter, or grow tab_length/part_length."
        )

    channel_width = bundle_diameter + CHANNEL_CLEARANCE
    channel_depth = bundle_diameter
    channel_half = channel_width / 2

    body_width = channel_width + 2 * wall_thickness
    body_half = body_width / 2
    body_height = base_thickness + channel_depth

    # Base and walls as one block, channel cut open at the top and both Y ends, so the
    # cable can drop in from above or feed through either end.
    body = Pos(0, 0, body_height / 2) * Box(body_width, part_length, body_height)
    channel = Pos(0, 0, base_thickness + (channel_depth + OVERSHOOT) / 2) * Box(
        channel_width, part_length + 2 * OVERSHOOT, channel_depth + OVERSHOOT
    )
    body -= channel

    # Mounting tab, flush with the bottom, on the outside of the +X wall.
    tab_center_x = body_half + tab_length / 2
    tab = Pos(tab_center_x, 0, base_thickness / 2) * Box(
        tab_length, part_length, base_thickness
    )
    body += tab

    hole = Pos(tab_center_x, 0, base_thickness / 2) * Cylinder(
        hole_diameter / 2, base_thickness + 2 * OVERSHOOT
    )
    body -= hole

    if draft:
        return body

    # The polish pass. Excluded: the bed-contact bottom face, every concave edge (the
    # channel floor's inside corners, the step where the tab meets the taller wall),
    # the whole channel cavity -- fit-critical mating geometry that a lead-in chamfer
    # would round even though its floor and mouth edges read as ordinary convex ones
    # -- and the hole rim, a plain through-hole rather than a countersink.
    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))

    def keep(edge):
        if edge.geom_type != GeomType.LINE:
            return False  # the hole rim
        bb = edge.bounding_box()
        if abs(bb.max.Z - bed) < EPS:
            return False  # lies in the bottom face
        if (
            bb.min.X > -channel_half - EPS
            and bb.max.X < channel_half + EPS
            and bb.min.Z > base_thickness - EPS
            and bb.max.Z < body_height + EPS
        ):
            return False  # bounds the channel cavity: floor, side walls, or either mouth
        return True

    candidates = [e for e in body.edges().filter_by(keep) if e not in concave]

    # Three mutually chamfered edges meeting at one convex corner leave a sliver
    # triangle behind, about 0.87mm2 at this chamfer_size and under nurb check's
    # 1mm2 floor. Every such corner here is an ordinary box corner with one short
    # edge and two long ones, so dropping the shortest breaks the triangle and
    # leaves a plain two-edge miter instead.
    def vkey(v):
        return (round(v.X, 4), round(v.Y, 4), round(v.Z, 4))

    at_vertex = {}
    for e in candidates:
        for v in (e.position_at(0), e.position_at(1)):
            at_vertex.setdefault(vkey(v), []).append(e)

    drop = {min(edges, key=lambda e: e.length) for edges in at_vertex.values() if len(edges) >= 3}
    candidates = [e for e in candidates if e not in drop]

    return polish(body, candidates, chamfer_size)
