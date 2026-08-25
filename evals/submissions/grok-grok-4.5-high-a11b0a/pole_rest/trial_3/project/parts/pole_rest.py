from nurb import *

# Pole axis height above the bed is fixed by the bench layout.
AXIS_HEIGHT = 18.0
# Clear of the soft finish, but still close enough to cradle it.
CLEARANCE = 0.2
# Radial material behind the seat contact.
BACKING = 2.0
# Length along the pole (Y).
LENGTH = 24.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: diameter of the pole this rest holds
    """
    if pole_diameter <= 0:
        reject("pole_diameter must be positive", param="pole_diameter")

    radius = pole_diameter / 2.0
    seat_r = radius + CLEARANCE
    if seat_r >= AXIS_HEIGHT:
        reject(
            f"pole_diameter {pole_diameter} needs a seat deeper than the {AXIS_HEIGHT}mm "
            f"axis height; use a smaller pole",
            param="pole_diameter",
        )

    half_width = seat_r + BACKING
    # Block top sits at the axis so the bore opens as a semicircle: drop-in from above,
    # ~180deg cradle, prints support-free (inner normals face up or out, never down).
    body = Box(2 * half_width, LENGTH, AXIS_HEIGHT)
    body = body.move(Location((0, 0, AXIS_HEIGHT / 2)))

    bore = Cylinder(seat_r, LENGTH + 2, rotation=(90, 0, 0))
    bore = bore.move(Location((0, 0, AXIS_HEIGHT)))
    body = body - bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    bb = body.bounding_box()
    # Soft finish seat stays unchamfered. Only the four outer vertical corners get
    # the polish pass — top-rim chamfers collide into sub-mm slivers at the lips.
    def _outer_vertical(e):
        ebb = e.bounding_box()
        # Skip edges that lie in the bed plane; verticals that only meet the bed are fine.
        if ebb.max.Z <= bed + 1e-3:
            return False
        # Vertical: spans Z, negligible XY length.
        if ebb.max.Z - ebb.min.Z < AXIS_HEIGHT * 0.5:
            return False
        if (ebb.max.X - ebb.min.X) + (ebb.max.Y - ebb.min.Y) > 0.2:
            return False
        # Outer corners only (not the cradle opening).
        on_x = abs(ebb.min.X - bb.min.X) < 0.2 or abs(ebb.max.X - bb.max.X) < 0.2
        on_y = abs(ebb.min.Y - bb.min.Y) < 0.2 or abs(ebb.max.Y - bb.max.Y) < 0.2
        return on_x and on_y

    keep = body.edges().filter_by(_outer_vertical)
    return polish(body, keep, 1.0)
