from nurb import *

@part
def bundle_holder(bundle_diameter=8.0):
    """Wall-mounted cable bundle holder.

    Retains a horizontal cable bundle against a wall with a single M4 screw mount.

    bundle_diameter: the diameter of the cable bundle to hold (mm)
    """

    # Retention clearance and channel sizing
    clearance = 0.4
    hole_dia = bundle_diameter + 2 * clearance

    # Screw specs
    screw_hole_dia = 4.4
    bore_depth = 2.4

    # Part dimensions
    length_y = 15.0  # along bundle direction
    height_z = 10.0  # back face height
    depth_x = 10.0   # depth into wall

    # Main mounting block
    body = Box(depth_x, length_y, height_z)

    # Carve open-top channel for bundle retention
    # Channel sits open from the top, held from falling by its own shape
    channel_width = hole_dia  # 8.4 mm to hold 8.0 mm bundle
    channel_depth = 5.5  # enough to prevent 1.0 mm downward movement

    # Carved from top surface, leaving bottom intact for support
    channel = Box(depth_x + 2, channel_width, channel_depth)
    channel_z = height_z / 2 + 0.3 - channel_depth / 2
    body = body - channel.translate([0, 0, channel_z])

    # Screw hole through the back mounting face
    # Positioned to have solid material around it
    screw_hole = Cylinder(screw_hole_dia / 2, bore_depth + 1.5).rotate(Axis.Y, 90)
    screw_z = height_z / 2 - 2.5
    body = body - screw_hole.translate([-depth_x / 2 + bore_depth / 2, 0, screw_z])

    # Polish exposed edges (exclude back face and bottom)
    if not draft:
        bed = body.bounding_box().min.Z
        back_x = body.bounding_box().min.X

        keep = body.edges().filter_by(lambda e:
            e.bounding_box().min.Z > bed + 0.1 and
            e.bounding_box().min.X > back_x + 0.1
        )

        body = polish(body, keep, 1.0)

    return body
