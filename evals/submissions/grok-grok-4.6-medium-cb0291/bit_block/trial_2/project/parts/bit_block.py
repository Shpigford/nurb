from nurb import *

ROWS = 2
CLEARANCE = 0.3
WALL = 2.0
FLOOR = 3.0
POCKET_DEPTH = 12.0
LEAD = 0.8


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: measured width of a bit shank
    columns: number of pockets along the long side
    """
    if columns < 1:
        reject("need at least one column of pockets", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pocket_dia = shank_diameter + CLEARANCE
    pocket_r = pocket_dia / 2.0
    pitch = pocket_dia + WALL
    inset = WALL + pocket_r
    length = 2.0 * inset + (columns - 1) * pitch
    width = 2.0 * inset + (ROWS - 1) * pitch
    height = FLOOR + POCKET_DEPTH

    if length <= 2.0 * LEAD or width <= 2.0 * LEAD:
        reject(
            "shank_diameter leaves no top face after the 0.8mm perimeter chamfer; raise it",
            param="shank_diameter",
        )

    body = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Four triangular prisms, each longer than its edge, so they meet at plane
    # intersections instead of leaving sliver triangles at the corners.
    overrun = 2.0
    wedges = [
        extrude(
            Plane.YZ.offset(-length / 2.0 - overrun)
            * Polygon(
                (width / 2.0, height),
                (width / 2.0 - LEAD, height),
                (width / 2.0, height - LEAD),
            ),
            amount=length + 2.0 * overrun,
        ),
        extrude(
            Plane.YZ.offset(-length / 2.0 - overrun)
            * Polygon(
                (-width / 2.0, height),
                (-width / 2.0, height - LEAD),
                (-width / 2.0 + LEAD, height),
            ),
            amount=length + 2.0 * overrun,
        ),
        extrude(
            Plane.XZ.offset(-width / 2.0 - overrun)
            * Polygon(
                (length / 2.0, height),
                (length / 2.0 - LEAD, height),
                (length / 2.0, height - LEAD),
            ),
            amount=width + 2.0 * overrun,
        ),
        extrude(
            Plane.XZ.offset(-width / 2.0 - overrun)
            * Polygon(
                (-length / 2.0, height),
                (-length / 2.0, height - LEAD),
                (-length / 2.0 + LEAD, height),
            ),
            amount=width + 2.0 * overrun,
        ),
    ]
    body = body - sum(wedges[1:], start=wedges[0])

    extra = 0.5
    cutters = []
    for col in range(columns):
        for row in range(ROWS):
            x = -length / 2.0 + inset + col * pitch
            y = -width / 2.0 + inset + row * pitch
            bore = Pos(x, y, FLOOR) * Cylinder(
                pocket_r,
                height - FLOOR + extra,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            lead_in = Pos(x, y, height - LEAD) * Cone(
                pocket_r,
                pocket_r + LEAD + extra,
                LEAD + extra,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            cutters.append(bore + lead_in)

    body = body - sum(cutters[1:], start=cutters[0])
    return body
