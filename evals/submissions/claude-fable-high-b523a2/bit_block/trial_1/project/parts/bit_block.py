from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    rows=2,
    pocket_depth=12.0,
    floor_thickness=3.0,
    wall_between_pockets=2.0,
    pocket_clearance=0.3,
    draft=False,
):
    """A bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: how wide a bit's shank measures across
    columns: how many pockets along the long side
    rows: how many pockets along the short side
    pocket_depth: how deep each bit sinks into the block
    floor_thickness: solid material under the pockets
    wall_between_pockets: material between neighbouring pockets and out to the sides
    pocket_clearance: extra pocket width over the shank so bits drop in freely
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if rows < 1:
        reject("rows must be at least 1", param="rows")

    pocket_dia = shank_diameter + pocket_clearance
    if pocket_dia < 2.0:
        reject(
            f"pocket diameter {pocket_dia:.1f} is under the 2mm printable hole floor: "
            "raise shank_diameter",
            param="shank_diameter",
        )

    pitch = pocket_dia + wall_between_pockets
    width = (columns - 1) * pitch + pocket_dia + 2 * wall_between_pockets
    depth = (rows - 1) * pitch + pocket_dia + 2 * wall_between_pockets
    height = pocket_depth + floor_thickness

    chamfer_size = 0.8
    if wall_between_pockets <= 2 * chamfer_size:
        reject(
            f"wall_between_pockets {wall_between_pockets:.1f} leaves no room for the "
            f"{chamfer_size}mm lead-in chamfers: raise it above {2 * chamfer_size:.1f}",
            param="wall_between_pockets",
        )

    body = Pos(0, 0, height / 2) * Box(width, depth, height)
    x0 = -(columns - 1) * pitch / 2
    y0 = -(rows - 1) * pitch / 2
    pockets = [
        Pos(x0 + i * pitch, y0 + j * pitch, height - pocket_depth / 2)
        * Cylinder(pocket_dia / 2, pocket_depth)
        for i in range(columns)
        for j in range(rows)
    ]
    body = body - pockets

    if draft:
        return body

    # The exact lead-in on every pocket mouth and the top outer perimeter is all
    # the edge-breaking this part gets: bottom and vertical edges stay sharp so
    # the bounding box is exact. Every edge lying in the top plane is that set.
    top = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > height - 1e-6
    )
    return chamfer(top, chamfer_size)
