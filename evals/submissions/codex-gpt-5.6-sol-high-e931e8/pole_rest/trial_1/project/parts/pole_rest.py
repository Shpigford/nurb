from math import cos, radians

from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A low, full-length cradle for a freshly finished pole.

    pole_diameter: measured diameter of the pole that rests in the cradle
    """
    pole_radius = pole_diameter / 2.0
    pole_axis_height = 18.0
    radial_clearance = 0.2
    cradle_radius = pole_radius + radial_clearance

    # The cavity is exposed over 130 degrees around the lower half of the pole.
    # Keeping the body a little wider than the cavity leaves over 1.2 mm of
    # backing behind the complete contact arc, including at both shoulders.
    cradle_arc = 130.0
    body_height = pole_axis_height - cradle_radius * cos(radians(cradle_arc / 2.0))
    body_width = 2.0 * (cradle_radius + 2.2)
    body_length = max(24.0, pole_diameter + 4.0)

    body = Pos(0, 0, body_height / 2.0) * Box(body_width, body_length, body_height)
    cutter = Pos(0, 0, pole_axis_height) * Rot(90, 0, 0) * Cylinder(
        cradle_radius, body_length + 2.0
    )
    return body - cutter
