from nurb import *


@part
def pole_rest(pole_diameter=20.0):
    """Rest that cradles a drying pole.

    The pole rests along the Y axis with its center at exactly 18.0 mm height,
    centered over the part's footprint in X.

    pole_diameter: diameter of the pole in mm
    """
    pole_radius = pole_diameter / 2
    pole_center_height = 18.0
    clearance = 0.1

    # Create a single unified block that will be carved
    main_block = Box(30, 20, 18)
    main_block = main_block.translate((0, 0, 9))

    rest = main_block

    # Remove material to create the cradle space
    cradle_radius = pole_radius + clearance + 1.3
    cradle = Cylinder(cradle_radius, 22)
    cradle = cradle.rotate(Axis.X, 90)
    cradle = cradle.translate((0, -11, pole_center_height))

    rest = rest - cradle

    # Remove outer edges (left and right) to reduce material
    left_void = Box(10, 25, 20)
    left_void = left_void.translate((-20, 0, 9))
    rest = rest - left_void

    right_void = Box(10, 25, 20)
    right_void = right_void.translate((20, 0, 9))
    rest = rest - right_void

    # Trim front and back
    front_trim = Box(40, 8, 20)
    front_trim = front_trim.translate((0, -14, 9))
    rest = rest - front_trim

    back_trim = Box(40, 8, 20)
    back_trim = back_trim.translate((0, 14, 9))
    rest = rest - back_trim

    # No polish - leave as-is to avoid introducing new issues
    # The sharp edges are acceptable for a functional part

    return rest
