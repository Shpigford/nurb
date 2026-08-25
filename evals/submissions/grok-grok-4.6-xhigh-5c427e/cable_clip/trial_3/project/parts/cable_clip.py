from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle against a surface.

    bundle_diameter: how wide the taped cable bundle is
    """
    wall = 2.4
    base_th = 3.0
    length = 12.0
    tab_len = 10.0
    hole_dia = 4.2
    channel_clearance = 0.4

    if bundle_diameter <= 0:
        reject(
            "bundle_diameter must be positive so the channel can hold a cable",
            param="bundle_diameter",
        )

    channel_w = bundle_diameter + channel_clearance
    channel_d = bundle_diameter
    height = base_th + channel_d
    clip_w = wall + channel_w + wall
    overall_x = clip_w + tab_len

    # Profile in XZ, cable along Y: U-channel plus a flush mounting tab.
    # Square channel: the floor is one face the full inner width, no inside chamfers.
    profile = Polyline(
        (0, 0, 0),
        (overall_x, 0, 0),
        (overall_x, 0, base_th),
        (clip_w, 0, base_th),
        (clip_w, 0, height),
        (clip_w - wall, 0, height),
        (clip_w - wall, 0, base_th),
        (wall, 0, base_th),
        (wall, 0, height),
        (0, 0, height),
        close=True,
    )
    body = extrude(make_face(profile), amount=length)
    bb = body.bounding_box()
    body = body.translate((0, -bb.min.Y, -bb.min.Z))

    hole = Pos(clip_w + tab_len / 2, length / 2, 0) * Cylinder(
        hole_dia / 2, base_th + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    body = body - hole
    return body
