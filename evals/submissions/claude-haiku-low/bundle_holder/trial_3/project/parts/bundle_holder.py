from nurb import *

@part
def bundle_holder(bundle_diameter=8.0):
    """Wall-mounted cable bundle holder with M4 screw mount."""

    clearance = 0.4
    bundle_opening = bundle_diameter + clearance  # 8.4 mm

    # Part dimensions
    part_length = 20.0  # Y direction
    back_width = 12.0  # Z direction (width of mounting face)
    back_depth = 3.0  # X direction (depth from wall)

    # Bundle support geometry
    # The bundle sits in a channel that's:
    # - Supported from below (1.0mm material underneath)
    # - Blocked from sliding away (1.0mm material in front)

    support_height = 1.0  # material height supporting bundle from below
    lip_width = 1.0  # width of front lip preventing forward movement

    # Create the mounting plate with integral supports
    # Using boolean operations to maintain single solid
    mounting_base = Box(back_depth, part_length, back_width)

    # Create M4 screw hole
    screw_hole = Cylinder(2.2, back_depth + 1, rotation=(0, 90, 0))
    screw_hole = screw_hole.move(Location((0, part_length / 2, back_width / 2)))

    # Remove the upper portion to create space for the bundle
    # This leaves a support shelf at the bottom for the bundle to rest on
    upper_space = Box(
        back_depth + 2,  # cut through
        part_length + 2,
        back_width - support_height - bundle_opening  # remove all but support + bundle space
    )
    # Position this cutout at the top
    upper_space_z = (back_width - support_height - bundle_opening) / 2 + support_height + bundle_opening / 2
    upper_space = upper_space.move(Location((back_depth / 2, 0, upper_space_z)))

    # Remove space for the bundle width (open side for insertion)
    side_space = Box(
        back_depth - lip_width,  # cut from front, leave lip at back
        part_length + 2,
        bundle_opening
    )
    # Position centered on the support
    side_z = -back_width / 2 + support_height + bundle_opening / 2
    side_space = side_space.move(Location((lip_width + (back_depth - lip_width) / 2, 0, side_z)))

    # Combine into body
    body = mounting_base - screw_hole - upper_space - side_space

    if draft:
        return body

    # Polish pass
    bed = body.bounding_box().min.Z
    back_x = body.bounding_box().min.X

    # Polish exposed edges (not back face or bed)
    keep = body.edges().filter_by(
        lambda e: (
            e.bounding_box().min.Z > bed + 0.1 and
            e.bounding_box().min.X > back_x + 0.05
        )
    )

    return polish(body, keep, 1.0)
