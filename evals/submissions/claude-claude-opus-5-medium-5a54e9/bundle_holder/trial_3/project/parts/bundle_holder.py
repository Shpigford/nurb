from nurb import *

SCREW_HOLE = 4.4          # M4 clearance, medium column
SCREW_HEAD_SWING = 8.4    # pan head plus driver socket, must stay clear ahead of the seat


def _block(x0, x1, y0, y1, z0, z1):
    """An axis-aligned block given by its two corners."""
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    bundle_clearance=0.4,
    holder_length=12.0,
    back_thickness=3.0,
    floor_thickness=2.4,
    lip_thickness=2.4,
    lip_extra_height=0.8,
    screw_wall=2.4,
    chamfer_size=1.2,
    draft=False,
):
    """A wall saddle that carries a cable bundle running horizontally along the wall.

    bundle_diameter: how thick the cable bundle is across
    bundle_clearance: extra room around the bundle so it drops in instead of being forced
    holder_length: how much of the bundle the saddle wraps, measured along the run
    back_thickness: how thick the plate against the wall is
    floor_thickness: how thick the shelf the bundle rests on is
    lip_thickness: how thick the front lip that stops the bundle falling out is
    lip_extra_height: how far the lip reaches past where the bundle can push it
    screw_wall: how much material rings the screw hole
    chamfer_size: how big the chamfer on the exposed edges is
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} leaves a channel no printer can open: "
            "raise it above 2.0",
            param="bundle_diameter",
        )

    channel = bundle_diameter + bundle_clearance      # the pocket the bundle drops into
    radius = channel / 2
    bundle_radius = bundle_diameter / 2

    # The bundle rides centred in the channel, resting off the wall plate.
    centre_x = back_thickness + radius
    centre_z = floor_thickness + radius

    lip_inner = back_thickness + channel
    front = lip_inner + lip_thickness

    # Pushed 1mm away from the wall the bundle meets the lip over a chord this tall;
    # the lip carries that whole chord plus a little, so it grips rather than grazes.
    reach = max(0.0, bundle_radius**2 - max(0.0, radius - 1.0) ** 2) ** 0.5
    lip_height = centre_z + reach + lip_extra_height

    # The screw sits above the bundle so the head and its driver swing in clear air,
    # and so a driven screw never crosses the space the bundle occupies.
    screw_z = centre_z + bundle_radius + SCREW_HEAD_SWING / 2
    # Tall enough to ring the bore, and tall enough that the seat face carries the whole
    # head footprint rather than running out into the top chamfer.
    height = max(
        screw_z + SCREW_HOLE / 2 + screw_wall,
        screw_z + SCREW_HEAD_SWING / 2 + chamfer_size,
    )

    half = holder_length / 2
    body = _block(0.0, back_thickness, -half, half, 0.0, height)
    body += _block(0.0, front, -half, half, 0.0, floor_thickness)
    body += _block(lip_inner, front, -half, half, 0.0, lip_height)

    bore = Pos(-1.0, 0.0, screw_z) * Rot(0, 90, 0) * Cylinder(
        SCREW_HOLE / 2, back_thickness + 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    body -= bore

    if draft:
        return body

    # Nothing lying in the wall face or the bed face, and no concave edge: a chamfer
    # there is a wedge added to the inside corner, not a corner taken off.
    inside = set(concave_edges(body))
    box = body.bounding_box()
    keep = body.edges().filter_by(
        lambda e: e not in inside
        and e.geom_type != GeomType.CIRCLE
        and e.bounding_box().max.X > box.min.X + 1e-6
        and e.bounding_box().max.Z > box.min.Z + 1e-6
    )
    return polish(body, keep, chamfer_size)
