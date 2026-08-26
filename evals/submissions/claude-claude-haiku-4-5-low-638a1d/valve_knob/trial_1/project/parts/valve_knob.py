from build123d import *
from nurb import *


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
    knob_height: float = 16.0,
    bottom_diameter: float = 33.0,
):
    """D-shaft valve knob with torque transmission via flat bore.
    The bore opens upward on the vertical centerline with the shaft's flat facing +X.

    shaft_diameter: stem diameter at widest point (mm)
    shaft_across_flat: stem width across the flat (mm)
    knob_height: total height of knob (mm)
    bottom_diameter: diameter of knob base for grip (mm)
    """

    # Main knob body
    knob = Cylinder(radius=bottom_diameter / 2, height=knob_height)

    # Bore dimensions: fit 0.3mm grown stem, jam 1.0mm grown stem
    # With 0.3mm clearance on all sides
    bore_diameter = shaft_diameter + 0.6  # 8.6 mm
    bore_flat_width = shaft_across_flat + 0.6  # 7.1 mm

    # Distance from center to the flat side (preserved from shaft proportions)
    flat_depth = (shaft_diameter - shaft_across_flat) / 2  # 0.75 mm

    # Bore extends 13mm up into the knob (1mm past stem height of 12mm)
    bore_height = 13.0
    bore_z = knob_height - bore_height

    # Create D-shaped bore with two parts
    with BuildSketch(Plane.XY) as sketch:
        # Outer circle part of the D
        Circle(bore_diameter / 2)
    bore_round = extrude(sketch.sketch, amount=bore_height)

    # Flat part of the D - creates the torque-transmitting flat
    # The flat extends inward from the bore to ensure contact
    flat_reach = bore_diameter / 2 + 0.5  # Extends past center

    with BuildSketch(Plane.XY) as flat_sketch:
        Rectangle(bore_flat_width, flat_reach * 2, align=(Align.CENTER, Align.MIN))
    bore_flat = extrude(flat_sketch.sketch, amount=bore_height)

    # Position the flat so its outer edge is at -Y (shaft flat facing +X means -Y face)
    bore_flat = bore_flat.move(Location((0, -flat_reach + flat_depth, 0)))

    # Combine bore components
    bore = bore_round
    bore = bore.fuse(bore_flat)
    bore = bore.move(Location((0, 0, bore_z)))

    # Cut bore from knob
    result = knob.cut(bore)

    return result
