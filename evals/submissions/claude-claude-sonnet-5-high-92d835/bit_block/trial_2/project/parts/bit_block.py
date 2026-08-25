from nurb import *

ROWS = 2                     # pocket rows; fixed, only columns is a parameter
POCKET_CLEARANCE = 0.3       # pocket diameter over shank diameter
WALL_BETWEEN_POCKETS = 2.0   # material between neighbouring pocket walls
EDGE_MARGIN = 2.0            # material from the outermost pocket wall to the block side
FLOOR = 3.0                  # solid material under the pockets
POCKET_DEPTH = 12.0          # how deep each pocket is cut
CHAMFER = 0.8                # pocket mouth and top perimeter lead-in


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """
    shank_diameter: the bit shanks' diameter, measured across, in mm
    columns: how many pocket columns the grid has (rows are fixed at 2)
    """
    if columns < 1:
        reject(f"columns {columns} must be at least 1", param="columns")

    pocket_dia = shank_diameter + POCKET_CLEARANCE
    if pocket_dia < 2.0:
        reject(
            f"shank_diameter {shank_diameter} gives a {pocket_dia:.2f}mm pocket, "
            f"under the 2mm minimum hole: raise shank_diameter above {2.0 - POCKET_CLEARANCE}",
            param="shank_diameter",
        )

    pitch = pocket_dia + WALL_BETWEEN_POCKETS
    width = (columns - 1) * pitch + pocket_dia + 2 * EDGE_MARGIN
    depth = (ROWS - 1) * pitch + pocket_dia + 2 * EDGE_MARGIN
    height = FLOOR + POCKET_DEPTH

    body = Pos(0, 0, height / 2) * Box(width, depth, height)

    pocket_z = height - POCKET_DEPTH / 2
    x0 = -(columns - 1) * pitch / 2
    y0 = -(ROWS - 1) * pitch / 2
    pockets = None
    for c in range(columns):
        for r in range(ROWS):
            placed = Pos(x0 + c * pitch, y0 + r * pitch, pocket_z) * Cylinder(pocket_dia / 2, POCKET_DEPTH)
            pockets = placed if pockets is None else pockets + placed

    body -= pockets

    if draft:
        return body

    top_edges = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - height) < 1e-6 and abs(e.bounding_box().max.Z - height) < 1e-6
    )
    return polish(body, top_edges, CHAMFER)
