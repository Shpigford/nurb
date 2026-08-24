from nurb import *

# The pole sits with its axis along Y at this height, independent of diameter.
AXIS_HEIGHT = 18.0
# Soft finish: stay off the coating, but close enough to cradle it.
CLEARANCE = 0.1


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    rest_length=24.0,
    wall=2.4,
    draft=False,
):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: measured across the pole; the seat radius follows this
    rest_length: how far the rest runs along the pole
    wall: thickness of the cradle beside the pole
    """
    if pole_diameter <= 0:
        reject("pole_diameter must be positive", param="pole_diameter")
    inner_r = pole_diameter / 2.0 + CLEARANCE
    if AXIS_HEIGHT - inner_r < 2.0:
        reject(
            f"pole_diameter {pole_diameter} puts the seat under 2mm above the bed",
            param="pole_diameter",
        )
    if wall < 2.0:
        reject("wall must be at least 2mm", param="wall")
    if rest_length < 20.0:
        reject("rest_length must be at least 20mm along the pole", param="rest_length")

    half_width = inner_r + wall
    block = Box(2 * half_width, rest_length, AXIS_HEIGHT)
    block = block.move(Location((0, 0, AXIS_HEIGHT / 2)))

    seat = Cylinder(inner_r, rest_length + 4)
    seat = seat.rotate(Axis.X, 90).move(Location((0, 0, AXIS_HEIGHT)))

    body = block - seat

    if draft:
        return body
    # Chamfer the outer box only. Polishing the seat rims leaves sliver faces.
    def outer_box(e):
        bb = e.bounding_box()
        if bb.min.Z < 0.05:
            return False
        at_outer = min(abs(bb.center().X - half_width), abs(bb.center().X + half_width)) < 0.2
        long_y = (bb.max.Y - bb.min.Y) > rest_length - 1.0
        tall = (bb.max.Z - bb.min.Z) > AXIS_HEIGHT - 2.0
        return at_outer and (long_y or tall)

    keep = body.edges().filter_by(outer_box)
    return polish(body, keep, 1.0)
