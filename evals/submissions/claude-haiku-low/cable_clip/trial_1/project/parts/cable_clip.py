from nurb import *

@part
def cable_clip(bundle_diameter: float = 8.0) -> Solid:
    """
    Screw-down cable clip holding a cable bundle.

    bundle_diameter: outer diameter of the cable bundle in mm
    """

    # Derived dimensions
    channel_inner_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    channel_wall_thickness = 2.4
    base_thickness = 3.0
    channel_outer_width = channel_inner_width + 2 * channel_wall_thickness
    part_length_y = 12.0
    mounting_tab_length_x = 10.0
    hole_diameter = 4.2

    total_x = channel_outer_width + mounting_tab_length_x
    total_z = base_thickness + channel_depth

    # Main solid block containing channel and tab
    part = Box(total_x, part_length_y, total_z)

    # Subtract the open-top channel cavity
    channel_cavity = Box(channel_inner_width, part_length_y, channel_depth)
    channel_cavity = channel_cavity.move(Pos(channel_wall_thickness, 0, base_thickness))
    part = part.cut(channel_cavity)

    # Subtract the mounting tab through-hole (4.2 mm diameter)
    hole = Cylinder(hole_diameter / 2, base_thickness)
    hole = hole.move(Pos(
        channel_outer_width + mounting_tab_length_x / 2,
        part_length_y / 2,
        base_thickness / 2
    ))
    part = part.cut(hole)

    # Apply polish to exposed edges, excluding concave edges and bottom edges
    concave = concave_edges(part)
    edges_to_polish = []
    for edge in part.edges():
        if edge in concave:
            continue
        # Check if edge is on the bottom face (Z=0)
        edge_min_z = min(v.Z for v in edge.vertices())
        if edge_min_z > 0.01:  # Not on the bottom
            edges_to_polish.append(edge)

    if edges_to_polish:
        return polish(part, edges_to_polish, 1.0)
    return part
