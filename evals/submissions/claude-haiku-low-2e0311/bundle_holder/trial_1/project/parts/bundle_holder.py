from nurb import *

@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """Wall-mounted cable bundle holder with M4 mounting.

    Simple design: a solid mounting block with a semicircular cradle cavity
    and retention walls that prevent bundle from moving down or outward.

    bundle_diameter: diameter of the cable bundle in mm
    """
    # Get measured bundle size for parametric scaling
    dia = measured("bundle_diameter")
    clearance = 0.4
    hole_dia = dia + clearance  # 8.4mm for 8.0mm bundle
    radius = hole_dia / 2  # 4.2mm

    # Dimensions
    length_y = 12.0  # bundle runs along Y
    mount_x = 3.5  # mounting plate thickness (wall-facing)
    cradle_depth_x = 5.5  # cradle extends forward
    total_x = mount_x + cradle_depth_x
    height_z = 10.0  # vertical extent
    bottom_wall = 1.0  # bottom retention wall thickness

    # Create solid rectangular block
    part = Box(total_x, length_y, height_z)

    # Subtract the semicircular cradle from the top
    # Position cylinder at the center of the cradle depth, centered Z
    # Cylinder will be rotated to run along Y axis
    cradle_hole = Cylinder(radius, length_y + 2)
    cradle_hole = cradle_hole.rotate(Axis.X, 90)  # Rotate 90° to align with Y axis
    cradle_hole = cradle_hole.translate((mount_x + cradle_depth_x / 2, 0, radius + 0.5))
    part = part - cradle_hole

    # Carve out the top space above the cradle to make it open
    # Remove a box from the top that includes the cradle area
    top_cutout = Box(cradle_depth_x, length_y + 2, radius + 1.5)
    top_cutout = top_cutout.translate((mount_x + cradle_depth_x / 2, 0, radius + 1.0))
    part = part - top_cutout

    # Subtract screw hole (M4: 4.4mm diameter) through mounting plate
    screw_hole = Cylinder(2.2, mount_x + 0.5)
    screw_hole = screw_hole.rotate(Axis.Y, 90)  # Rotate to X axis
    screw_hole = screw_hole.translate((0, length_y / 2, 0))
    part = part - screw_hole

    if draft:
        return part

    # Polish: chamfer exposed edges except back face and bed
    bed_z = part.bounding_box().min.Z
    back_x = part.bounding_box().min.X
    concave = concave_edges(part)

    exposed = part.edges().filter_by(
        lambda e: (
            e.bounding_box().min.X > back_x + 0.2 and  # Not on back face
            e.bounding_box().max.Z > bed_z + 0.3 and  # Not on bed
            e not in concave  # Not concave edges (where polish forbidden)
        )
    )

    return polish(part, exposed, 1.0)
