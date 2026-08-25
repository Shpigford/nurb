from nurb import *


@part
def pole_rest(pole_diameter: float = 20.0):
    """A low, continuous saddle for a freshly finished pole.

    pole_diameter: measured diameter of the pole the rest cradles
    """
    pole_radius = pole_diameter / 2
    pole_axis_height = 18.0
    clearance = 0.15
    cradle_thickness = 2.05
    rest_length = 22.0
    rest_width = 2 * (pole_radius + clearance + 3.0)
    buttress_width = 6.0

    # This wide base gives the part a stable, support-free footprint. The bore
    # below removes all material inside the pole's clearance envelope.
    base = Box(rest_width, rest_length, 10.0,
               align=(Align.CENTER, Align.CENTER, Align.MIN))

    # The lower half of an annulus makes a 180-degree, radially backed cradle.
    # The small vertical buttresses replace the two steep outer portions of that
    # annulus, so the rest remains support-free in its printed orientation.
    outer = Cylinder(pole_radius + clearance + cradle_thickness, rest_length,
                     align=(Align.CENTER, Align.CENTER, Align.CENTER),
                     rotation=(90, 0, 0)).translate((0, 0, pole_axis_height))
    inner = Cylinder(pole_radius + clearance, rest_length,
                     align=(Align.CENTER, Align.CENTER, Align.CENTER),
                     rotation=(90, 0, 0)).translate((0, 0, pole_axis_height))
    lower_half = Box(40.0, rest_length + 2.0, pole_axis_height,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    cradle = (outer & lower_half)
    buttress_offset = rest_width / 2 - buttress_width / 2
    left_buttress = Box(buttress_width, rest_length, pole_axis_height,
                         align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((-buttress_offset, 0, 0))
    right_buttress = Box(buttress_width, rest_length, pole_axis_height,
                          align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((buttress_offset, 0, 0))
    return (base + cradle + left_buttress + right_buttress) - inner
