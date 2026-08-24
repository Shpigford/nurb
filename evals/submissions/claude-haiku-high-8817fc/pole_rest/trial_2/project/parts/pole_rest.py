from nurb import *


@part
def pole_rest(pole_diameter=20.0):
    """
    A cradle that holds a freshly finished pole while it dries. The pole
    is cradled from below along its length, allowing it to be placed and
    removed vertically.

    pole_diameter: diameter of the pole to support, in mm
    """
    pole_radius = pole_diameter / 2.0
    pole_axis_height = 18.0

    base_width = 30.0
    base_length = 25.0
    base_height = 10.0

    base = Box(base_width, base_length, base_height)
    base = base.translate((0, 0, base_height / 2.0))

    support_radius = pole_radius - 0.1
    cyl = Cylinder(radius=support_radius, height=base_length + 2.0)
    cyl = cyl.translate((0, 0, pole_axis_height))

    part = base - cyl

    bed = part.bounding_box().min.Z
    keep = part.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    return polish(part, keep, 1.0)
