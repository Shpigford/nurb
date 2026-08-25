from nurb import *


@part
def pole_rest(pole_diameter: float = measured("pole_diameter"), draft=False):
    """A support-free drying rest for a pole lying along Y.

    pole_diameter: diameter of the pole being dried
    """
    axis_height = 18.0
    pole_radius = pole_diameter / 2.0

    # The pole is kept 0.2 mm off the printed cradle surface, comfortably
    # inside the required 0.4 mm fit band.
    inner_radius = pole_radius + 0.20

    length = 28.0
    base_height = axis_height - inner_radius
    web_bottom_x = pole_radius * 0.80
    base_width = 2.0 * web_bottom_x + 1.0

    # A broad, flat base ends just below the pole's lowest point.  Its top
    # remains clear of the pole, but overlaps the two cradle webs for a robust
    # single-solid fuse.
    base = Box(
        base_width,
        length,
        base_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # The outer web is a straight, shallow slope.  It is deliberately farther
    # out than the nominal backing radius so every point behind the inner arc
    # has at least 1.2 mm of material in the radial direction.
    web_bottom_z = base_height - 0.20
    web_top_x = pole_radius + 3.0

    inner_tool = Pos(0.0, 0.0, axis_height) * Cylinder(
        inner_radius,
        length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        rotation=(90.0, 0.0, 0.0),
    )

    def web(sign):
        points = [
            (0.0, 0.0, web_bottom_z),
            (sign * web_bottom_x, 0.0, web_bottom_z),
            (sign * web_top_x, 0.0, axis_height),
            (0.0, 0.0, axis_height),
        ]
        outer = Pos(0.0, -length / 2.0, 0.0) * extrude(
            make_face(Polygon(*points)), amount=length, dir=(0.0, 1.0, 0.0)
        )
        return outer - inner_tool

    return base + web(1) + web(-1)
