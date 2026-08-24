from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle in an open-top channel.

    bundle_diameter: how wide the taped cable bundle is
    """
    if bundle_diameter < 1.0:
        reject(
            f"bundle_diameter {bundle_diameter} is too small to form a channel",
            param="bundle_diameter",
        )

    clearance = 0.4
    wall = 2.4
    base_thickness = 3.0
    length = 12.0
    tab_length = 10.0
    tab_thickness = 3.0
    hole_dia = 4.2

    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    body_width = wall + channel_width + wall
    height = base_thickness + channel_depth
    total_x = body_width + tab_length

    # XZ profile extruded along Y: the cable lies along Y, channel open at +Z.
    outline = Polygon(
        (0, 0),
        (total_x, 0),
        (total_x, tab_thickness),
        (body_width, tab_thickness),
        (body_width, height),
        (body_width - wall, height),
        (body_width - wall, base_thickness),
        (wall, base_thickness),
        (wall, height),
        (0, height),
    )
    # Plane.XZ points -Y, so a negative amount extrudes the cable along +Y.
    body = extrude(Plane.XZ * outline, amount=-length)

    hole = Cylinder(
        hole_dia / 2,
        tab_thickness + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body -= Pos(body_width + tab_length / 2, length / 2, -1) * hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    x0 = wall
    x1 = wall + channel_width
    z_floor = base_thickness
    concave = set(concave_edges(body))

    def keep_edge(edge):
        if edge in concave:
            return False
        bb = edge.bounding_box()
        if bb.min.Z <= bed + 1e-6:
            return False
        # Only the long outer rims. End and vertical chamfers nibble the
        # channel mouth and triple-chamfer into slivers at the tab wall.
        if bb.max.Z - bb.min.Z > 0.5:
            return False
        if bb.max.Y - bb.min.Y < 5.0:
            return False
        inside_channel = (
            bb.min.X >= x0 - 1e-4
            and bb.max.X <= x1 + 1e-4
            and bb.min.Z >= z_floor - 1e-4
        )
        if inside_channel:
            return False
        if edge.geom_type == GeomType.CIRCLE:
            return False
        return True

    return polish(body, body.edges().filter_by(keep_edge), 1.0)
