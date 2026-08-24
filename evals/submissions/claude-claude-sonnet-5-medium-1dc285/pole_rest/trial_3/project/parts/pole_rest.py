from math import cos, radians, sin

from nurb import *


@part
def pole_rest(pole_diameter=20.0, length=22.0, draft=False):
    """
    pole_diameter: the diameter of the pole this rest cradles
    length: how long the rest is along the pole, front to back
    """
    pole_radius = pole_diameter / 2
    axis_height = 18.0  # fixed by the bench: the pole always rides this high

    gap = 0.3  # clearance between the pole and the cradle surface
    groove_radius = pole_radius + gap
    half_angle = radians(70.0)  # 140 degrees of contact, clear of a 120 minimum

    rim_height = axis_height - groove_radius * cos(half_angle)
    if rim_height <= 3.0:
        reject(
            f"pole_diameter {pole_diameter} leaves only {rim_height:.1f}mm of block "
            "below the groove rim: lower pole_diameter so the cradle has room to sit "
            "under the fixed 18mm axis height",
            param="pole_diameter",
        )

    backing = 1.6  # material kept behind the contact arc, above the 1.2mm minimum
    shoulder = 1.5  # flat rim left outside the groove opening
    half_width = sin(half_angle) * (groove_radius + backing) + shoulder
    width = 2 * half_width

    body = Box(width, length, rim_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    groove = Cylinder(
        groove_radius,
        length * 2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        rotation=(90, 0, 0),
    )
    groove = Pos(0, 0, axis_height) * groove
    body -= groove

    if draft:
        return body

    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    return polish(body, keep, 1.0)
