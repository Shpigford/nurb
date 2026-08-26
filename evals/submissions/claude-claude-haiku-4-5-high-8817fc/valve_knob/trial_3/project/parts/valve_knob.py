from nurb import *

@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    bore_depth=12.0,
    knob_diameter=34.0,
    knob_height=14.0,
):
    """
    Valve knob with D-shaped bore for D-shaft stem.

    shaft_diameter: D-shaft diameter in mm
    shaft_across_flat: D-shaft flat measurement in mm
    bore_depth: how deep to bore into the knob
    knob_diameter: main cylinder diameter for grip
    knob_height: knob height when sitting on bed
    """

    # Main body with tapered base
    body = Cylinder(knob_diameter / 2, knob_height)

    # Remove bottom edge taper to improve bed contact
    base_taper = Cylinder(knob_diameter / 2 - 1.5, 1.5)
    body = body - base_taper.translate((0, 0, -knob_height / 2 - 1.5))

    # D-shaped bore pocket for stem engagement
    bore_radius = 4.2
    flat_depth = 0.75
    pocket_depth = 10.0

    # Bore geometry: round opening with flat side cut
    bore_round = Cylinder(bore_radius, pocket_depth + 1)

    # Flat face reduction
    flat_cut = Box(bore_radius * 2.0, bore_radius * 2.0, pocket_depth + 2)
    flat_cut = flat_cut.translate((bore_radius + flat_depth, 0, 0))

    bore_pocket = bore_round - flat_cut

    # Position at knob top
    bore_pocket = bore_pocket.translate((0, 0, knob_height - pocket_depth / 2))

    # Subtract bore from body
    knob = body - bore_pocket

    # Smooth all edges
    knob = polish(knob, knob.edges(), 1.0)

    return knob
