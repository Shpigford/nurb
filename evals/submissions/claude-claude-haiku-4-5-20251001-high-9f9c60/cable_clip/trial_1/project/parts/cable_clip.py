from nurb import *

@part
def cable_clip(bundle_diameter: float = 8.0) -> "Solid":
    """Screw-down cable clip for holding bundled cables.

    bundle_diameter: diameter of the cable bundle to hold
    """

    # Derived dimensions
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    tab_height = 3.0
    hole_diameter = 4.2

    # Main body dimensions
    main_width = 2 * wall_thickness + channel_width
    total_height = base_thickness + channel_depth

    # Create main body (positioned to sit on Z=0 with correct X/Y positioning)
    # Since Box is centered, we need to position it and then shift to align with origin
    body = Box(main_width, part_length, total_height)
    body = body.translate((main_width / 2, 0, total_height / 2))

    # Create channel cutout (centered in the channel space, positioned correctly)
    channel_void = Box(channel_width, part_length, channel_depth)
    channel_void = channel_void.translate((wall_thickness + channel_width / 2, 0, base_thickness + channel_depth / 2))

    # Subtract channel to create walls
    body = body - channel_void

    # Create mounting tab (positioned to extend from main body in +X direction)
    tab = Box(tab_length, part_length, tab_height)
    tab = tab.translate((main_width + tab_length / 2, 0, tab_height / 2))

    # Union body and tab
    result = body.fuse(tab)

    # Create and subtract through-hole in tab (centered in tab)
    hole_x = main_width + tab_length / 2
    hole_y = 0
    hole = Cylinder(radius=hole_diameter / 2, height=tab_height)
    hole = hole.translate((hole_x, hole_y, tab_height / 2))
    result = result - hole

    # Polish: chamfer exposed edges only (1mm)
    # Exclude: channel edges (fit-critical), bed-contact edges, concave edges
    if not draft:
        bed_face = [f for f in result.faces() if f.center.Z < 0.1][0]
        bed_edges = bed_face.edges()

        # Channel faces (the interior surfaces of the channel)
        channel_faces = [f for f in result.faces()
                        if (abs(f.center.X - (wall_thickness + channel_width/2)) < 0.1 or
                            abs(f.center.Z - (base_thickness + channel_depth/2)) < 0.1) and
                           f.center.Z > base_thickness - 0.1]
        channel_edges = set()
        for f in channel_faces:
            channel_edges.update(f.edges())

        # Get all edges and filter out those to exclude
        all_edges = result.edges()
        keep_edges = [e for e in all_edges
                     if e not in bed_edges and
                        e not in channel_edges and
                        is_convex(e, *e.faces())]

        # Apply chamfer
        if keep_edges:
            result = chamfer(keep_edges, 1.0)

    return result
