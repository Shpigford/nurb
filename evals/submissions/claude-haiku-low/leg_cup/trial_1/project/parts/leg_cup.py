from nurb import part, polish, concave_edges, measured
from build123d import Box

@part
def leg_cup(leg_width=measured("leg_width"), leg_depth=measured("leg_depth"), lift=measured("lift")):
    """Slip-over foot cup that lifts a workbench level.

    The leg's foot drops into the pocket from above; the solid floor lifts the bench.

    leg_width: width of the leg pocket (mm)
    leg_depth: depth of the leg pocket (mm)
    lift: height of solid floor (mm)
    """
    # Pocket inner dimensions (with 0.4mm clearance)
    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    pocket_height = 8.0
    wall = 2.0

    # Outer dimensions
    outer_width = pocket_width + 2 * wall
    outer_depth = pocket_depth + 2 * wall
    total_height = lift + pocket_height

    # Create solid body
    body = Box(outer_width, outer_depth, total_height)

    # Create pocket cutout positioned at lift height
    # Box() creates centered boxes, so pocket is naturally centered in X/Y
    # For Z: pocket floor at 'lift' mm from body bottom
    # In centered coords (body center at 0): pocket center should be at
    # lift - total_height/2 + pocket_height/2 = lift - total_height/2 + pocket_height/2
    pocket_z_offset = lift - total_height / 2 + pocket_height / 2

    pocket = Box(pocket_width, pocket_depth, pocket_height)
    pocket = pocket.translate((0, 0, pocket_z_offset))

    # Subtract pocket from body
    cup = body - pocket

    # Polish only the top edges (pocket rim) - exclude concave and bottom edges
    concave = set(concave_edges(cup))
    edges_to_polish = []

    for edge in cup.edges():
        if edge in concave:
            continue
        # Only polish edges above the base (avoid bed contact)
        sp = edge.start_point()
        ep = edge.end_point()
        min_z = min(float(sp[2]), float(ep[2])) if hasattr(sp, '__getitem__') else min(sp.Z, ep.Z)
        if min_z > 0.5:
            edges_to_polish.append(edge)

    if edges_to_polish:
        cup = polish(cup, edges_to_polish, 1.0)

    return cup
