from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, length=16.0, wall_thickness=1.3, draft=False):
    """A compact, through-threaded wall clip for one horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle being retained
    length: length of the holder along the cable run
    wall_thickness: thickness of the printed retaining sleeve
    """
    if bundle_diameter <= 0:
        reject("bundle diameter must be positive", "bundle_diameter")

    # The cradle gives 0.4 mm radial fitting clearance. Its floor stops downward
    # movement; the short upright lip stops outward movement while leaving the top
    # open for dropping a bundle in.
    clearance_radius = bundle_diameter / 2 + 0.4
    cable_x = 11.5
    cable_z = clearance_radius + 5.4

    # The continuous back plate supplies a generous flat wall contact and a fully
    # supported screw seat.  The retaining features occupy 6 mm of the 16 mm run.
    back_plate = Box(2.6, length, 25.2, align=(Align.MIN, Align.MIN, Align.MIN))
    floor = Box(cable_x + clearance_radius, 6.0, 5.4,
                align=(Align.MIN, Align.MIN, Align.MIN))
    lip = Box(wall_thickness, 6.0, cable_z + 1.2,
              align=(Align.MIN, Align.MIN, Align.MIN)) \
        .translate((cable_x + clearance_radius, 0, 0))
    body = back_plate + floor + lip

    # M4 clearance bore from the wall, followed by an 8.4 mm pan-head/driver path.
    # Its height keeps the screw and the retained bundle independent.
    screw_z = 21.0
    shank = Cylinder(2.2, 2.7, align=(Align.CENTER, Align.CENTER, Align.CENTER)) \
        .rotate(Axis.Y, 90).translate((1.35, length / 2, screw_z))
    head_path = Cylinder(4.2, 20.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)) \
        .rotate(Axis.Y, 90).translate((12.6, length / 2, screw_z))

    return body - shank - head_path
