from nurb import *

@part
def leg_cup(
    leg_width: "mm" = measured("leg_width"),
    leg_depth: "mm" = measured("leg_depth"),
    lift: "mm" = measured("lift"),
):
    """Cup to slip over a table leg and level it"""

    wall = 2.0
    pocket_height = 8.0
    clearance = 0.4

    # Calculate dimensions
    pocket_width = leg_width + clearance
    pocket_depth = leg_depth + clearance
    outer_width = pocket_width + 2 * wall
    outer_depth = pocket_depth + 2 * wall
    total_height = lift + pocket_height

    # Create the outer box, positioned so bottom is at z=0
    cup = Box(outer_width, outer_depth, total_height)
    cup = cup.locate(Location((0, 0, total_height / 2)))

    # Create the pocket cutout, positioned so it starts at z=lift
    pocket = Box(pocket_width, pocket_depth, pocket_height)
    pocket = pocket.locate(Location((0, 0, lift + pocket_height / 2)))

    # Cut the pocket from the cup
    result = cup - pocket

    # Polish exposed edges, excluding concave edges and bed-level edges
    concave = concave_edges(result)
    edges_to_polish = []
    for edge in result.edges():
        # Skip concave edges (pocket interior)
        if edge in concave:
            continue
        # Skip edges entirely on the bed face
        bbox = edge.bounding_box()
        if bbox.min.Z < 0.1 and bbox.max.Z < 0.1:
            continue
        edges_to_polish.append(edge)

    result = polish(result, edges_to_polish, 1.0)

    return result
