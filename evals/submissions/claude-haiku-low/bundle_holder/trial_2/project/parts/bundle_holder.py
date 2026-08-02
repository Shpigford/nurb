from nurb import *

@part
def bundle_holder(bundle_diameter: float = 8.0) -> Solid:
    """
    Wall-mounted cable bundle holder.

    bundle_diameter: diameter of the cable bundle in mm
    """

    # Clearance and retention parameters
    clearance = 0.4  # clearance around bundle
    retention_margin = 1.0  # required travel distance before hitting part

    # Channel geometry
    bundle_radius = bundle_diameter / 2
    channel_width = bundle_diameter + 2 * clearance
    channel_depth_x = bundle_radius + clearance + retention_margin

    # Part dimensions - balanced for function and weight
    part_length_y = 30.0  # length along wall
    back_wall_thickness = 2.4  # mounting face thickness
    side_wall_thickness = 0.9  # economical side walls
    base_thickness = 1.0  # floor thickness

    # Channel height: just enough to hold and release bundle safely
    # Total = base + (radius with clearance bottom and top)
    channel_height_z = 2 * (bundle_radius + clearance)  # 8.8 mm total

    # Total dimensions
    total_width_x = back_wall_thickness + channel_depth_x + side_wall_thickness
    total_height_z = base_thickness + channel_height_z

    # Create main body
    body = Box(
        length=total_width_x,
        width=part_length_y,
        height=total_height_z
    )

    # Create channel cavity (U-shaped pocket)
    channel_cavity = Box(
        length=channel_depth_x,
        width=channel_width,
        height=channel_height_z
    )

    # Position cavity
    from nurb import Location, Vector
    cavity_x = back_wall_thickness
    cavity_y = (part_length_y - channel_width) / 2
    cavity_z = base_thickness

    loc = Location(Vector(cavity_x, cavity_y, cavity_z))
    channel_cavity = channel_cavity.locate(loc)

    # Subtract the channel
    holder = body - channel_cavity

    # Add mounting boss at base
    m4_hole_diameter = 4.4
    boss_radius = 3.2
    boss_y = 4.0

    # Mounting boss from back face
    boss = Cylinder(
        radius=boss_radius,
        height=back_wall_thickness
    )
    boss_loc = Location(Vector(0, boss_y, 0))
    boss = boss.locate(boss_loc)

    holder = holder + boss

    # Drill M4 screw hole
    screw_hole = Cylinder(
        radius=m4_hole_diameter / 2,
        height=back_wall_thickness + 1
    )
    hole_loc = Location(Vector(-0.5, boss_y, 0))
    screw_hole = screw_hole.locate(hole_loc)

    holder = holder - screw_hole

    # Polish exposed edges
    edges_to_polish = concave_edges(holder)
    return polish(holder, edges_to_polish, 1.0)
