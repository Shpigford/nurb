from nurb import *

# Pole axis is fixed in the workshop frame: along Y, 18mm above the bed,
# centered on the rest in X. Geometry below derives from pole_diameter only.
AXIS_HEIGHT = 18.0
CLEARANCE = 0.2  # radial gap to soft finish; must stay in [0.1, 0.4]
BACKING = 1.4  # solid behind the cradle surface (>= 1.2)
LENGTH = 22.0  # along Y; several rests share the pole across a row
OUTER_MARGIN = 0.9  # extra beyond backing so a 1mm polish still leaves wall


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: how wide the pole is across; the cradle and width rebuild from this
    """
    if pole_diameter < 8.0:
        reject(
            f"pole_diameter {pole_diameter} is under 8mm: too small for a printable cradle",
            param="pole_diameter",
        )

    seat_r = pole_diameter / 2.0 + CLEARANCE
    floor = AXIS_HEIGHT - seat_r
    if floor < 2.4:
        reject(
            f"pole_diameter {pole_diameter} leaves only {floor:.2f}mm under the seat "
            f"at axis height {AXIS_HEIGHT}: lower pole_diameter or the floor vanishes",
            param="pole_diameter",
        )

    half_width = seat_r + BACKING + OUTER_MARGIN
    width = 2.0 * half_width
    height = AXIS_HEIGHT

    body = Box(width, LENGTH, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Open-top semicylinder along Y: pole drops straight in from +Z.
    cutter = Pos(0, 0, AXIS_HEIGHT) * Rot(90, 0, 0) * Cylinder(seat_r, LENGTH + 4.0)
    body = body - cutter

    if draft:
        return body

    # Polish only the outer box frame. Chamfering the cradle rim as well eats the
    # narrow shoulder (backing + margin) from both sides and leaves sliver faces.
    bed = body.bounding_box().min.Z

    def outer_frame(e):
        ebb = e.bounding_box()
        if ebb.min.Z <= bed + 1e-4:
            return False
        # Cradle rim and end-arcs sit within seat_r of the pole axis — leave them.
        mx = (ebb.min.X + ebb.max.X) / 2.0
        mz = (ebb.min.Z + ebb.max.Z) / 2.0
        if (mx * mx + (mz - AXIS_HEIGHT) * (mz - AXIS_HEIGHT)) <= (seat_r + 0.05) ** 2:
            return False
        # Short top shoulders at the Y ends cannot take a 1mm chamfer cleanly.
        if e.length < 2.0 + 1e-3:
            return False
        return True

    keep = body.edges().filter_by(outer_frame)
    return polish(body, keep, 1.0)
