import math

from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A support-free cradle for a finished pole.

    pole_diameter: diameter of the pole being held
    """
    pole_radius = pole_diameter / 2.0
    clearance = 0.15
    inner_radius = pole_radius + clearance
    axis_height = 18.0
    length = 24.0
    base_width = 32.0
    base_height = 5.5
    # The 130 degree opening leaves a generous drop-in mouth while keeping a
    # continuous, rounded support arc around the lower side of the pole.
    mouth_half_angle = 25.0
    mouth_top = axis_height - inner_radius * math.sin(math.radians(mouth_half_angle))

    base = Pos(0, 0, base_height / 2.0) * Box(base_width, length, base_height)

    # Build a faceted outer envelope whose lower wall is vertical and whose
    # upper shoulder is exactly 45 degrees.  It supports the circular inner
    # surface from the foot instead of leaving a curved underside hanging in
    # mid-air.
    lower = base_height - 0.2
    shoulder_z = axis_height - inner_radius
    shoulder_x = pole_radius + 0.25
    upper_x = shoulder_x + (mouth_top - shoulder_z)
    outline = Polygon(
        (-shoulder_x, lower),
        (shoulder_x, lower),
        (shoulder_x, shoulder_z),
        (upper_x, mouth_top),
        (-upper_x, mouth_top),
        (-shoulder_x, shoulder_z),
    )
    outer_envelope = Pos(0, -length / 2.0, 0) * extrude(
        Plane.XZ * make_face(outline), amount=length, dir=(0, 1, 0)
    )

    # The cutter is centred and turned so its axis runs along Y.  It opens the
    # envelope while retaining the lower 130 degree circular support arc.
    inner = Pos(0, 0, axis_height) * Cylinder(
        inner_radius, length + 0.4, rotation=(90, 0, 0)
    )
    body = base + (outer_envelope - inner)
    return body
