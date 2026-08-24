from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A support-free, wall-mounted cable-bundle clip.

    bundle_diameter: measured diameter of the cable bundle being retained
    """
    # The channel is deliberately 0.4 mm larger than the measured bundle.
    bundle_clear_diameter = bundle_diameter + 0.4
    bundle_radius = bundle_clear_diameter / 2.0
    length = 12.0
    back_thickness = 4.0
    bundle_center_x = back_thickness + bundle_radius + 0.3
    shelf_height = 1.0
    bundle_center_z = bundle_radius + shelf_height
    screw_z = bundle_center_z + bundle_radius + 5.6

    # The tall back plate gives the screw a 4 mm shank land and a 12 x 21 mm
    # flat contact face. The shelf catches downward motion; the upright nose
    # catches motion away from the wall while leaving an open Y-direction run.
    back = Box(back_thickness, length, screw_z + 6.0,
               align=(Align.MIN, Align.CENTER, Align.MIN))
    shelf = Box(11.0, length, shelf_height,
                align=(Align.MIN, Align.CENTER, Align.MIN)).translate((back_thickness, 0, 0))
    nose_start = bundle_center_x + bundle_radius + 0.3
    nose = Box(2.2, length, bundle_center_z + bundle_radius + 0.8 - shelf_height,
               align=(Align.MIN, Align.CENTER, Align.MIN)).translate((nose_start, 0, shelf_height))
    body = back + shelf + nose

    # M4 clearance bore, then a front-side pan-head/driver relief. The relief
    # begins after the 4 mm shank land so the head seats against solid plate.
    screw_y = 0.0
    shank = Cylinder(2.2, back_thickness, rotation=(0, 90, 0)).translate((0, screw_y, screw_z))
    head_relief = Cylinder(4.3, 4.6, rotation=(0, 90, 0)).translate((back_thickness, screw_y, screw_z))
    return body - shank - head_relief
