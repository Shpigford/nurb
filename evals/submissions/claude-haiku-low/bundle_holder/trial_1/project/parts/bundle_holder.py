from nurb import *

@part
def bundle_holder(bundle_diameter: float = 8.0):
    """
    Wall-mounted holder for a cable bundle.

    bundle_diameter: diameter of the cable bundle to retain, in mm
    """

    clearance = 0.4
    bundle_space = bundle_diameter + clearance

    depth_x = 11.0
    length_y = 32.0
    height_z = 10.0

    # Create main body
    body = Box(depth_x, length_y, height_z)

    # Cut a narrow channel for bundle retention
    # Channel width matches bundle + clearance, ensuring tight fit
    # Bottom support at Z=0-2 prevents downward motion
    # Front and back walls (each ~1.3mm) provide lateral resistance
    channel = Box(bundle_space, length_y, 8.0)
    channel = channel.translate((0, 0, 2.0))
    body = body.cut(channel)

    # Mount hole through back face for M4 screw
    hole = Box(5.0, 5.0, depth_x + 1.0)
    hole = hole.translate((0, length_y/2 - 2.5, height_z/2 - 2.5))
    body = body.cut(hole)

    # Polish exposed edges (exclude back and bed faces per doctrine)
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 0.1 and e.bounding_box().min.X > 0.1)
    body = polish(body, keep, 1.0)

    return body
