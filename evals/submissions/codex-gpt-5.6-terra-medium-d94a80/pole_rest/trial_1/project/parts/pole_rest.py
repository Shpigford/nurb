from nurb import *


@part
def pole_rest(pole_diameter: float = measured("pole_diameter")):
    """A low, printable trough for a freshly finished pole.

    pole_diameter: outside diameter of the pole being supported
    """
    # The pole's centerline is deliberately fixed at z=18 mm.  The slightly
    # oversized cylindrical cut is both the finish-safe clearance and the
    # continuous, 180-degree lower cradle.
    pole_radius = pole_diameter / 2
    pole_axis_height = 18.0
    clearance = 0.20
    cradle_radius = pole_radius + clearance

    length = 24.0
    base_width = max(36.0, pole_diameter + 16.0)
    base_height = 3.0
    support_width = pole_diameter + 2.0
    support_height = pole_axis_height - base_height

    base = Box(
        base_width, length, base_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    support = Pos(0, 0, base_height) * Box(
        support_width, length, support_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # A through-cut gives the pole a clear vertical drop path; its bottom half
    # leaves a generous backed circular seat rather than two bearing edges.
    cutter = (
        Pos(0, 0, pole_axis_height)
        * Rot(90, 0, 0)
        * Cylinder(cradle_radius, length + 2.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    )
    return (base + support) - cutter
