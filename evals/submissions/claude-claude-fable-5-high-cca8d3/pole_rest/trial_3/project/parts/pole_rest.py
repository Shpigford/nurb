from nurb import *

# The rests stand in a row on the bench, so the pole's axis height is the one
# dimension the row fixes: exactly 18.0 above the bed, for every rest.
POLE_AXIS_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    rest_length=22.0,
    wall_thickness=3.2,
    pole_gap=0.25,
    draft=False,
):
    """A bench rest that cradles a freshly finished pole while it dries.

    pole_diameter: how thick the pole is, measured across
    rest_length: how long the rest runs along the pole
    wall_thickness: how much material backs the seat at its thinnest
    pole_gap: extra room around the pole so the soft finish never binds
    """
    pole_r = pole_diameter / 2.0
    seat_r = pole_r + pole_gap
    half_width = seat_r + wall_thickness

    if pole_gap < 0.1:
        reject(
            "pole_gap %.2f would let the seat touch the wet finish: keep it at 0.1 or more"
            % pole_gap,
            param="pole_gap",
        )
    if pole_gap > 0.35:
        reject(
            "pole_gap %.2f holds the seat too far off the pole to cradle it: keep it under 0.35"
            % pole_gap,
            param="pole_gap",
        )
    if POLE_AXIS_HEIGHT - seat_r < 4.0:
        reject(
            "pole_diameter %.1f leaves under 4mm of material below the seat at the fixed "
            "18mm axis height: this rest only fits poles up to %.1f across"
            % (pole_diameter, 2 * (POLE_AXIS_HEIGHT - 4.0 - pole_gap)),
            param="pole_diameter",
        )
    if wall_thickness < 3.0:
        reject(
            "wall_thickness %.1f leaves the seat rim under the 2mm minimum wall once "
            "the 1mm chamfer comes off the top edge: keep it at 3.0 or more"
            % wall_thickness,
            param="wall_thickness",
        )
    if rest_length < 20.0:
        reject(
            "rest_length %.1f is under the 20mm the pole needs to sit on: raise it"
            % rest_length,
            param="rest_length",
        )

    # A plinth whose top face sits exactly at the pole's axis height, with the
    # seat cut as a half cylinder: a 180-degree cradle, and nothing above the
    # axis for the pole to hit on its way straight down into the seat.
    block = Pos(0, 0, POLE_AXIS_HEIGHT / 2) * Box(
        2 * half_width, rest_length, POLE_AXIS_HEIGHT
    )
    groove = Pos(0, 0, POLE_AXIS_HEIGHT) * Rot(90, 0, 0) * Cylinder(
        seat_r, rest_length + 2.0
    )
    body = block - groove

    if draft:
        return body

    # Chamfer the outside only: the seat and its rim are fit geometry, and the
    # bottom-face edges lie in the bed. Vertical corners and the top outer
    # edges all live on the outer walls, so select by that.
    bed = body.bounding_box().min.Z
    eps = 1e-4

    def outer(e):
        b = e.bounding_box()
        on_wall = max(abs(b.min.X), abs(b.max.X)) > half_width - eps
        runs_flat_in_x = (b.max.X - b.min.X) < eps
        above_bed = b.max.Z > bed + eps
        return on_wall and runs_flat_in_x and above_bed

    keep = body.edges().filter_by(outer)
    return polish(body, keep, 1.0)
