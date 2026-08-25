from nurb import *

# Screw-down clip for a taped cable bundle.
# Channel inner width is bundle_diameter + 0.4 so the bundle drops in;
# depth matches the measured bundle so it sits to the floor.


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle and screws to a surface.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    clearance = 0.4
    wall = 2.4
    base = 3.0
    length = 12.0
    tab_length = 10.0
    tab_thickness = 3.0
    hole_diameter = 4.2

    if bundle_diameter < 2.0:
        reject(
            "bundle_diameter is too small for a printable channel: raise it to at least 2.0",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    height = base + channel_depth
    channel_outer = channel_width + 2 * wall
    total_x = channel_outer + tab_length

    # Profile in XZ, extruded along Y: open-top U-channel with a flush
    # mounting tab off one wall. Square channel corners stay in the sketch.
    profile = Plane.XZ * Polygon(
        (0, 0),
        (total_x, 0),
        (total_x, tab_thickness),
        (channel_outer, tab_thickness),
        (channel_outer, height),
        (channel_outer - wall, height),
        (channel_outer - wall, base),
        (wall, base),
        (wall, height),
        (0, height),
    )
    body = extrude(profile, amount=length)

    bb = body.bounding_box()
    hole_x = bb.max.X - tab_length / 2.0
    hole_y = (bb.min.Y + bb.max.Y) / 2.0
    hole = Cylinder(
        hole_diameter / 2.0,
        tab_thickness + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - hole.move(Location((hole_x, hole_y, -1.0)))

    if draft:
        return body

    # Channel is fit-critical: leave the floor one flat face the full width
    # and do not chamfer anything inside it. Skip bed, concave, hole rims,
    # and vertical step edges at the tab (those make 0.9mm2 corner triangles).
    bed = body.bounding_box().min.Z
    x_left = bb.min.X + wall
    x_right = x_left + channel_width
    z_floor = bed + base
    z_top = bed + height
    concave = concave_edges(body)

    def keep_edge(edge):
        e_bb = edge.bounding_box()
        if e_bb.min.Z <= bed + 1e-4:
            return False
        if edge in concave:
            return False
        if edge.geom_type == GeomType.CIRCLE:
            return False
        c = edge.center()
        if (x_left - 0.05) <= c.X <= (x_right + 0.05) and (
            z_floor - 0.05
        ) <= c.Z <= (z_top + 0.05):
            return False
        dx = e_bb.max.X - e_bb.min.X
        dy = e_bb.max.Y - e_bb.min.Y
        dz = e_bb.max.Z - e_bb.min.Z
        # Only the long outer rims along Y. End-face chamfers nick the
        # channel mouth; verticals at the tab step make sliver triangles.
        if not (dy > dx and dy > dz):
            return False
        return True

    keep = body.edges().filter_by(keep_edge)
    return polish(body, keep, 1.0)
