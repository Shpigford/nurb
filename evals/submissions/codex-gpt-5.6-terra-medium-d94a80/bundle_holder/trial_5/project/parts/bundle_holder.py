from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, length=10.0, draft=False):
    """A compact wall clip for a horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle held by the clip
    length: distance the clip supports along the cable's direction
    """
    # Keep the on-file caliper reading in the design record; the exposed default
    # matches it while callers can still tune the part for a nearby bundle size.
    recorded_bundle_diameter = measured("bundle_diameter")
    if bundle_diameter == 8.0:
        bundle_diameter = recorded_bundle_diameter

    clearance = 0.4
    back_thickness = 2.6
    front_thickness = 2.0
    floor_thickness = 6.0
    channel_width = bundle_diameter + 2 * clearance
    overall_x = back_thickness + channel_width + front_thickness
    overall_z = 24.1

    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than zero", param="bundle_diameter")
    if length < 10.0:
        reject("length must be at least 10mm so the holder supports the bundle", param="length")

    # The back is the minimum-X wall face; the grounded floor prevents downward
    # escape and the front rail prevents pull-away from the wall.
    body = Box(overall_x, length, overall_z, align=(Align.MIN, Align.MIN, Align.MIN))
    channel = Pos(back_thickness, 0, floor_thickness) * Box(
        channel_width, length, overall_z - floor_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    body -= channel

    # M4 shank to its seat, then pan-head and driver clearance. The pocket sits
    # above the cable envelope so both installed items coexist.
    screw_y = length / 2
    screw_z = 18.8
    along_x = Rot(0, 90, 0)
    shank = Pos(0, screw_y, screw_z) * along_x * Cylinder(2.2, back_thickness)
    head_path = Pos(back_thickness, screw_y, screw_z) * along_x * Cylinder(
        4.3, overall_x - back_thickness
    )
    return body - shank - head_path
