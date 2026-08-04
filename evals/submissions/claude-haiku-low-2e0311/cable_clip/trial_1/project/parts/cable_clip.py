from nurb import *

@part
def cable_clip(bundle_diameter=8.0):
    """
    Screw-down cable clip that holds a cable bundle.

    bundle_diameter: diameter of cable bundle in mm
    """
    # Channel geometry derived from bundle size
    channel_width = bundle_diameter + 0.4  # 8.4
    channel_depth = bundle_diameter       # 8.0
    wall_thickness = 2.4
    base_thickness = 3.0
    clip_length = 12.0
    hole_diameter = 4.2
    tab_length = 10.0

    # Overall dimensions
    channel_box_width = 2 * wall_thickness + channel_width  # 13.2
    total_width = channel_box_width + tab_length  # 23.2

    # Base (23.2 x 12.0 x 3.0): covers full footprint from Z=0
    base = Box(total_width, clip_length, base_thickness)
    base = base.translate((total_width / 2, clip_length / 2, base_thickness / 2))

    # Left wall (2.4 x 12.0 x 8.0): sits on base at Z=3.0
    left_wall = Box(wall_thickness, clip_length, channel_depth)
    left_wall = left_wall.translate((wall_thickness / 2, clip_length / 2, base_thickness + channel_depth / 2))

    # Right wall (2.4 x 12.0 x 8.0): at X = channel_box_width - wall_thickness
    right_wall = Box(wall_thickness, clip_length, channel_depth)
    right_wall = right_wall.translate((channel_box_width - wall_thickness / 2, clip_length / 2, base_thickness + channel_depth / 2))

    # Mounting tab (10.0 x 12.0 x 3.0): extends from right wall at same Z level as base
    tab = Box(tab_length, clip_length, base_thickness)
    tab = tab.translate((channel_box_width + tab_length / 2, clip_length / 2, base_thickness / 2))

    # Combine all pieces into one solid
    part = base.fuse(left_wall).fuse(right_wall).fuse(tab)

    # Create through-hole in tab (4.2 mm diameter, vertical)
    hole_radius = hole_diameter / 2
    hole = Cylinder(hole_radius, base_thickness)
    hole_center_x = channel_box_width + tab_length / 2
    hole_center_y = clip_length / 2
    hole = hole.translate((hole_center_x, hole_center_y, base_thickness / 2))

    # Subtract the hole
    part = part.cut(hole)

    return part
