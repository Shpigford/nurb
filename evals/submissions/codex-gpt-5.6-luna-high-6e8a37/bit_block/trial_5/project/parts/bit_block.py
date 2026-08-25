from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """Bench block for upright driver bits.

    shank_diameter: diameter of the bit shank measured across the metal
    columns: number of pockets in the left-to-right row
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be greater than 0", param="shank_diameter")

    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pitch = pocket_diameter + 2.0
    block_width = 4.0 + columns * pocket_diameter + (columns - 1) * 2.0
    block_depth = 4.0 + 2 * pocket_diameter + 2.0
    block_height = 15.0
    floor_thickness = 3.0
    lead_in = 0.8

    vertical_block = Box(
        block_width,
        block_depth,
        block_height - lead_in,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    lower_outline = Pos(
        block_width / 2.0,
        block_depth / 2.0,
        block_height - lead_in,
    ) * Rectangle(block_width, block_depth)
    upper_outline = Pos(
        block_width / 2.0,
        block_depth / 2.0,
        block_height,
    ) * Rectangle(
        block_width - 2.0 * lead_in,
        block_depth - 2.0 * lead_in,
    )
    outer_lead_in = loft([lower_outline, upper_outline], ruled=True)
    block = vertical_block.fuse(outer_lead_in)

    pockets = []
    for column in range(columns):
        for row in range(2):
            x = 2.0 + pocket_radius + column * pitch
            y = 2.0 + pocket_radius + row * pitch
            straight_pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_radius,
                block_height - floor_thickness - lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            mouth = Pos(x, y, block_height - lead_in) * Cone(
                pocket_radius,
                pocket_radius + lead_in,
                lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            pockets.append(straight_pocket.fuse(mouth))

    pocket_tools = pockets[0].fuse(*pockets[1:])
    block = block.cut(pocket_tools)

    if draft:
        return block

    return block
