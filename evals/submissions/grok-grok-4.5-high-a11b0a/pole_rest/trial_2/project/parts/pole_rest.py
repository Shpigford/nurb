from nurb import *

# Pole axis is fixed in the workshop frame: along Y, centred in X, 18 mm above the bed.
AXIS_HEIGHT = 18.0
# Soft finish: cradle close to the pole, never touching. Support wants ≤0.4; fit wants ≥0.1.
CLEARANCE = 0.25
# Radial material behind the cradle contact (rule asks for ≥1.2).
BACKING = 2.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), rest_length=24.0, draft=False):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: diameter of the pole this rest cradles
    rest_length: how long the cradle runs along the pole
    """
    pole_diameter = float(pole_diameter)
    if pole_diameter <= 0:
        reject("pole_diameter must be positive", param="pole_diameter")
    if rest_length < 20.0:
        reject("rest_length must be at least 20 mm along the pole", param="rest_length")

    seat_r = pole_diameter / 2.0 + CLEARANCE
    outer_r = seat_r + BACKING
    if outer_r > AXIS_HEIGHT:
        reject(
            f"pole_diameter {pole_diameter:g} needs a cradle thicker than the "
            f"{AXIS_HEIGHT:g} mm axis height allows; use a smaller pole",
            param="pole_diameter",
        )

    # Block top sits at the axis so the trough is an open semicircle: drop-in from +Z,
    # ~180° of cradle, and the pole is centred over the footprint in X.
    width = 2.0 * outer_r + 2.0  # extra for outer polish without thinning the backing
    height = AXIS_HEIGHT
    body = Pos(0, 0, height / 2.0) * Box(width, rest_length, height)

    # Semicylindrical seat: full cylinder cut from a block that only exists at z ≤ axis.
    cut = Pos(0, 0, AXIS_HEIGHT) * Rot(90, 0, 0) * Cylinder(seat_r, rest_length + 4.0)
    body = body - cut

    if draft:
        return body

    bed = body.bounding_box().min.Z

    # Keep the cradle surface unchamfered so clearance and arc stay honest.
    def on_seat(e):
        c = e.center()
        return abs((c.X**2 + (c.Z - AXIS_HEIGHT) ** 2) ** 0.5 - seat_r) < 0.3

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 0.05 and not on_seat(e)
    )
    return polish(body, keep, 1.0)
