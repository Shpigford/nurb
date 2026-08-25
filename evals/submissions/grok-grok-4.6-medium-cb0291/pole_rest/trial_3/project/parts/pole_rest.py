from nurb import *
import math

# The pole's axis is a bench constraint, not a function of diameter.
AXIS_Z = 18.0
# 0.1mm is the fit floor; 0.4mm is the support ceiling. 0.25 sits in that band.
CLEARANCE = 0.25
# 1.2mm of backing is required; 2.4mm is a printable wall.
WALL = 2.4
# 130° of wrap leaves margin over the 120° support arc after the ends are chamfered.
WRAP_DEG = 130.0
LENGTH = 24.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A bench rest that cradles a freshly finished pole while it dries.

    pole_diameter: width of the pole this rest holds
    """
    if pole_diameter < 10.0:
        reject(
            f"pole_diameter {pole_diameter:g} is too small for a printable cradle; "
            "raise it above 10",
            param="pole_diameter",
        )

    inner_r = pole_diameter / 2.0 + CLEARANCE
    floor = WALL
    if AXIS_Z - inner_r < floor:
        limit = 2.0 * (AXIS_Z - floor - CLEARANCE)
        reject(
            f"pole_diameter {pole_diameter:g} puts the cradle through the bed "
            f"with the axis at {AXIS_Z:g}; keep it below {limit:g}",
            param="pole_diameter",
        )

    half = math.radians(WRAP_DEG / 2.0)
    height = AXIS_Z - inner_r * math.cos(half) + 0.8
    width = 2.0 * ((inner_r + WALL) * math.sin(half) + WALL)

    body = Box(width, LENGTH, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    groove = Pos(0, 0, AXIS_Z) * Rot(90, 0, 0) * Cylinder(
        inner_r,
        LENGTH + 4.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    body = body - groove

    if draft:
        return body

    bed = body.bounding_box().min.Z
    # Leave the cylindrical seat alone so the contact arc stays a true cradle.
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 0.05)
    keep = keep - concave_edges(body)
    keep = keep - body.faces().filter_by(GeomType.CYLINDER).edges()
    return polish(body, keep, 1.0)
