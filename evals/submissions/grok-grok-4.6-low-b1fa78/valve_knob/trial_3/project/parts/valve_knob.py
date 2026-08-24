from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    height=14.0,
    grip_across=32.0,
    draft=False,
):
    """Replacement knob for a broken D-shaft valve handle.

    shaft_diameter: round-side diameter of the valve stem
    shaft_across_flat: stem thickness from the flat to the opposite round
    height: how tall the knob is (prints bore-up)
    grip_across: distance across the hex flats, the narrowest grip
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter",
            param="shaft_across_flat",
        )
    if height < 12.0:
        reject("height must be at least 12 to cover the stem", param="height")
    if grip_across < 28.0:
        reject("grip_across must be at least 28 so wet hands can turn it", param="grip_across")

    clearance = 0.5
    bore_d = shaft_diameter + clearance
    bore_af = shaft_across_flat + clearance
    bore_r = bore_d / 2.0
    # Flat faces +X: leftmost of the circle is -bore_r, so the flat sits at -r + across_flat.
    flat_x = -bore_r + bore_af
    vertex_r = grip_across / (3.0**0.5)

    body = extrude(RegularPolygon(vertex_r, 6), height)
    void = Cylinder(bore_r, height + 4.0)
    void = void - Pos(flat_x + 40.0, 0, 0) * Box(80.0, bore_d * 3.0, height + 6.0)
    body = body - Pos(0, 0, height / 2.0) * void

    if draft:
        return body

    bed = body.bounding_box().min.Z

    def outer_keep(e):
        c = e.center()
        if c.Z < bed + 0.05:
            return False
        # Leave the six vertical corners sharp so vertex reach stays past the 12% grip rule.
        bb = e.bounding_box()
        if bb.max.Z - bb.min.Z > height * 0.5:
            return False
        return (c.X * c.X + c.Y * c.Y) ** 0.5 > bore_r + 1.0

    keep = body.edges().filter_by(outer_keep)
    return polish(body, keep, 1.0)
