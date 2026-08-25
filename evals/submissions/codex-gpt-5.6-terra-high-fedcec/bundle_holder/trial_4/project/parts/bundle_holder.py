from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """A two-band, wall-mounted cable-bundle holder.

    bundle_diameter: measured width of the cable bundle that the holder cradles
    """
    measured_bundle = measured("bundle_diameter")
    if abs(bundle_diameter - measured_bundle) > 3.0:
        reject(
            "bundle_diameter is outside the supported range around the recorded 8mm bundle",
            param="bundle_diameter",
        )

    # The 0.4 mm clearance is applied on each constrained side of the bundle.
    fit_diameter = bundle_diameter + 0.8
    cable_radius = fit_diameter / 2.0
    back_thickness = 2.5
    length = 16.0
    band_length = 3.3
    cable_x = back_thickness + cable_radius + 0.5
    cable_z = cable_radius + 9.0
    shelf_top = cable_z - cable_radius - 0.4
    lip_front = cable_x + cable_radius + 0.5
    front_thickness = 2.0
    height = cable_z + cable_radius + 0.6

    # A tall, thin plate gives the wall a generous, completely flat mounting face.
    back = Box(back_thickness, length, height, align=(Align.MIN, Align.MIN, Align.MIN))

    # The two end bands leave the central screw-driver path open.  Together they
    # retain the cable over more than a third of its run while using little plastic.
    lower_a = Pos(back_thickness, 0, 0) * Box(
        lip_front - back_thickness + front_thickness,
        band_length,
        shelf_top,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    lower_b = Pos(back_thickness, length - band_length, 0) * Box(
        lip_front - back_thickness + front_thickness,
        band_length,
        shelf_top,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    lip_a = Pos(lip_front, 0, shelf_top) * Box(
        front_thickness,
        band_length,
        height - shelf_top,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    lip_b = Pos(lip_front, length - band_length, shelf_top) * Box(
        front_thickness,
        band_length,
        height - shelf_top,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    body = back + lower_a + lower_b + lip_a + lip_b

    # M4 clearance bore and a pan-head/driver escape that opens toward +X.
    # The head is deliberately below the cradle so an installed screw and bundle
    # have separate clearance envelopes.
    screw_y = length / 2.0
    screw_z = 4.3
    bore = Pos(-0.1, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(2.2, back_thickness + 0.2)
    head_escape = Pos(back_thickness, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(4.2, lip_front + front_thickness)
    body = body - bore - head_escape

    # The square cradle junctions are deliberately left sharp: polishing their
    # concave edges creates narrow, non-printable runout strips.
    return body
