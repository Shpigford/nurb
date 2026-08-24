from build123d import *
from nurb import *
import math


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
):
    """
    Replacement knob for a valve stem with D-shaft bore.

    shaft_diameter: overall diameter of the D-shaped stem (mm)
    shaft_across_flat: width across the flat of the D-shaped stem (mm)
    """

    knob_height = 15
    base_d = 30
    mid_d = 36

    # Build body: wider at middle for grip, narrower at ends
    with BuildPart() as bp:
        # Bottom section
        Cylinder(radius=base_d / 2, height=5)

        # Middle section - wider for grip (overlap by 1mm with bottom)
        mid_cyl = Cylinder(radius=mid_d / 2, height=6)
        add(mid_cyl.translate((0, 0, 4)))

        # Top section (overlap by 2mm with middle)
        top_cyl = Cylinder(radius=mid_d / 2 - 0.5, height=5)
        add(top_cyl.translate((0, 0, 8)))

    body = bp.part

    # Create D-shaped bore with clearance
    bore_clearance = 0.32
    bore_diameter = shaft_diameter + 2 * bore_clearance
    bore_flat_width = shaft_across_flat + 2 * bore_clearance

    # Bore cylinder
    bore_cyl = Cylinder(
        radius=bore_diameter / 2,
        height=knob_height + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Calculate flat depth
    bore_radius = bore_diameter / 2
    flat_depth = math.sqrt(max(0, bore_radius**2 - (bore_flat_width / 2) ** 2))

    # Flat cut for D-shape
    flat_cut = Box(
        width=bore_flat_width + 0.5,
        length=flat_depth + 0.3,
        height=knob_height + 2,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )

    # D-shaped bore
    bore = bore_cyl - flat_cut

    # Remove bore from body
    knob = body - bore

    # Chamfer bore opening edges
    try:
        small_edges = [e for e in knob.edges() if e.length < 30 and e.length > 8]
        if small_edges:
            knob = chamfer(small_edges, length=0.6)
    except:
        pass

    # Add base for bed contact
    base = Cylinder(radius=base_d / 2 - 0.4, height=1.8)
    knob = knob + base

    # Polish all edges
    knob = polish(knob, knob.edges(), 0.7)

    return knob
