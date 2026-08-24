from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip for a cable bundle that runs along the wall.

    bundle_diameter: measured width of the taped cable bundle
    """
    clearance = 0.4
    inner = bundle_diameter + clearance
    wall_thick = 2.4
    floor = 2.2
    front = 2.0
    length = 12.0
    pad_above = 10.0
    bore = 4.4

    channel_h = floor + inner
    height = channel_h + pad_above
    hole_z = channel_h + pad_above / 2.0
    hole_y = length / 2.0

    back = Box(wall_thick, length, height, align=(Align.MIN, Align.MIN, Align.MIN))
    floor_box = Box(
        inner + front,
        length,
        floor,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((wall_thick, 0, 0)))
    front_wall = Box(
        front,
        length,
        channel_h,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((wall_thick + inner, 0, 0)))

    body = back + floor_box + front_wall

    hole = Cylinder(bore / 2.0, wall_thick + 4.0).rotate(Axis.Y, -90)
    hole = hole.moved(Location((-2.0, hole_y, hole_z)))
    body = body - hole

    if draft:
        return body

    back_x = body.bounding_box().min.X
    creases = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > channel_h + 0.05
        and e.bounding_box().min.X > back_x + 0.05
        and e not in creases
    )
    return polish(body, keep, 1.0)
