from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter")):
    """Wall-mounted tunnel for a horizontal cable bundle.

    bundle_diameter: measured width of the cable bundle held by the tunnel
    """
    clearance = 0.4
    tunnel_width = bundle_diameter + clearance
    tunnel_radius = tunnel_width / 2

    length = 10.5
    wall_thickness = 2.0
    back_thickness = 3.0

    tunnel_center_x = back_thickness + tunnel_radius
    tunnel_center_z = wall_thickness + tunnel_radius
    tunnel_front = tunnel_center_x + tunnel_radius + wall_thickness
    tunnel_height = tunnel_center_z + tunnel_radius + wall_thickness

    # Keep the pan head and its driver clear of the cable tunnel.
    driver_radius = 4.2
    screw_center_z = tunnel_height + driver_radius + 0.8
    plate_height = screw_center_z + driver_radius

    body = Box(
        back_thickness,
        length,
        plate_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    body += Box(
        tunnel_front,
        length,
        tunnel_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    cable_path = Pos(tunnel_center_x, length / 2, tunnel_center_z) * Cylinder(
        tunnel_radius,
        length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        rotation=(90, 0, 0),
    )
    body -= cable_path

    screw_bore = Pos(back_thickness / 2, length / 2, screw_center_z) * Cylinder(
        2.2,
        back_thickness + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        rotation=(0, 90, 0),
    )
    body -= screw_bore

    return body
