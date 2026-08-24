from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall-mounted clip for a cable bundle that runs along the wall.

    bundle_diameter: caliper size of the taped cable bundle
    """
    if bundle_diameter < 4.0:
        reject(
            "bundle_diameter is under 4mm; raise it so the channel can print",
            param="bundle_diameter",
        )

    clearance = 0.4
    inner = bundle_diameter + clearance
    wall = 2.2
    back = 2.6
    length = 14.0
    bore = 4.4
    head = 8.4
    around = 2.2

    floor_top = wall
    channel_top = floor_top + inner
    screw_z = channel_top + around + head / 2.0
    tab_top = screw_z + head / 2.0 + around
    front_x = back + inner
    outer_x = front_x + wall
    y_mid = length / 2.0

    back_plate = Box(back, length, tab_top, align=(Align.MIN, Align.MIN, Align.MIN))
    floor = Box(outer_x, length, wall, align=(Align.MIN, Align.MIN, Align.MIN))
    front = Box(
        wall,
        length,
        channel_top,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    front = front.move(Location((front_x, 0, 0)))

    body = back_plate + floor + front

    hole = Rot(Y=90) * Cylinder(bore / 2.0, back + 4.0)
    hole = hole.move(Location((back / 2.0, y_mid, screw_z)))
    body = body - hole

    return body
