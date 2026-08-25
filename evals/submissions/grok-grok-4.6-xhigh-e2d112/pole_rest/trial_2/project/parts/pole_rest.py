from nurb import *

# Pole axis is a bench interface: 18 mm above the bed, centered on the rest in X.
AXIS_HEIGHT = 18.0
# Soft finish: sit close enough to cradle, far enough not to smear.
CRADLE_GAP = 0.2
WALL = 3.0
LENGTH = 24.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while the finish dries.

    pole_diameter: width of the pole this rest holds
    """
    if pole_diameter < 8.0:
        reject(
            f"pole_diameter {pole_diameter} is too small to cradle; raise it to 8 or more",
            param="pole_diameter",
        )

    inner_r = pole_diameter / 2.0 + CRADLE_GAP
    floor = AXIS_HEIGHT - inner_r
    if floor < WALL:
        reject(
            f"pole_diameter {pole_diameter} needs a cradle deeper than the 18 mm axis "
            f"height allows with a {WALL:g} mm floor; use a smaller pole",
            param="pole_diameter",
        )

    width = 2.0 * (inner_r + WALL)

    with BuildPart() as built:
        with BuildSketch(Plane.XZ):
            Rectangle(width, AXIS_HEIGHT, align=(Align.CENTER, Align.MIN))
            with Locations((0, AXIS_HEIGHT)):
                Circle(inner_r, mode=Mode.SUBTRACT)
        extrude(amount=LENGTH / 2.0, both=True)

    body = built.part
    if draft:
        return body

    # Chamfer only the long edges (along the pole). Chamfering the end-face
    # rims as well leaves sliver triangles at the four lip corners.
    bed = body.bounding_box().min.Z
    keep = (
        body.edges()
        .filter_by(Axis.Y)
        .filter_by(lambda e: e.bounding_box().min.Z > bed + 1e-4)
    )
    return polish(body, keep, 1.0)
