from nurb import *


@part
def pole_rest(
    pole_diameter=20.0,
    length=22.0,
    clearance=0.2,
    wall=2.5,
    margin=2.0,
    draft=False,
):
    """
    pole_diameter: diameter of the pole this rest cradles
    length: how long the rest runs along the pole's axis
    clearance: gap between the cradle and the pole's surface
    wall: material thickness behind the cradle surface
    margin: extra material at the base beyond the cradle's footprint
    """
    pole_radius = pole_diameter / 2.0
    axis_height = 18.0

    if clearance < 0.1:
        reject(
            f"clearance {clearance} is under the 0.1mm minimum stand-off from the pole",
            param="clearance",
        )

    inner_radius = pole_radius + clearance
    outer_radius = inner_radius + wall + 1.2

    half_width = outer_radius + margin
    width = 2 * half_width

    # Stop the groove well below the pole's centre height so it opens wide
    # (under 180 degrees) straight upward, letting the pole drop in from
    # above, and so its rim sits clear of the tangent zone where the lid
    # and the bore would otherwise meet at a knife edge.
    lip = 3.0
    top_z = axis_height - lip

    # The cradle is a constant-thickness pipe (outer cylinder minus inner
    # cylinder), never a solid block cut by a circle, so `wall` of material
    # backs the pole everywhere along the arc. A flat slab under it, reaching
    # only up to the pipe's own lowest point, gives it a bed footprint.
    span = length + 20
    outer_cyl = Cylinder(outer_radius, span, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    inner_cyl = Cylinder(inner_radius, span, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    pipe = outer_cyl - inner_cyl
    pipe = pipe.rotate(Axis.X, 90).locate(Location((0, 0, axis_height)))

    bounds = Box(width, length, top_z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pipe = pipe & bounds

    base_height = axis_height - outer_radius + 2.5
    base = Box(width, length, base_height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    body = pipe + base

    if draft:
        return body

    bed = body.bounding_box().min.Z
    cradle = concave_edges(body)
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed) - cradle
    return polish(body, keep, 1.0)
