from nurb import part, polish

@part
def bit_block(
    shank_diameter: float = 6.0,
    columns: int = 5,
):
    """
    Bench block for holding driver bits upright.

    shank_diameter: bit shank diameter in mm
    columns: number of pocket columns (2 rows always)
    """
    from build123d import Box, Cylinder, Location

    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2
    pocket_depth = 12.0
    total_height = 15.0
    grid_pitch = 8.3
    margin = 2.0
    rows = 2

    # Calculate block dimensions from grid geometry
    block_width = 2 * margin + pocket_diameter + (columns - 1) * grid_pitch
    block_depth = 2 * margin + pocket_diameter + (rows - 1) * grid_pitch

    # Base solid block
    base = Box(block_width, block_depth, total_height)

    # Create pocket cylinders and subtract them
    result = base
    for col in range(columns):
        for row in range(rows):
            # Pocket center position
            x = margin + pocket_radius + col * grid_pitch
            y = margin + pocket_radius + row * grid_pitch
            z = total_height - pocket_depth

            pocket = Cylinder(pocket_radius, pocket_depth, mode="a")
            pocket.locate(Location((x, y, z)))
            result -= pocket

    # Collect top edges for polishing
    # Only chamfer: outer perimeter top edges + circular pocket edges
    # Exclude internal edges between pockets
    bbox = result.bounding_box()
    max_z = bbox.max.Z - 0.01

    top_edges = []
    perimeter_edges = []

    # Collect all edges on top faces
    for face in result.faces():
        center = face.center()
        if center.Z >= max_z:  # Top faces
            for edge in face.edges():
                # Check if edge is on perimeter (large X or Y values)
                # or if it's a circular edge (pocket mouth)
                edge_pts = edge.bounding_box()
                is_perimeter = (
                    abs(edge_pts.min.X) < 0.1 or abs(edge_pts.max.X - block_width) < 0.1 or
                    abs(edge_pts.min.Y) < 0.1 or abs(edge_pts.max.Y - block_depth) < 0.1
                )

                # Check if circular (pocket mouth)
                is_circular = False
                try:
                    # Circular edges have specific geometry
                    from build123d import Geom
                    geom = edge.geom
                    is_circular = hasattr(geom, 'is_circle') and geom.is_circle()
                except:
                    pass

                if is_perimeter or is_circular:
                    top_edges.append(edge)

    # Polish collected edges with 0.8 mm chamfer
    if top_edges:
        result = polish(result, top_edges, 0.8)

    return result
