from nurb import *

# Pole axis is fixed in the world: along Y, 18 mm above the bed, centred in X.
AXIS_HEIGHT = 18.0
# Gap keeps finish off the plastic (must stay in 0.1..0.4 so the cradle both
# clears and still supports).
CLEARANCE = 0.25
# Radial backing behind the contact; 1.2 mm is the functional floor, 3 mm
# prints as a real wall after the 1 mm polish on the inner and outer rims.
WALL = 3.0
# Along the pole; long enough that end chamfers still leave well over 2/3
# of the length as a full cradle.
REST_LENGTH = 24.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A bench rest that cradles a freshly finished pole while it dries.

    Several of these stand in a row; the pole lies along Y across them.

    pole_diameter: width of the pole this rest holds
    """
    radius = pole_diameter / 2.0
    inner = radius + CLEARANCE
    bottom_under_seat = AXIS_HEIGHT - inner
    if bottom_under_seat < 1.2:
        reject(
            f"pole_diameter {pole_diameter} leaves only {bottom_under_seat:.2f}mm "
            f"under the seat at axis height {AXIS_HEIGHT}; the pole has to stay "
            f"small enough that the cradle keeps 1.2mm of material under it",
            param="pole_diameter",
        )
    if pole_diameter < 2.0:
        reject(
            f"pole_diameter {pole_diameter} is under 2mm, too small to cradle",
            param="pole_diameter",
        )

    width = 2.0 * (inner + WALL)
    height = AXIS_HEIGHT

    body = Box(width, REST_LENGTH, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Cylinder defaults to +Z; spin it onto Y and sit its axis on the pole axis.
    trough = Cylinder(inner, REST_LENGTH + 4.0)
    trough = trough.rotate(Axis.X, 90)
    trough = trough.move(Location((0, 0, AXIS_HEIGHT)))
    body -= trough

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    # The trough's end-face arcs, chamfered together with the long rims,
    # leave four sub-1mm2 corners. Polish everything else, including the
    # long rims (a lead-in for drop-in) and the outer box.
    keep = []
    for e in body.edges():
        if e.bounding_box().min.Z <= bed + 1e-3:
            continue
        if e in concave:
            continue
        ebb = e.bounding_box()
        y_span = ebb.max.Y - ebb.min.Y
        x_span = ebb.max.X - ebb.min.X
        if y_span < 1.0 and x_span > inner:
            continue
        keep.append(e)
    return polish(body, keep, 1.0)
