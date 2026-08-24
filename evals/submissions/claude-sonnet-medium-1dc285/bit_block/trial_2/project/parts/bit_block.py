from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """
    shank_diameter: bit shank width across, the pockets open 0.3mm wider than this
    columns: how many pockets sit side by side in each row
    """
    rows = 2
    pocket_dia = shank_diameter + 0.3
    pocket_depth = 12.0
    floor_thickness = 3.0
    edge_margin = 2.0
    pitch = pocket_dia + 2.0

    height = floor_thickness + pocket_depth
    width = (columns - 1) * pitch + pocket_dia + 2 * edge_margin
    depth = (rows - 1) * pitch + pocket_dia + 2 * edge_margin

    body = Box(width, depth, height)
    top_z = body.bounding_box().max.Z

    x0 = -(columns - 1) * pitch / 2
    y0 = -(rows - 1) * pitch / 2

    for c in range(columns):
        for r in range(rows):
            x = x0 + c * pitch
            y = y0 + r * pitch
            pocket = Pos(x, y, top_z - pocket_depth) * Cylinder(
                pocket_dia / 2, pocket_depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            body -= pocket

    if draft:
        return body

    top_faces = body.faces().filter_by(Axis.Z)
    top_face = max(top_faces, key=lambda f: f.center().Z)
    edges = top_face.edges()

    return chamfer(edges, 0.8)
