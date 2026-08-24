from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A screw-down clip for a cable bundle.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    clearance = 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2

    channel_width = bundle_diameter + clearance
    outer_width = channel_width + 2.0 * wall_thickness

    base = Box(
        outer_width,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Box(
        wall_thickness,
        part_length,
        bundle_diameter,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((0.0, 0.0, base_thickness)))
    right_wall = Box(
        wall_thickness,
        part_length,
        bundle_diameter,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((outer_width - wall_thickness, 0.0, base_thickness)))
    tab = Box(
        tab_length,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((outer_width, 0.0, 0.0)))

    body = base + left_wall + right_wall + tab
    hole = Cylinder(
        screw_hole_width / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((outer_width + tab_length / 2.0, part_length / 2.0, 0.0)))
    return body - hole
