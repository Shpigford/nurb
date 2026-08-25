from nurb import *


_DEFAULT_SHANK_DIAMETER = float(measured("shank_diameter"))


@part
def bit_block(shank_diameter=_DEFAULT_SHANK_DIAMETER, columns=5, draft=False):
    """A two-row bench block with vertical round pockets for driver bits.

    shank_diameter: diameter of the bit shanks being held
    columns: number of pockets in each row
    """
    if columns < 1:
        reject("columns must be at least 1 so the block has a pocket", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pocket_diameter = shank_diameter + 0.3
    pitch = pocket_diameter + 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = pocket_depth + floor_thickness
    width = (columns - 1) * pitch + pocket_diameter + 4.0
    depth = pitch + pocket_diameter + 4.0

    body = Pos(width / 2, depth / 2, height / 2) * Box(width, depth, height)

    pocket_x = [2.0 + pocket_diameter / 2 + i * pitch for i in range(columns)]
    pocket_y = [2.0 + pocket_diameter / 2, 2.0 + pocket_diameter / 2 + pitch]
    for x in pocket_x:
        for y in pocket_y:
            pocket = Pos(x, y, floor_thickness + pocket_depth / 2) * Cylinder(
                pocket_diameter / 2, pocket_depth
            )
            body = body - pocket

    if draft:
        return body

    # Only edges wholly in the top plane are selected: the outer top perimeter and
    # each pocket mouth. The bottom perimeter and pocket floors stay sharp.
    top_z = body.bounding_box().max.Z
    top_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > top_z - 1e-5
        and edge.bounding_box().max.Z > top_z - 1e-5
    )
    return chamfer(top_edges, length=0.8)
