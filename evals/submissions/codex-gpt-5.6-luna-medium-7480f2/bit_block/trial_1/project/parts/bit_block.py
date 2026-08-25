from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """A bench block for storing driver bits upright.

    shank_diameter: diameter of the bit shank being held
    columns: number of pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_diameter = shank_diameter + 0.3
    pitch = pocket_diameter + 2.0
    width = (columns - 1) * pitch + pocket_diameter + 4.0
    depth = pitch + pocket_diameter + 4.0
    height = 15.0
    pocket_floor = 3.0

    # MIN alignment makes z=0 the sharp, full-area bed face.
    body = Box(width, depth, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Five columns by two rows at the default, with the same construction
    # remaining valid when the column count or shank diameter is changed.
    x0 = -((columns - 1) * pitch) / 2.0
    y0 = -pitch / 2.0
    for column in range(columns):
        for row in range(2):
            x = x0 + column * pitch
            y = y0 + row * pitch
            pocket = Pos(x, y, pocket_floor) * Cylinder(
                pocket_diameter / 2.0,
                height - pocket_floor,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body - pocket

    if draft:
        return body

    # Only edges lying entirely in the top plane are selected.  This includes
    # the outer top perimeter and each pocket mouth, while leaving the bottom
    # perimeter and the pocket floors sharp.
    top_edges = body.edges().filter_by(
        lambda edge: (
            abs(edge.bounding_box().min.Z - height) < 1e-6
            and abs(edge.bounding_box().max.Z - height) < 1e-6
        )
    )
    return chamfer(top_edges, length=0.8)
