from nurb import *

@part
def bit_block(
    shank_diameter: float = 6.0,
    columns: int = 5,
):
    """Hold driver bits upright in a grid of pockets.

    shank_diameter: diameter of the bit shanks in mm
    columns: number of columns in the pocket grid
    """

    # Derived dimensions
    pocket_dia = shank_diameter + 0.3
    pocket_depth = 12.0
    block_height = 15.0
    floor_thickness = 3.0
    rows = 2
    pitch = 8.3
    margin = 2.0
    chamfer_size = 0.8

    # Calculate block dimensions from column and row counts
    block_width = 2 * margin + pocket_dia * columns + 2 * (columns - 1)
    block_depth = 2 * margin + pocket_dia * rows + 2 * (rows - 1)

    # Create base block (centered at origin)
    part = Box(block_width, block_depth, block_height)

    # Subtract pockets at grid positions
    # Box is centered, so it goes from -width/2 to +width/2
    # Pockets go from -height/2 + floor_thickness to +height/2
    # The center Z position for cylinders: (-height/2 + floor_thickness + height/2) / 2
    pocket_radius = pocket_dia / 2
    z_center = -block_height / 2 + floor_thickness + pocket_depth / 2

    # Grid positions: margin + radius offset from edges
    x_start = -block_width / 2 + margin + pocket_radius
    y_start = -block_depth / 2 + margin + pocket_radius

    for col in range(columns):
        x = x_start + col * pitch
        for row in range(rows):
            y = y_start + row * pitch

            pocket = Cylinder(pocket_radius, pocket_depth)
            pocket = pocket.located(Location((x, y, z_center)))
            part = part - pocket

    # Chamfer top edges (pocket mouths and outer perimeter)
    # Top face is at Z = +block_height/2
    top_z = block_height / 2
    top_faces = [f for f in part.faces() if abs(f.center().Z - top_z) < 0.01]
    top_edges = []
    for face in top_faces:
        top_edges.extend(face.edges())

    if top_edges:
        part = part.chamfer(chamfer_size, None, top_edges)

    return part
