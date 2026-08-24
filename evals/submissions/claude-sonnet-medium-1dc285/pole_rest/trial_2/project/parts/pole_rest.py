from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), length=24.0, wall=3.0, clearance=0.2, draft=False):
    """
    pole_diameter: the diameter of the pole the rest cradles
    length: how long the rest is along the pole's axis
    wall: solid material behind the cradle's contact surface
    clearance: gap left between the cradle and the pole's surface
    """
    axis_z = 18.0
    r_pole = pole_diameter / 2.0
    r_groove = r_pole + clearance
    half_width = r_groove + wall
    width = 2 * half_width
    height = axis_z

    block = Box(width, length, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    groove = Cylinder(r_groove, length + 4.0, rotation=(90, 0, 0))
    groove = groove.translate((0, 0, axis_z))

    body = block - groove

    if draft:
        return body

    bed = body.bounding_box().min.Z
    y_end = length / 2.0
    concave_ids = {id(e) for e in concave_edges(body)}

    def eligible(e):
        bb = e.bounding_box()
        if bb.min.Z <= bed:
            return False
        if id(e) in concave_ids:
            return False
        on_end = abs(bb.max.Y - bb.min.Y) < 0.01 and (
            bb.min.Y <= -y_end + 0.01 or bb.max.Y >= y_end - 0.01
        )
        if on_end:
            return False
        return True

    keep = body.edges().filter_by(eligible)
    return polish(body, keep, 1.0)
