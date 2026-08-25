from nurb import *


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    length=24.0,
    wall=3.0,
    clearance=0.25,
    draft=False,
):
    """
    pole_diameter: diameter of the pole this rest cradles
    length: how long the rest runs along the pole
    wall: material thickness around and under the cradle
    clearance: gap left between the cradle and the pole's surface
    """
    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + clearance
    axis_z = 18.0
    base_min = 2.0

    if seat_radius + base_min > axis_z:
        reject(
            f"pole_diameter {pole_diameter} puts the seat within {base_min}mm of "
            f"the bed at a fixed 18.0mm axis height: keep pole_diameter under "
            f"{2 * (axis_z - base_min - clearance):.1f}",
            param="pole_diameter",
        )

    width = 2.0 * (seat_radius + wall)
    height = axis_z
    center_x = width / 2.0

    body = Box(width, length, height, align=(Align.MIN, Align.MIN, Align.MIN))

    overhang = 1.0
    cut = Cylinder(
        seat_radius,
        length + 2 * overhang,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cut = Rot(-90, 0, 0) * cut
    cut = Pos(center_x, -overhang, axis_z) * cut

    body = body - cut

    if draft:
        return body

    mating = list(body.faces().filter_by(GeomType.CYLINDER).edges())
    concave = list(concave_edges(body))

    # Only the 4 vertical corner edges: chamfering the top perimeter too would
    # meet them at the top corners and leave sub-mm2 sliver triangles.
    keep = [
        e
        for e in body.edges()
        if e not in mating
        and e not in concave
        and e.bounding_box().size.X < 1e-6
        and e.bounding_box().size.Y < 1e-6
        and e.bounding_box().size.Z > 1e-6
    ]

    return polish(body, keep, 1.0)
