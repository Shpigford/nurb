from nurb import *


def _d_profile(diameter, across_flat):
    """Circle of `diameter` with a flat facing +X, `across_flat` from round to flat."""
    radius = diameter / 2.0
    flat_x = -radius + across_flat
    with BuildSketch() as sketch:
        Circle(radius)
        with Locations((flat_x, 0)):
            Rectangle(
                diameter + 4.0,
                diameter + 4.0,
                align=(Align.MIN, Align.CENTER),
                mode=Mode.SUBTRACT,
            )
    return sketch.sketch


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """Replacement valve knob, printed bore-up, flipped onto the D-stem in use.

    shaft_diameter: round-side width of the valve stem
    shaft_across_flat: distance from the stem's flat to the opposite round
    """
    if shaft_diameter < 4.0:
        reject(
            "shaft_diameter 4mm is the smallest stem this knob can grip; raise it",
            param="shaft_diameter",
        )
    if shaft_across_flat <= 0:
        reject(
            "shaft_across_flat must be positive",
            param="shaft_across_flat",
        )
    if shaft_across_flat >= shaft_diameter - 0.4:
        reject(
            "shaft_across_flat must stay below shaft_diameter so the D-flat can transmit torque",
            param="shaft_across_flat",
        )

    # Between the 0.3mm must-fit stem and the 1.0mm must-jam stem.
    slack = 0.7
    bore_diameter = shaft_diameter + slack
    bore_across_flat = shaft_across_flat + slack

    height = 14.0
    floor = 3.0
    hub_radius = 15.5
    lobe_radius = 6.0
    lobe_offset = 13.0

    with BuildPart() as built:
        with BuildSketch():
            Circle(hub_radius)
            with PolarLocations(lobe_offset, 4):
                Circle(lobe_radius)
        extrude(amount=height)
        with BuildSketch(Plane.XY.offset(floor)):
            add(_d_profile(bore_diameter, bore_across_flat))
        extrude(amount=height - floor + 1.0, mode=Mode.SUBTRACT)

    body = built.part
    if draft:
        return body
    bed = body.bounding_box().min.Z
    concave = list(concave_edges(body))

    def _skip(edge):
        if any(edge.wrapped.IsSame(other.wrapped) for other in concave):
            return True
        center = edge.center()
        return (center.X ** 2 + center.Y ** 2) ** 0.5 < hub_radius - 2.0

    keep = [
        e
        for e in body.edges()
        if e.bounding_box().min.Z > bed + 0.05 and not _skip(e)
    ]
    return polish(body, keep, 1.0)
