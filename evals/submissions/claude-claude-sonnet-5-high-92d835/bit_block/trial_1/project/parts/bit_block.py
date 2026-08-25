from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    rows=2,
    wall_gap=2.0,
    edge_margin=2.0,
    pocket_depth=12.0,
    floor_thickness=3.0,
    chamfer_size=0.8,
    draft=False,
):
    """Bench block that holds driver bits upright, shank-down, in a grid of pockets.

    shank_diameter: how wide a bit's shank is across, so pockets grip without slop
    columns: how many pockets sit side by side along the long edge
    rows: how many pockets deep, front to back
    wall_gap: material left between neighbouring pocket walls
    edge_margin: material left between the outermost pocket walls and the block's sides
    pocket_depth: how far a pocket bores down for the bit to stand in
    floor_thickness: solid material kept under the pockets
    chamfer_size: the lead-in chamfer at every pocket mouth and the top perimeter
    """
    if shank_diameter <= 0:
        reject(f"shank_diameter {shank_diameter} must be positive", param="shank_diameter")
    if columns < 1:
        reject(f"columns {columns} must be at least 1", param="columns")
    if rows < 1:
        reject(f"rows {rows} must be at least 1", param="rows")
    if wall_gap < 2.0:
        reject(f"wall_gap {wall_gap} is under the 2mm minimum wall: raise it to 2.0 or more", param="wall_gap")
    if edge_margin < 2.0:
        reject(f"edge_margin {edge_margin} is under the 2mm minimum wall: raise it to 2.0 or more", param="edge_margin")
    if floor_thickness < 2.0:
        reject(f"floor_thickness {floor_thickness} is under the 2mm minimum wall: raise it to 2.0 or more", param="floor_thickness")
    if chamfer_size < 0.8:
        reject(f"chamfer_size {chamfer_size} is under the 0.8mm chamfer floor: raise it to 0.8 or more", param="chamfer_size")

    pocket_dia = shank_diameter + 0.3
    pitch = pocket_dia + wall_gap
    block_x = 2 * edge_margin + columns * pocket_dia + (columns - 1) * wall_gap
    block_y = 2 * edge_margin + rows * pocket_dia + (rows - 1) * wall_gap
    height = floor_thickness + pocket_depth

    body = Box(block_x, block_y, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    x0 = -(columns - 1) * pitch / 2
    y0 = -(rows - 1) * pitch / 2
    for c in range(columns):
        for r in range(rows):
            pocket = Pos(x0 + c * pitch, y0 + r * pitch, height - pocket_depth) * Cylinder(
                pocket_dia / 2, pocket_depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            body = body - pocket

    if draft:
        return body

    # The top perimeter and every pocket mouth are the only edges entirely in the
    # top plane; the pocket floors and the bottom perimeter stay untouched.
    lead_in = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - height) < 1e-6 and abs(e.bounding_box().max.Z - height) < 1e-6
    )
    return chamfer(lead_in, chamfer_size)
