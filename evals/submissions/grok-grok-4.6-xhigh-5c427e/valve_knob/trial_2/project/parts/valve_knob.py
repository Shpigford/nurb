from nurb import *


# Clearance on each stem dimension: larger than the 0.3-grown probe, smaller
# than the 1.0-grown probe, so the stem seats without rattling and the flat
# still transmits torque.
_BORE_SLACK = 0.6
_FLOOR = 3.0


def _d_profile(diameter, across_flat):
    """D-face on XY, circle at the origin, flat facing +X."""
    radius = diameter / 2.0
    flat_x = across_flat - radius
    circle = Circle(radius)
    clip = Location((flat_x, 0, 0)) * Rectangle(
        max(diameter * 3.0, 8.0),
        max(diameter * 3.0, 8.0),
        align=(Align.MAX, Align.CENTER),
    )
    return circle.intersect(clip)


@part
def valve_knob(
    shaft_diameter=float(measured("shaft_diameter")),
    shaft_across_flat=float(measured("shaft_across_flat")),
    knob_width=32.0,
    height=16.0,
    draft=False,
):
    """Replacement knob for a D-shaft valve, printed bore-up.

    shaft_diameter: round-side width of the valve stem
    shaft_across_flat: stem thickness from the flat to the opposite round side
    knob_width: distance across the flats of the grip
    height: how tall the knob is, with the bore opening at the top
    """
    if shaft_diameter <= 0:
        reject("shaft_diameter must be a real stem width", param="shaft_diameter")
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} must be less than "
            f"shaft_diameter {shaft_diameter} for a D-stem",
            param="shaft_across_flat",
        )
    if shaft_across_flat <= 0:
        reject("shaft_across_flat must be a real flat depth", param="shaft_across_flat")
    if knob_width < 28.0:
        reject(
            "knob_width must be at least 28 mm so wet hands can turn it",
            param="knob_width",
        )
    if height < 12.0:
        reject("height must be at least 12 mm so the stem can seat", param="height")

    floor = min(_FLOOR, height - 10.5)
    if floor < 2.4:
        reject(
            f"height {height} leaves no floor under a 10 mm stem insertion; raise it",
            param="height",
        )
    bore_depth = height - floor
    bore_diameter = shaft_diameter + _BORE_SLACK
    bore_across_flat = shaft_across_flat + _BORE_SLACK

    grip = extrude(RegularPolygon(knob_width / 2.0, 6, major_radius=False), height)
    cutter = extrude(_d_profile(bore_diameter, bore_across_flat), bore_depth + 1.0)
    cutter = cutter.move(Location((0, 0, floor)))
    body = grip - cutter

    if draft:
        return body
    bed = body.bounding_box().min.Z
    top = body.faces().sort_by(Axis.Z)[-1]
    keep = top.outer_wire().edges()
    keep = keep.filter_by(lambda e: e.bounding_box().min.Z > bed)
    return polish(body, keep, 1.0)
