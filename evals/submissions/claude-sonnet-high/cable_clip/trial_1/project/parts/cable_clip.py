from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    wall_thickness=2.4,
    base_thickness=3.0,
    channel_clearance=0.4,
    part_length=12.0,
    tab_length=10.0,
    hole_diameter=4.2,
    draft=False,
):
    """
    bundle_diameter: how thick the cable bundle is, sets the channel size
    wall_thickness: how thick the channel's side walls are
    base_thickness: how thick the solid base is under the channel
    channel_clearance: extra room in the channel beyond the bundle diameter
    part_length: how long the clip is along the cable
    tab_length: how far the mounting tab sticks out past the wall
    hole_diameter: the screw hole's diameter through the mounting tab
    """
    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    body_width = 2 * wall_thickness + channel_width
    body_height = base_thickness + channel_depth
    overshoot = 1.0

    body = Pos(body_width / 2, part_length / 2, body_height / 2) * Box(
        body_width, part_length, body_height
    )
    tab = Pos(-tab_length / 2, part_length / 2, base_thickness / 2) * Box(
        tab_length, part_length, base_thickness
    )
    blank = body + tab

    # Channel cutter overshoots both Y ends so the channel opens straight
    # through the part's ends rather than leaving a thin cap.
    channel_cutter = Pos(
        wall_thickness + channel_width / 2,
        part_length / 2,
        base_thickness + channel_depth / 2,
    ) * Box(channel_width, part_length + 2 * overshoot, channel_depth)
    channeled = blank - channel_cutter
    channel_edges = new_edges(blank, combined=channeled)

    hole_cutter = Pos(-tab_length / 2, part_length / 2, base_thickness / 2) * Cylinder(
        radius=hole_diameter / 2, height=base_thickness + 2 * overshoot
    )
    drilled = channeled - hole_cutter
    hole_edges = new_edges(channeled, combined=drilled)

    if draft:
        return drilled

    # Never touch the channel (fit-critical mating geometry) or the hole
    # bore, and never touch the bed face or a concave edge.
    bed = drilled.bounding_box().min.Z

    # On the tab's wall, the outer face is split by the tab step, so this
    # corner's vertical edge is short and doesn't reach the bed like its
    # counterpart on the far wall does. Chamfering it collides with the top
    # rim chamfer and leaves a sub-1mm2 sliver; skip it, matching the far
    # wall's corner where the (bed-excluded) vertical edge stays sharp too.
    def is_short_riser(e):
        bb = e.bounding_box()
        return (
            abs(bb.min.X - bb.max.X) < 1e-6
            and abs(bb.min.X) < 1e-6
            and abs(bb.min.Z - base_thickness) < 1e-6
            and abs(bb.max.Z - body_height) < 1e-6
        )

    risers = drilled.edges().filter_by(is_short_riser)
    protect = (
        set(channel_edges)
        | set(hole_edges)
        | set(concave_edges(drilled))
        | set(risers)
    )
    keep = drilled.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in protect
    )
    return polish(drilled, keep, 1.0)
