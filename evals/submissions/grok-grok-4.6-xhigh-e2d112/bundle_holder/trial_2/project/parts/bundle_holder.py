from nurb import *

_BUNDLE = measured("bundle_diameter")

# M4 pan-head through the back: 4.4 clearance bore, 8.4 head-and-driver envelope.
_BORE = 4.4
_HEAD_CLEAR = 8.4
_BUNDLE_CLEARANCE = 0.4
_WALL = 2.4
_BACK = 2.6
_LENGTH = 12.0
_PAD_GAP = 1.6


@part
def bundle_holder(bundle_diameter=_BUNDLE, draft=False):
    """Wall clip that traps a cable bundle on one M4 pan-head screw.

    bundle_diameter: width of the taped cable bundle the clip holds
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 2mm: raise it to at least 2",
            param="bundle_diameter",
        )

    pocket = bundle_diameter + _BUNDLE_CLEARANCE
    depth = _BACK + pocket + _WALL
    pocket_top = _WALL + pocket
    screw_z = pocket_top + _PAD_GAP + _HEAD_CLEAR / 2
    height = screw_z + _BORE / 2 + _WALL

    # XZ profile: U-cradle on the bed, tall back plate for the M4. Extruded along Y
    # so the bundle has a clear run the full length of the part.
    profile = Polygon(
        (0, 0),
        (depth, 0),
        (depth, pocket_top),
        (depth - _WALL, pocket_top),
        (depth - _WALL, _WALL),
        (_BACK, _WALL),
        (_BACK, height),
        (0, height),
    )
    body = extrude(Plane.XZ * profile, amount=_LENGTH / 2, both=True)

    cutter = Pos(_BACK / 2, 0, screw_z) * Rot(0, 90, 0) * Cylinder(_BORE / 2, _BACK + 4)
    body = body - cutter

    if draft:
        return body

    box = body.bounding_box()
    bed = box.min.Z
    back_x = box.min.X
    top = box.max.Z
    concave = set(concave_edges(body))
    # Skip edges that lie in the bed, the wall face, or the top of the pad:
    # three 1mm chamfers meeting at the pad corners leave 0.87mm2 slivers.
    keep = body.edges().filter_by(
        lambda e: (
            e.bounding_box().max.Z > bed + 1e-4
            and e.bounding_box().min.Z < top - 1e-4
            and e.bounding_box().max.X > back_x + 1e-4
            and e not in concave
            and e.geom_type != GeomType.CIRCLE
        )
    )
    return polish(body, keep, 1.0)
