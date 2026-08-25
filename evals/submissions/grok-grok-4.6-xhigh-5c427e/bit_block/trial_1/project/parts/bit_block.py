from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5):
    """A bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: how wide a bit shank measures across
    columns: how many pockets sit along the long side
    """
    web, depth, floor, cham = 2.0, 12.0, 3.0, 0.8
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_d = shank_diameter + 0.3
    r = pocket_d / 2
    pitch = pocket_d + web
    x = columns * pitch + web
    y = 2 * pitch + web
    z = floor + depth

    body = Pos(x / 2, y / 2, z / 2) * Box(x, y, z)
    for col in range(columns):
        for row in range(2):
            cx = web + r + col * pitch
            cy = web + r + row * pitch
            body -= Pos(cx, cy, z - depth / 2) * Cylinder(r, depth)

    # Mouth rims and the top perimeter all sit on the top face; one call chamfers
    # both. Two passes (or a selector from before the pockets were cut) fail the
    # 2.0 web, which is only just above 2 * 0.8 of face between neighbouring edges.
    top = body.faces().sort_by(Axis.Z)[-1]
    return chamfer(top.edges(), cham)
