from nurb import *

@part
def cable_clip(bundle_diameter=8.0):
    """Cable clip for holding a cable bundle.

    bundle_diameter: cable bundle diameter in mm
    """

    # Dimensions derived from bundle_diameter
    inner_width = bundle_diameter + 0.4
    inner_depth = bundle_diameter

    # Fixed dimensions
    wall = 2.4
    base = 3.0
    length = 12.0  # Y direction

    # Outer dimensions
    body_width = 2 * wall + inner_width  # 13.2
    body_height = base + inner_depth  # 11.0
    tab_width = 10.0
    hole_radius = 4.2 / 2

    # Create main channel body with flat bottom at Z=0
    # Body positioned from (0,0,0) to (body_width, length, body_height)
    main = Box(body_width, length, body_height)
    main = main.locate(Location((body_width/2, length/2, body_height/2)))

    # Cut the channel from the top
    # Channel interior: width=inner_width, length=length, depth=inner_depth
    # Positioned: centered in X, full length in Y, from z=base to z=body_height
    channel = Box(inner_width, length, inner_depth)
    channel = channel.locate(Location((body_width/2, length/2, base + inner_depth/2)))
    main = main - channel

    # Add mounting tab on the right side
    # Tab: width=tab_width, length=length, height=base
    # Positioned: from x=body_width to x=body_width+tab_width, y=0 to y=length, z=0 to z=base
    tab = Box(tab_width, length, base)
    tab = tab.locate(Location((body_width + tab_width/2, length/2, base/2)))
    main = main + tab

    # Drill through-hole in the tab, centered
    hole = Cylinder(hole_radius, base)
    hole = hole.locate(Location((body_width + tab_width/2, length/2, base/2)))
    main = main - hole

    return main
