from nurb import *

@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5) -> Part:
    """Bench block to hold driver bits upright.

    shank_diameter: bit shank diameter, adds 0.3mm clearance for pockets
    columns: number of pocket columns in the grid
    """

    rows = 2
    pocket_dia = shank_diameter + 0.3
    pocket_r = pocket_dia / 2
    pocket_depth = 12.0
    floor_h = 3.0
    grid_pitch = 8.3

    # Derived dimensions
    block_w = 2.0 + grid_pitch * columns
    block_d = 2.0 + grid_pitch * rows
    block_h = floor_h + pocket_depth

    # Create base block, bottom at z=0
    base = Box(block_w, block_d, block_h)
    base = base.translate(Vector(0, 0, block_h / 2))

    # Subtract pocket cylinders
    for col in range(columns):
        for row in range(rows):
            # Pocket center coordinates
            x = -block_w/2 + 2.0 + pocket_r + col * grid_pitch
            y = -block_d/2 + 2.0 + pocket_r + row * grid_pitch
            z = block_h - pocket_depth / 2

            hole = Cylinder(radius=pocket_r, height=pocket_depth)
            hole = hole.translate(Vector(x, y, z))
            base = base - hole

    # Chamfer top edges: pocket mouths and outer perimeter (0.8 x 45 degree)
    top_edges = []
    for edge in base.edges():
        # Get edge center point
        try:
            center = edge.center()
            # Check if edge is near the top surface
            if hasattr(center, '__getitem__'):
                z = center[2]
            elif hasattr(center, 'Z'):
                z = center.Z
            else:
                # Try getting attributes
                z = getattr(center, 'z', None)
                if z is None:
                    continue

            if abs(z - block_h) < 0.5:
                top_edges.append(edge)
        except:
            pass

    if top_edges:
        base = polish(base, top_edges, 0.8)

    return base
