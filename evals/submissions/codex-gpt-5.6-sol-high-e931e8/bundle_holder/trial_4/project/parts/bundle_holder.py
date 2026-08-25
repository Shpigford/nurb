from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall-mounted tunnel for a horizontal cable bundle.

    bundle_diameter: measured width across the cable bundle
    """
    if bundle_diameter < 4.0:
        reject(
            "bundle_diameter under 4.0 mm leaves too little room for the M4 mount geometry",
            param="bundle_diameter",
        )

    length = 12.0
    retention_length = 4.8
    clearance = 0.4
    shell = 2.4
    back_thickness = 3.0
    screw_hole_width = 4.4
    screw_head_width = 8.4

    passage_width = bundle_diameter + clearance
    passage_bottom = shell
    passage_top = passage_bottom + passage_width
    roof_peak = passage_top + passage_width / 2.0
    passage_start = shell
    holder_width = passage_width + 2.0 * shell
    holder_top = roof_peak + shell

    # Keep the pan head and driver above the cable tunnel. Four millimetres of
    # plastic remains around the loaded side of the M4 bore.
    screw_z = holder_top + screw_head_width / 2.0 + clearance
    back_height = screw_z + screw_hole_width / 2.0 + 4.0

    back = Box(
        back_thickness,
        length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    holder_blank = Box(
        holder_width,
        retention_length,
        holder_top,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    holder_blank = Pos(0.0, (length - retention_length) / 2.0, 0.0) * holder_blank
    body = back + holder_blank

    # A square cable seat gives the bundle its full 0.4 mm diametral clearance.
    # The pointed 45-degree roof prints without support while leaving a clear
    # straight passage along Y.
    passage_profile = Plane.XZ * Polygon(
        (passage_start, passage_bottom),
        (passage_start + passage_width, passage_bottom),
        (passage_start + passage_width, passage_top),
        (passage_start + passage_width / 2.0, roof_peak),
        (passage_start, passage_top),
    )
    passage = extrude(passage_profile, amount=-length)
    body = body - passage

    # The 3 mm back plate is the screw's bearing thickness. The head and driver
    # remain entirely outside the part from this seat toward +X.
    screw_bore = Cylinder(
        screw_hole_width / 2.0,
        back_thickness + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).rotate(Axis.Y, 90.0)
    screw_bore = Pos(-1.0, length / 2.0, screw_z) * screw_bore
    body = body - screw_bore

    return body
