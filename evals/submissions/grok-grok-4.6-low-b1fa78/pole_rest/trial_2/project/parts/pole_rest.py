from nurb import *

AXIS_HEIGHT = 18.0
CLEARANCE = 0.1
BACKING = 2.4


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    draft=False,
):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: measured width of the pole; the seat follows this size
    """
    if pole_diameter < 8.0:
        reject(
            "pole_diameter is too small for a printable cradle at the 18 mm axis",
            param="pole_diameter",
        )

    inner_r = pole_diameter / 2.0 + CLEARANCE
    if inner_r >= AXIS_HEIGHT - 2.0:
        reject(
            "pole_diameter is too large: the seat would cut through the bed at the 18 mm axis",
            param="pole_diameter",
        )

    length = 24.0
    wall = BACKING
    width = 2.0 * (inner_r + wall)
    height = AXIS_HEIGHT

    body = Box(width, length, height).moved(Location((0, 0, height / 2.0)))
    seat = Cylinder(inner_r, length + 4.0).rotate(Axis.X, 90).moved(
        Location((0, 0, AXIS_HEIGHT))
    )
    body = body - seat

    if draft:
        return body

    bed = body.bounding_box().min.Z

    def polishable(edge):
        bb = edge.bounding_box()
        if bb.min.Z <= bed + 0.05:
            return False
        # Leave the seat rims sharp so chamfers cannot sliver the groove.
        if abs(bb.center().X) < inner_r + 1.8:
            return False
        return True

    keep = body.edges().filter_by(polishable)
    return polish(body, keep, 1.0)
