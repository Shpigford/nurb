from nurb import *


@part
def bit_block(
    shank_diameter=6.0,
    columns=5,
    rows=2,
    wall=2.0,
    floor=3.0,
    pocket_depth=12.0,
    draft=False,
):
    """
    shank_diameter: the diameter of the bit shanks the pockets hold
    columns: how many pockets sit side by side across the block
    rows: how many pockets sit front to back
    wall: material left between neighbouring pocket walls, and from the outer
        pockets to the block's sides
    floor: solid material left under the pockets
    pocket_depth: how deep each pocket is cut
    """
    pocket_dia = shank_diameter + 0.3
    pitch = pocket_dia + wall
    height = floor + pocket_depth

    width = (columns - 1) * pitch + pocket_dia + 2 * wall
    depth = (rows - 1) * pitch + pocket_dia + 2 * wall

    body = Box(width, depth, height)
    top_z = height / 2

    xs = [(-(columns - 1) / 2 + i) * pitch for i in range(columns)]
    ys = [(-(rows - 1) / 2 + j) * pitch for j in range(rows)]

    pockets = [
        Pos(x, y, top_z - pocket_depth / 2)
        * Cylinder(radius=pocket_dia / 2, height=pocket_depth)
        for x in xs
        for y in ys
    ]
    body = body - pockets

    if draft:
        return body

    top_edges = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top_z) < 1e-6
        and abs(e.bounding_box().max.Z - top_z) < 1e-6
    )
    chamfer_edges = top_edges.filter_by(
        lambda e: e.geom_type in (GeomType.LINE, GeomType.CIRCLE)
    )
    return polish(body, chamfer_edges, 0.8)
