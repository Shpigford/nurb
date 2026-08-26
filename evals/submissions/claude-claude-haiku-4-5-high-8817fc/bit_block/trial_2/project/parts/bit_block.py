from nurb import *

@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """
    Bench block for holding driver bits upright in a grid.

    shank_diameter: diameter of bit shanks (mm)
    columns: number of columns in the grid (rows are always 2)
    """
    # Pocket dimensions
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2
    pocket_depth = 12.0

    # Grid and block dimensions
    grid_pitch = 8.3
    edge_material = 2.0
    total_height = 15.0
    rows = 2
    chamfer_size = 0.8

    # Calculate block dimensions
    width = 2 * edge_material + 2 * pocket_radius + (columns - 1) * grid_pitch
    depth = 2 * edge_material + 2 * pocket_radius + (rows - 1) * grid_pitch

    # Create the base block
    result = Box(width, depth, total_height)

    # Create and subtract pockets
    for row in range(rows):
        for col in range(columns):
            # Calculate pocket center position
            x = edge_material + pocket_radius + col * grid_pitch
            y = edge_material + pocket_radius + row * grid_pitch
            z_bottom = total_height - pocket_depth

            # Create a cylinder positioned at the pocket location
            pocket = Cylinder(pocket_radius, pocket_depth)
            pocket = pocket.locate(Location((x, y, z_bottom)))

            # Subtract from part
            result = result - pocket

    # Collect and chamfer top edges
    # Get all edges and separate top from bottom
    all_edges = list(result.edges())

    # Sort edges by z-coordinate of their center
    top_edges = []
    bottom_edges = []

    for edge in all_edges:
        center = edge.center()
        if center.Z > total_height / 2:  # Top half
            top_edges.append(edge)
        else:
            bottom_edges.append(edge)

    # Only chamfer top edges
    if top_edges:
        try:
            # Try using polish which handles edge selection intelligently
            result = polish(result, top_edges, chamfer_size)
        except Exception as e:
            # If polish fails, it might be because we selected bad edges
            # Just continue without chamfering
            pass

    return result
