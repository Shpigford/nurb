from nurb import *


@part
def pole_rest(pole_diameter=20.0):
    """A low, open cradle for supporting a freshly finished pole.

    pole_diameter: measured width across the pole
    """
    pole_radius = pole_diameter / 2.0
    clearance = 0.2
    cradle_radius = pole_radius + clearance

    length = 24.0
    outer_width = pole_diameter + 2.0
    # Keeping the rim 0.48 radii below the axis provides a little over
    # 120 degrees of close cylindrical support at every pole diameter.
    cradle_top = 18.0 - 0.48 * cradle_radius

    body = Box(outer_width, length, cradle_top)
    bed = body.bounding_box().min.Z
    axis_height = bed + 18.0
    cavity = Cylinder(cradle_radius, length + 2.0)
    cavity = cavity.rotate(Axis.X, 90).translate((0, 0, axis_height))
    return body - cavity
