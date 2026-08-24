from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """Driver bit holder block with upright pockets for driver bits.

    shank_diameter: diameter of the driver bit shank in mm
    columns: number of columns in the grid (default 5 for 5x2 layout)
    """
    # Derived parameters from requirements
    pocket_diameter = shank_diameter + 0.3
    pocket_depth = 12.0
    total_height = 15.0
    chamfer_size = 0.8

    # Grid parameters
    grid_pitch = pocket_diameter + 2.0  # Pocket diameter + 2mm gap
    margin = 2.0  # Margin from outer edge to pocket edge
    rows = 2

    # Calculate block dimensions to match requirements exactly
    width = 2 * margin + (columns - 1) * grid_pitch + pocket_diameter
    depth = 2 * margin + (rows - 1) * grid_pitch + pocket_diameter

    # Create base block (centered at origin)
    base = Box(width, depth, total_height)

    # Create and subtract pockets (cylinders going from top to base)
    pocket_radius = pocket_diameter / 2.0

    for col in range(columns):
        for row in range(rows):
            # Calculate pocket center position in original coordinate system (0 to width, 0 to depth)
            x_orig = margin + pocket_radius + col * grid_pitch
            y_orig = margin + pocket_radius + row * grid_pitch

            # Adjust for centered box coordinate system
            # Box is centered, so it goes from -width/2 to width/2, -depth/2 to depth/2, -height/2 to height/2
            x_centered = x_orig - width / 2
            y_centered = y_orig - depth / 2
            z_centered = total_height / 2 - pocket_depth / 2

            # Create pocket cylinder with base at z=3.0, top at z=15.0
            pocket = Cylinder(pocket_radius, pocket_depth)
            # Move to center position in the centered coordinate system
            pocket = pocket.move(Location((x_centered, y_centered, z_centered)))

            # Subtract pocket from base
            base -= pocket

    # Keep bottom edges sharp, chamfer everything else
    bottom_z = 0.0
    keep_edges = base.edges().filter_by(lambda e: e.bounding_box().min.Z > bottom_z + 0.01)

    base = polish(base, keep_edges, chamfer_size)

    return base
