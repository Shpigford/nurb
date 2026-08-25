from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A support-free, drop-in cradle for a finished pole.

    pole_diameter: diameter of the pole being held
    """
    pole_radius = pole_diameter / 2.0
    axis_height = 18.0
    clearance = 0.1
    inner_radius = pole_radius + clearance
    wall = 2.4
    outer_radius = inner_radius + wall
    length = 24.0

    # Keep the bed plate just below the pole's lowest point. It supports the
    # lower cradle layers without intruding into the finished-pole envelope.
    base_top = axis_height - inner_radius - 0.25
    base_width = 2.0 * outer_radius + 4.0
    base = Pos(0, 0, base_top / 2.0) * Box(
        base_width, length, base_top,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    # A square-backed outer wall keeps every printable exterior face vertical;
    # the only curved face is the recessed pole-contact surface.
    outer = Pos(0, 0, axis_height - outer_radius / 2.0) * Box(
        2.0 * outer_radius,
        length,
        outer_radius,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    inner = Cylinder(
        inner_radius, length + 0.4,
        rotation=(90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    annulus = outer - (Pos(0, 0, axis_height) * inner)

    # The block is already limited to the lower 180-degree arc: the open top
    # lets the pole drop in, while the close-fitting inner wall supports it.
    cradle = annulus
    body = base + cradle

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(body, keep, 1.0)
