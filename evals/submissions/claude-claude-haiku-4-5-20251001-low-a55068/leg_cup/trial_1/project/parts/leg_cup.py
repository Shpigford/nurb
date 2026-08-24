from nurb import *

@part
def leg_cup():
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift_val = measured("lift")

    # Pocket inner dimensions with clearance
    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    pocket_height = 8.0

    # Wall thickness
    wall = 2.0

    # Overall dimensions
    outer_width = 26.4
    outer_depth = 22.9
    total_height = lift_val + pocket_height

    # Create main solid block, positioned with bottom at Z=0
    main = Box(outer_width, outer_depth, total_height)
    main = main.translate((0, 0, total_height / 2))

    # Create pocket cutout, positioned so it opens from top
    pocket_cutout = Box(pocket_width, pocket_depth, pocket_height)
    pocket_cutout = pocket_cutout.translate((0, 0, lift_val + pocket_height / 2))

    # Subtract pocket from main solid
    result = main - pocket_cutout

    # Polish exposed edges, excluding concave edges (stress concentrators)
    all_edges = result.edges()
    bed_edges = all_edges.filter_by(lambda e: e.bounding_box().min.Z < 0.1)
    concave = concave_edges(result)
    edges_to_polish = all_edges - bed_edges - concave
    result = polish(result, edges_to_polish, 1.0)

    return result
