from math import cos, radians, sin

from nurb import *


@part
def pole_rest(pole_diameter=20.0, draft=False):
    """A grounded cradle for a freshly finished pole.

    pole_diameter: diameter of the pole being dried; the measured value is 20.0 mm
    and the cradle keeps 0.1 mm radial clearance.
    """
    axis_height = 18.0
    pole_radius = pole_diameter / 2.0
    clearance = 0.1
    cradle_wall = 1.4
    # Each 15 degree chord sits 7.5 degrees inside its endpoint radius.  Offset
    # the construction radius so the chord, too, stays at the required clearance.
    inner_radius = (pole_radius + clearance) / cos(radians(7.5))
    outer_radius = inner_radius + cradle_wall

    # A broad, flat-footed base makes the part print in its working orientation.
    # Its top stops below the pole, leaving the curved cradle as the only close fit.
    base_height = axis_height - inner_radius - cradle_wall
    base = Pos(0, 0, base_height / 2.0) * Box(24.0, 24.0, base_height)

    # Draw the Y-extruded cross-section in X/Z.  The inner arc is sampled finely
    # enough to stay within 0.4 mm of the pole.  Vertical outsides and level
    # shoulders are support-free, unlike the outside of a full annular cylinder.
    arc = []
    for angle in range(210, 331, 15):
        a = radians(angle)
        arc.append((inner_radius * cos(a), axis_height + inner_radius * sin(a)))
    right_z = arc[-1][1]
    left_x = -outer_radius
    right_x = outer_radius
    profile = arc + [
        (right_x, right_z),
        (right_x, base_height - 0.2),
        (left_x, base_height - 0.2),
        (left_x, arc[0][1]),
    ]
    section = make_face(Polygon(*profile))
    # The rotation sends extrusion +Z toward -Y, so translate it back by half
    # its length to centre the cradle on Y=0 like the base.
    cradle = Pos(0, 12.0, 0) * Rot(90, 0, 0) * extrude(section, amount=24.0)
    result = base + cradle

    if draft:
        return result
    return result
