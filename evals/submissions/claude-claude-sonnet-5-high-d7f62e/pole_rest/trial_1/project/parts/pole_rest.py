from nurb import *

POLE_AXIS_HEIGHT = 18.0  # fixed interface: the pole's axis sits this high above the bed


@part
def pole_rest(
    pole_diameter=20.0,
    rest_length=24.0,
    wall_thickness=3.0,
    base_height=5.0,
    base_overhang=2.0,
    clearance=0.25,
    draft=False,
):
    """
    pole_diameter: diameter of the pole this cradle holds
    rest_length: how long the rest is along the pole
    wall_thickness: how much material backs the cradle around the pole
    base_height: thickness of the flat base plate on the bed
    base_overhang: how far the base ledge extends past the cradle riser on each side
    clearance: gap left between the cradle surface and the pole
    """
    if not (0.1 <= clearance <= 0.4):
        reject(
            f"clearance {clearance} must stay between 0.1 (fit) and 0.4 (a supporting cradle)",
            param="clearance",
        )

    pole_radius = pole_diameter / 2
    contact_radius = pole_radius + clearance
    riser_half_width = contact_radius + wall_thickness
    riser_width = 2 * riser_half_width
    base_width = riser_width + 2 * base_overhang
    riser_height = POLE_AXIS_HEIGHT - base_height

    if riser_height <= contact_radius:
        reject(
            f"base_height {base_height} leaves only {riser_height:.1f}mm of riser, "
            f"under the {contact_radius:.1f}mm the cradle needs to clear its own base",
            param="base_height",
        )

    base = Pos(0, 0, base_height / 2) * Box(base_width, rest_length, base_height)
    riser = Pos(0, 0, base_height + riser_height / 2) * Box(riser_width, rest_length, riser_height)
    groove = Pos(0, 0, POLE_AXIS_HEIGHT) * Rot(X=90) * Cylinder(contact_radius, rest_length + 4)

    body = (base + riser) - groove

    if draft:
        return body

    bed = body.bounding_box().min.Z
    cradle_edges = body.faces().filter_by(GeomType.CYLINDER).edges()
    concave = concave_edges(body)

    def is_mouth_shoulder_edge(e):
        # the short flat rim flanking the cradle mouth: leave it alone so no
        # three chamfers converge on the corner where it meets the cradle
        bb = e.bounding_box()
        return abs(bb.min.Z - POLE_AXIS_HEIGHT) < 1e-6 and abs(bb.max.Z - POLE_AXIS_HEIGHT) < 1e-6

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed
        and e not in cradle_edges
        and e not in concave
        and not is_mouth_shoulder_edge(e)
    )
    return polish(body, keep, 1.0)
