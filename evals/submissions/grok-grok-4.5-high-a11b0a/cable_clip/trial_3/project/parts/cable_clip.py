from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down open-top clip for a cable bundle.

    bundle_diameter: measured diameter of the cable bundle the channel holds
    """
    wall = 2.4
    base_thickness = 3.0
    length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2
    channel_clearance = 0.4

    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    channel_outer = channel_width + 2 * wall
    height = base_thickness + channel_depth

    # U-channel body: walls + floor, open top, cable along Y.
    block = Box(
        channel_outer, length, height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    block = Pos(tab_length, 0, 0) * block
    # Oversize the void in Y and +Z so the cut is clean and the top stays open.
    # Square corners: the floor stays one flat face the full channel width.
    void = Box(
        channel_width,
        length + 2,
        channel_depth + 1,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    void = Pos(tab_length + wall, -1, base_thickness) * void
    channel = block - void

    # Mounting tab flush with the bed, extending along X from one wall.
    tab = Box(
        tab_length, length, base_thickness, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    hole = Cylinder(
        hole_diameter / 2,
        base_thickness + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    hole = Pos(tab_length / 2, length / 2, -1) * hole
    tab = tab - hole

    # No polish: 2.4mm walls cannot take 1mm chamfers on both top edges, and the
    # channel interior must stay square (no fillets or chamfers inside).
    return channel + tab
