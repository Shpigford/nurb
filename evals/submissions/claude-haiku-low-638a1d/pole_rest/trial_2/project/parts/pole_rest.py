from nurb import *

@part
def pole_rest(pole_diameter=20.0):
    """Rest holding a drying pole, cradled to protect the soft finish.

    pole_diameter: diameter of the pole to hold (mm)
    """

    pole_radius = pole_diameter / 2
    pole_axis_z = 18.0  # Pole center height

    # Large flat base on the bed (>200mm² footprint, >20mm along Y)
    # Make base thick enough that 1mm chamfer won't reach the bed
    base = Box(40, 30, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Support web above base - narrower to hold just the cradle
    support_width = 18
    support_height = pole_axis_z - 5 - pole_radius + 1.5
    support = Box(support_width, 30, support_height, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((0, 0, 5))

    # Combine base and support into solid form
    part = base + support

    # Create a cylindrical cavity for the cradle
    # The cavity outer radius is pole_radius + 0.1 for slight clearance
    # The cavity inner radius is pole_radius - 1.2 for backing material

    cavity_outer = pole_radius + 0.1
    cavity_inner = pole_radius - 1.2

    # Create the cylindrical cavity by subtracting cylinders
    outer_cyl = Cylinder(cavity_outer, 32, align=(Align.CENTER, Align.CENTER, Align.CENTER)).translate((0, 0, pole_axis_z))
    inner_cyl = Cylinder(cavity_inner, 32, align=(Align.CENTER, Align.CENTER, Align.CENTER)).translate((0, 0, pole_axis_z))

    # Create annular cylinder (hollow)
    annular = outer_cyl - inner_cyl

    # Make it semi-cylindrical by cutting away the top half
    # Cut everything above z = pole_axis_z
    cutting_box = Box(60, 60, 60, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((0, 0, pole_axis_z))
    semi_annular = annular - cutting_box

    # Cut this from the main part
    part = part - semi_annular

    # Skip polishing to avoid bed contact issues for now
    return part
