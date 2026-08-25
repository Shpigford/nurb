from nurb import *

# The pole's axis is fixed by the bench interface: 18.0mm above the bed,
# centered in X. Not a parameter, so flexing pole_diameter never moves it.
AXLE_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=20.0,
    rest_length=25.0,
    clearance=0.25,
    wall_thickness=3.0,
    draft=False,
):
    """A cradle that a freshly finished pole rests in while it dries.

    pole_diameter: diameter of the pole this rest cradles
    rest_length: how long the rest is along the pole's axis
    clearance: gap left between the cradle and the pole's surface
    wall_thickness: material behind the cradle, holding the pole's weight
    """
    if pole_diameter <= 0:
        reject(f"pole_diameter {pole_diameter} must be positive", param="pole_diameter")

    pole_radius = pole_diameter / 2.0
    groove_radius = pole_radius + clearance

    if groove_radius + 1.0 >= AXLE_HEIGHT:
        reject(
            f"pole_diameter {pole_diameter} is too large for the fixed "
            f"{AXLE_HEIGHT}mm axis height: keep pole_diameter under "
            f"{2 * (AXLE_HEIGHT - 1.0 - clearance):.1f}",
            param="pole_diameter",
        )

    base_half_width = groove_radius + wall_thickness
    base_width = 2 * base_half_width

    block = Box(
        base_width,
        rest_length,
        AXLE_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    groove = Pos(0, 0, AXLE_HEIGHT) * Rot(X=90) * Cylinder(
        groove_radius,
        rest_length + 4.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    body = block - groove

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)

    def on_groove(e):
        # The tangent seam and rim of the cradle bore: the pole's mating
        # surface, never chamfered, the same rule as any mating mouth.
        eb = e.bounding_box()
        on_rim = (
            abs(abs(eb.min.X) - groove_radius) < 1e-3
            and abs(abs(eb.max.X) - groove_radius) < 1e-3
        )
        return e.geom_type == GeomType.CIRCLE or on_rim

    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 1e-6)
    keep = keep.filter_by(lambda e: e not in concave and not on_groove(e))
    return polish(body, keep, 1.0)
