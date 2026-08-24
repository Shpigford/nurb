import math

from nurb import *

# How much of the pole's circumference the cradle wraps, centered on the
# bottom. Fixed rather than a slider: drop below 120 degrees and the rest
# stops cradling the pole and starts balancing it on an edge.
CONTACT_HALF_ANGLE = math.radians(75.0)

# The bench interface: the pole's axis always sits this high above the bed,
# centered in X over the rest's footprint, no matter the pole size.
POLE_AXIS_Z = 18.0


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    length=24.0,
    pole_clearance=0.25,
    wall_thickness=3.0,
    draft=False,
):
    """
    pole_diameter: diameter of the pole the rest cradles
    length: how far the cradle runs along the pole
    pole_clearance: gap left between the cradle and the pole's surface
    wall_thickness: material behind the cradle, carrying the pole's weight
    """
    if pole_diameter <= 0:
        reject(f"pole_diameter {pole_diameter} has to be positive", param="pole_diameter")
    if length < 20.0:
        reject(f"length {length} is under the 20mm the pole needs to bear on", param="length")
    if not (0.1 <= pole_clearance <= 0.4):
        reject(
            f"pole_clearance {pole_clearance} has to stay between 0.1 (fit) and 0.4mm (cradle contact)",
            param="pole_clearance",
        )
    if wall_thickness < 1.2:
        reject(
            f"wall_thickness {wall_thickness} is under the 1.2mm the cradle needs behind the pole",
            param="wall_thickness",
        )

    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + pole_clearance
    outer_radius = seat_radius + wall_thickness

    # Flat top of the two horns, set where the cradle arc reaches
    # CONTACT_HALF_ANGLE either side of the pole's lowest point.
    top_z = POLE_AXIS_Z - seat_radius * math.cos(CONTACT_HALF_ANGLE)
    # Half width wide enough to keep wall_thickness of backing behind the
    # contact arc all the way to its rim, plus a little margin.
    half_width = outer_radius * math.sin(CONTACT_HALF_ANGLE) + 1.5

    block = Box(
        2 * half_width,
        length,
        top_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = (
        Pos(0, 0, POLE_AXIS_Z)
        * Rot(X=90)
        * Cylinder(radius=seat_radius, height=length + 2.0)
    )
    body = block - seat

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    seat_face = body.faces().filter_by(GeomType.CYLINDER)[0]
    seat_edges = seat_face.edges()

    def is_vertical_corner(e):
        # The block's 4 vertical corners meet 3 mutually-perpendicular
        # chamfers at one vertex, which leaves a sub-1mm2 sliver triangle.
        # Leaving these square avoids it; the top and end edges still chamfer.
        bb = e.bounding_box()
        return (bb.max.X - bb.min.X) < 1e-6 and (bb.max.Y - bb.min.Y) < 1e-6

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().max.Z > bed
        and e not in concave
        and e not in seat_edges
        and not is_vertical_corner(e)
    )
    return polish(body, keep, 1.0)
