from nurb import *

AXIS_HEIGHT = 18.0
CLEARANCE = 0.2
WALL = 2.6
LENGTH = 22.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while the finish dries.

    pole_diameter: width of the pole this rest holds
    """
    inner_r = pole_diameter / 2.0 + CLEARANCE
    if inner_r >= AXIS_HEIGHT - 1.2:
        reject(
            f"pole_diameter {pole_diameter} needs a cradle deeper than the 18mm axis; use a smaller pole",
            param="pole_diameter",
        )
    if pole_diameter < 8.0:
        reject(
            f"pole_diameter {pole_diameter} is too small for a 120 degree cradle under the 18mm axis; use a larger pole",
            param="pole_diameter",
        )

    height = AXIS_HEIGHT
    width = 2.0 * (inner_r + WALL)

    block = Box(width, LENGTH, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    groove = Cylinder(
        inner_r,
        LENGTH + 4.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    groove = groove.rotate(Axis.X, 90).translate((0, 0, AXIS_HEIGHT))
    body = block - groove

    if draft:
        return body
    bed = body.bounding_box().min.Z
    cradle = new_edges(block, combined=body)
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 0.05)
    keep = keep.filter_by(lambda e: e not in cradle)
    return polish(body, keep, 1.0)
