from nurb import *

# Clearance between the taped bundle and the channel walls.
_CHANNEL_CLEARANCE = 0.4
_WALL = 2.4
_BASE = 3.0
_LENGTH = 12.0
_TAB = 10.0
_HOLE = 4.2


@part
def cable_clip(bundle_diameter=float(measured("bundle_diameter")), draft=False):
    """Screw-down clip that holds a cable bundle in an open channel.

    bundle_diameter: diameter of the cable bundle the channel is sized for
    """
    channel_w = bundle_diameter + _CHANNEL_CLEARANCE
    channel_d = bundle_diameter
    body_w = channel_w + 2 * _WALL
    total_x = _TAB + body_w

    # Origin at the tab's outer corner; +X into the channel, +Y along the cable, +Z up.
    # Layout in X: [tab][wall][channel][wall]
    # Square channel: no fillets or chamfers on the floor or inner walls.
    align = (Align.MIN, Align.MIN, Align.MIN)

    slab = Box(total_x, _LENGTH, _BASE, align=align)
    left = Pos(_TAB, 0, _BASE) * Box(_WALL, _LENGTH, channel_d, align=align)
    right = Pos(_TAB + _WALL + channel_w, 0, _BASE) * Box(
        _WALL, _LENGTH, channel_d, align=align
    )
    body = slab + left + right

    # Through-hole centered in the mounting tab.
    hole = Pos(_TAB / 2, _LENGTH / 2, -0.1) * Cylinder(
        _HOLE / 2,
        _BASE + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - hole

    # Keep the part seated on the bed.
    return Pos(0, 0, -body.bounding_box().min.Z) * body
