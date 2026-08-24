from nurb import *

@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5):
    """
    Replacement knob for a D-shaft valve handle.

    The knob bore-up as it prints: bore opens straight up on the part's vertical
    centerline, with the stem's flat facing +X. In use the knob flips over onto
    the stem.

    shaft_diameter: D-shaft outer diameter (mm)
    shaft_across_flat: D-shaft flat-to-flat width (mm)
    """

    # Dimensions optimized for volume budget and functionality
    knob_height = 20
    knob_diameter = 28

    # Main cylindrical body
    body = Cylinder(radius=knob_diameter/2, height=knob_height)

    # D-shaped bore for the valve stem
    bore_depth = 12.5  # stem stands 12mm proud, plus margin

    # Bore sized to accept 0.3mm-grown stem (diameter + 0.6mm tolerance)
    # with minimal clearance for the jam/torque tests
    bore_diameter = shaft_diameter + 0.65
    bore_radius = bore_diameter / 2

    # Create bore: cylinder with flat cutout for D-shape
    bore = Cylinder(radius=bore_radius, height=bore_depth)

    # Rectangular notch for the flat side of the D-bore
    # The stem's flat faces +X, so the bore's flat (notch) faces -X
    notch_length = bore_radius + 1  # depth of the notch
    notch_width = bore_diameter + 1  # width to cut through the bore
    notch = Box(length=notch_length, width=notch_width, height=bore_depth + 1)
    notch = notch.moved(Location((-(bore_radius + notch_length/2), 0, -0.5)))

    bore = bore - notch

    # Position bore at top center of knob
    bore = bore.moved(Location((0, 0, knob_height - bore_depth)))

    # Create knob with bore
    knob = body - bore

    # Add grip features: 2 diametrically opposite lobes for gripping
    lobe_height = knob_height  # full height to ensure solid connection
    lobe_length = 8  # extends from cylinder surface outward
    lobe_width = 5
    lobe_reach = 4.2  # total reach beyond base radius

    for i in range(2):
        angle = i * 180  # 180 degrees apart
        # Position lobe so it overlaps with and extends beyond the cylinder
        lobe = Box(length=lobe_length, width=lobe_width, height=lobe_height)
        # Center the lobe at a position that overlaps the cylinder
        lobe = lobe.moved(Location((knob_diameter/2 + lobe_reach - lobe_length/2, 0, 0)))
        lobe = lobe.rotate(Axis.Z, angle)
        knob = knob + lobe

    # Polish all exposed edges for a finished appearance
    knob = polish(knob, knob.edges(), 1)

    return knob
