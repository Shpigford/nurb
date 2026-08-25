from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A one-screw wall clip for a horizontal cable bundle.

    bundle_diameter: measured width across the cable bundle
    """
    if bundle_diameter < 4.0:
        reject(
            "bundle_diameter must be at least 4.0 mm for this holder geometry",
            param="bundle_diameter",
        )

    length = 12.0
    wall_thickness = 3.0
    floor_thickness = 2.4
    lip_thickness = 2.4
    clearance = 0.4

    clear_width = bundle_diameter + clearance
    cable_center_height = floor_thickness + clear_width / 2
    lip_height = floor_thickness + clear_width + 0.6
    lip_inner_x = wall_thickness + clear_width
    overall_depth = lip_inner_x + lip_thickness

    screw_hole_width = 4.4
    screw_center_y = length / 2
    screw_center_z = lip_height + 6.0
    back_height = screw_center_z + 5.0

    back = Box(
        wall_thickness,
        length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    floor = Box(
        overall_depth,
        length,
        floor_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    lip = Pos(lip_inner_x, 0, 0) * Box(
        lip_thickness,
        length,
        lip_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    holder = back + floor + lip
    screw_bore = (
        Pos(wall_thickness / 2, screw_center_y, screw_center_z)
        * Rot(0, 90, 0)
        * Cylinder(screw_hole_width / 2, wall_thickness)
    )
    holder = holder - screw_bore

    if draft:
        return holder

    # Keep the wall face, bed face, bore, and cable channel dimensionally exact.
    # The single exposed outer rim receives the standard finishing chamfer.
    outer_rim = holder.edges().filter_by(
        lambda edge: edge.bounding_box().min.X > overall_depth - 0.01
        and edge.bounding_box().min.Z > lip_height - 0.01
    )
    return polish(holder, outer_rim, 1.0)
