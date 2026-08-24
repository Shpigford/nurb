from nurb import *

AXIS_HEIGHT = 18.0
CLEARANCE = 0.15
BACKING = 2.2
LENGTH = 22.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Cradle a freshly finished pole while it dries.

    pole_diameter: width of the pole across
    """
    r = pole_diameter / 2.0
    if r <= 0:
        reject("pole_diameter must be positive", param="pole_diameter")
    inner = r + CLEARANCE
    floor = AXIS_HEIGHT - inner
    if floor < 2.0:
        reject(
            f"pole_diameter {pole_diameter} puts the seat closer than 2mm to the bed; lower it",
            param="pole_diameter",
        )

    top_z = AXIS_HEIGHT - 2.0
    outer_r = inner + BACKING
    foot_w = 2.0 * outer_r + 2.0

    body = Box(foot_w, LENGTH, top_z, align=(Align.CENTER, Align.CENTER, Align.MIN))

    seat = Cylinder(inner, LENGTH + 4.0)
    seat = Rotation(X=90) * seat
    seat = Location((0, 0, AXIS_HEIGHT)) * seat

    opening = Box(
        2.0 * inner,
        LENGTH + 4.0,
        50.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    opening = Location((0, 0, AXIS_HEIGHT)) * opening

    body = body - seat - opening

    if draft:
        return body
    bed = body.bounding_box().min.Z
    # Polish only the outer box: leave the seat and its top lips alone so
    # clearance and the 120-degree contact arc stay intact.
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 0.05
        and abs(e.bounding_box().center().X) > inner + 0.5
    )
    return polish(body, keep, 1.0)
