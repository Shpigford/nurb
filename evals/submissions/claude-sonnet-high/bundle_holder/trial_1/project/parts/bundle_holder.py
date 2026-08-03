import math

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, wall_thickness=1.4, draft=False):
    """Wall-mounted clip that cradles a horizontal cable bundle, screwed to the
    wall with one M4 pan-head screw.

    bundle_diameter: the cable bundle's diameter, across the taped bundle
    wall_thickness: how thick the material is around the cable channel
    """
    channel_dia = bundle_diameter + 0.6
    channel_r = channel_dia / 2
    tube_outer_r = channel_r + wall_thickness
    length = channel_dia + 6.0

    screw_shank_dia = 4.5
    screw_head_dia = 8.6
    shank_r = screw_shank_dia / 2
    head_r = screw_head_dia / 2
    shank_depth = 2.8
    plate_thickness = shank_depth + 0.8

    screw_margin = 1.5
    z_s = head_r + screw_margin
    separation = channel_r + head_r + screw_margin
    z_c = z_s + separation

    plate_top = z_s + head_r + 0.8 + 1.1
    block_h = z_c + tube_outer_r + 0.8

    x_c = tube_outer_r + 0.6
    y_s = length / 2

    def y_cylinder(radius, y0, y1, x_pos, z_pos):
        cyl = Cylinder(radius=radius, height=y1 - y0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        cyl = cyl.rotate(Axis.X, -90)
        return cyl.translate((x_pos, y0, z_pos))

    def x_cylinder(radius, x0, x1, y_pos, z_pos):
        cyl = Cylinder(radius=radius, height=x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        cyl = cyl.rotate(Axis.Y, 90)
        return cyl.translate((x0, y_pos, z_pos))

    plate = Box(plate_thickness, length, plate_top, align=(Align.MIN, Align.MIN, Align.MIN))
    tube = y_cylinder(tube_outer_r, 0, length, x_c, z_c)
    body = plate + tube

    channel = y_cylinder(channel_r, 0, length, x_c, z_c)
    shank_hole = x_cylinder(shank_r, -1.0, shank_depth, y_s, z_s)
    head_hole = x_cylinder(head_r, shank_depth, plate_thickness + 1.0, y_s, z_s)
    body = body - channel - shank_hole - head_hole

    if draft:
        return body

    all_edges = body.edges()
    back_x = body.bounding_box().min.X
    bed_z = body.bounding_box().min.Z

    back = all_edges.filter_by(
        lambda e: math.isclose(e.bounding_box().min.X, back_x, abs_tol=1e-4)
        and math.isclose(e.bounding_box().max.X, back_x, abs_tol=1e-4)
    )
    bottom = all_edges.filter_by(
        lambda e: math.isclose(e.bounding_box().min.Z, bed_z, abs_tol=1e-4)
        and math.isclose(e.bounding_box().max.Z, bed_z, abs_tol=1e-4)
    )
    mating = all_edges.filter_by(
        lambda e: e.geom_type == "CIRCLE"
        and any(math.isclose(e.radius, r, abs_tol=1e-3) for r in (channel_r, head_r, shank_r))
    )
    concave = concave_edges(body)

    keep = all_edges - back - bottom - mating - concave
    return polish(body, keep, 1.0)
