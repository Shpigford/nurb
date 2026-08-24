from nurb import *

@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5, knob_diameter=34.0, knob_height=14.0):
    """Replacement knob for a D-shaft valve.

    shaft_diameter: diameter of the circular side of the D-stem
    shaft_across_flat: width of the flat side of the D-stem
    knob_diameter: nominal diameter of the knob body
    knob_height: height of the knob above the stem
    """

    # Bore dimensions with clearance for 0.3mm grown stem to fit, 1.0mm to jam
    bore_clearance = 0.35
    bore_diameter = shaft_diameter + 2 * bore_clearance
    bore_across_flat = shaft_across_flat + 2 * bore_clearance
    bore_depth = 11.0  # Reduced to avoid intersecting with bed level

    # The D-shaft geometry
    bore_radius = bore_diameter / 2.0
    flat_cutoff = bore_diameter - bore_across_flat
    flat_distance_from_center = bore_radius - flat_cutoff

    # Create main knob as a cylinder
    knob = Cylinder(radius=knob_diameter / 2.0, height=knob_height)

    # Add octagonal cross-section by cutting corners for grip
    # Cut 4 corner boxes to create an octagonal shape
    # Start the cuts above the base to avoid bed_bevel issues
    corner_cut_depth = 3.0  # How much to cut off each corner
    corner_height = knob_height - 3.5  # Leave bottom flat
    corner_start_z = 2.5  # Start cuts above the base

    corner_size = corner_cut_depth * 1.5
    offset = knob_diameter / 2.0 - corner_cut_depth / 2.0

    # Create 4 corner cuts (45 degree cuts on 4 corners)
    # Corner 1: +X, +Y
    corner1 = Box(length=corner_size, width=corner_size, height=corner_height)
    corner1 = corner1.translate((offset, offset, corner_start_z + corner_height / 2.0))

    # Corner 2: +X, -Y
    corner2 = Box(length=corner_size, width=corner_size, height=corner_height)
    corner2 = corner2.translate((offset, -offset, corner_start_z + corner_height / 2.0))

    # Corner 3: -X, +Y
    corner3 = Box(length=corner_size, width=corner_size, height=corner_height)
    corner3 = corner3.translate((-offset, offset, corner_start_z + corner_height / 2.0))

    # Corner 4: -X, -Y
    corner4 = Box(length=corner_size, width=corner_size, height=corner_height)
    corner4 = corner4.translate((-offset, -offset, corner_start_z + corner_height / 2.0))

    # Subtract the corners to create octagonal profile in the upper portion
    knob = knob - corner1 - corner2 - corner3 - corner4

    # Create the D-shaped bore at the top
    bore_cylinder = Cylinder(radius=bore_radius, height=bore_depth)
    bore_cylinder = bore_cylinder.translate((0, 0, knob_height - bore_depth / 2.0))

    # Create a box to subtract for the flat part of the D
    flat_removal_height = bore_diameter * 2
    flat_removal_width = bore_diameter * 2
    flat_removal_depth = (bore_radius - flat_distance_from_center) + 1.0

    flat_box = Box(
        length=flat_removal_width,
        width=flat_removal_height,
        height=flat_removal_depth
    )
    flat_box = flat_box.translate((0, -flat_distance_from_center - flat_removal_depth / 2.0, knob_height - bore_depth / 2.0))

    # Create the D-bore
    bore = bore_cylinder - flat_box

    # Subtract the bore from the knob
    knob = knob - bore

    return knob
