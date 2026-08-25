from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall-mounted J holder for a horizontal cable bundle.

    bundle_diameter: measured width across the cable bundle
    draft: skip the small finish chamfers for a faster preview
    """
    if bundle_diameter < 4.0:
        reject(
            "bundle_diameter below 4 mm leaves the fixed M4 mounting boss oversized; "
            "raise it to at least 4 mm",
            param="bundle_diameter",
        )

    length = 12.0
    fit_clearance = 0.4
    clear_radius = (bundle_diameter + fit_clearance) / 2.0

    back_thickness = 3.0
    floor_thickness = 2.6
    lip_thickness = 2.4
    side_clearance = 0.1

    bundle_x = back_thickness + clear_radius + side_clearance
    bundle_z = floor_thickness + clear_radius
    lip_inner_x = bundle_x + clear_radius + side_clearance
    projection = lip_inner_x + lip_thickness
    lip_height = bundle_z + 1.8

    screw_hole_width = 4.4
    screw_head_width = 8.4
    screw_z = bundle_z + clear_radius + screw_head_width / 2.0 + 0.8
    back_height = screw_z + screw_head_width / 2.0 + 1.8

    back = Box(
        back_thickness,
        length,
        back_height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    floor = Box(
        projection,
        length,
        floor_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    lip = Pos(lip_inner_x, 0, 0) * Box(
        lip_thickness,
        length,
        lip_height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )

    holder = back + floor + lip

    if not draft:
        finish_edges = holder.edges().filter_by(
            lambda edge: (
                edge.bounding_box().min.X > projection - 0.01
                and edge.bounding_box().max.Z > lip_height - 0.01
            )
        )
        holder = polish(holder, finish_edges, 1.0)

    screw_bore = Pos(-0.2, 0, screw_z) * Rot(0, 90, 0) * Cylinder(
        screw_hole_width / 2.0,
        back_thickness + 0.4,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return holder - screw_bore
