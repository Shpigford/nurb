from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """
    shank_diameter: the bit shanks' diameter, so pockets grip without binding
    columns: how many pockets sit side by side (always 2 rows deep)
    """
    rows = 2
    wall_gap = 2.0  # material left between neighbouring pocket walls
    edge_gap = 2.0  # material left from the outermost pocket wall to the block's side
    pocket_depth = 12.0
    floor_thickness = 3.0
    chamfer_size = 0.8

    if columns < 1:
        reject(f"columns {columns} has to be at least 1", param="columns")

    pocket_dia = shank_diameter + 0.3
    if pocket_dia < 2.0:
        reject(
            f"shank_diameter {shank_diameter} gives a {pocket_dia:g}mm pocket, "
            "under nurb's 2mm minimum hole size: raise shank_diameter above 1.7",
            param="shank_diameter",
        )

    pitch = pocket_dia + wall_gap
    length = columns * pocket_dia + (columns - 1) * wall_gap + 2 * edge_gap
    width = rows * pocket_dia + (rows - 1) * wall_gap + 2 * edge_gap
    height = floor_thickness + pocket_depth

    block = Box(length, width, height)
    top = height / 2

    x0 = -(columns - 1) * pitch / 2
    y0 = -(rows - 1) * pitch / 2
    for i in range(columns):
        for j in range(rows):
            x = x0 + i * pitch
            y = y0 + j * pitch
            pocket = Pos(x, y, top - pocket_depth / 2) * Cylinder(
                pocket_dia / 2, pocket_depth
            )
            block -= pocket

    if draft:
        return block

    def at_top(edge):
        bb = edge.bounding_box()
        return abs(bb.min.Z - top) < 1e-6 and abs(bb.max.Z - top) < 1e-6

    top_edges = block.edges().filter_by(at_top)
    perimeter = top_edges.filter_by(GeomType.LINE)
    pocket_mouths = top_edges.filter_by(GeomType.CIRCLE)

    return chamfer(perimeter + pocket_mouths, chamfer_size)
