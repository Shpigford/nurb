from nurb import *

@part
def pole_rest(pole_diameter: float = 20.0):
    """Rest that cradles a drying pole.

    pole_diameter: diameter of the pole, in mm
    """
    pole_radius = pole_diameter / 2.0
    pole_axis_height = 18.0
    clearance = 0.4
    backing_thickness = 1.2

    # Dimensions
    base_width = 25.0
    base_length = 25.0
    base_height = 1.5

    cradle_outer = pole_radius + clearance + backing_thickness

    # Create one unified tall base that provides all support
    # This ensures single solid with no connectivity issues
    unified_height = pole_axis_height
    unified_base = Box(base_width, base_length, unified_height)
    unified_base = unified_base.translate((0, 0, unified_height / 2))

    # Add cylindrical cradle on top of the unified base
    # Use the full cylinder for proper cradle geometry
    cradle_cyl = Cylinder(radius=cradle_outer, height=base_length)
    cradle_cyl = cradle_cyl.rotate(Axis.X, 90)
    cradle_cyl = cradle_cyl.translate((0, 0, pole_axis_height))

    # Combine into one solid
    result = unified_base + cradle_cyl

    return result
