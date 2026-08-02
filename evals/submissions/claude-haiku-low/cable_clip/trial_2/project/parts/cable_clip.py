from nurb import *

@part
def cable_clip(bundle_diameter: float = 8.0):
    """A screw-down cable clip for holding cable bundles.

    bundle_diameter: diameter of the cable bundle to hold
    """

    # Derived dimensions (all in mm)
    inner_width = bundle_diameter + 0.4
    inner_depth = bundle_diameter
    wall_thick = 2.4
    base_height = 3.0
    clip_length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2

    # Total width: walls + channel + walls + tab
    total_width = wall_thick + inner_width + wall_thick + tab_length

    # Create base block (entire footprint, centered at XY, sitting on Z=0)
    base = Box(total_width, clip_length, base_height, align=(Align.MIN, Align.MIN, Align.MIN))

    # Create left wall above base (at x=0, full length Y, sitting on base)
    left_wall = Box(wall_thick, clip_length, inner_depth, align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = left_wall.moved(Location((0, 0, base_height)))

    # Create right wall above base (at x=wall_thick+inner_width, full length Y, sitting on base)
    right_wall = Box(wall_thick, clip_length, inner_depth, align=(Align.MIN, Align.MIN, Align.MIN))
    right_wall = right_wall.moved(Location((wall_thick + inner_width, 0, base_height)))

    # Combine base with walls
    shape = base + left_wall + right_wall

    # Subtract the channel opening (cut out the inner area)
    channel = Box(inner_width, clip_length, inner_depth, align=(Align.MIN, Align.MIN, Align.MIN))
    channel = channel.moved(Location((wall_thick, 0, base_height)))
    shape = shape - channel

    # Subtract the mounting hole in the tab
    hole_x = wall_thick + inner_width + wall_thick + tab_length / 2
    hole_y = clip_length / 2
    hole = Cylinder(hole_diameter / 2, base_height + 1, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    hole = hole.moved(Location((hole_x, hole_y, base_height / 2)))
    shape = shape - hole

    return shape
