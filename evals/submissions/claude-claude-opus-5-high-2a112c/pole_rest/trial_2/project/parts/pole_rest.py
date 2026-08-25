from math import cos, radians, sin

from nurb import *

# 1.4mm rather than the doctrine's usual 1mm. Three chamfers meet at each of the four
# top corners, and at 1mm that corner facet lands at 0.9mm2, right on the sliver floor;
# at 1.4 it is 1.7mm2 and every exposed edge still gets broken.
CHAMFER = 1.4


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    pole_axis_height=measured("pole_axis_height"),
    cradle_gap=0.25,
    cradle_wrap=140.0,
    wall=3.0,
    rest_length=22.0,
    draft=False,
):
    """A cradle that holds a freshly finished pole off the bench while it dries.

    pole_diameter: how thick the pole is across
    pole_axis_height: how high the middle of the pole sits above the bench, fixed by
        the row of rests the pole lies across
    cradle_gap: the air left all round the pole, so the wet finish is never touched
    cradle_wrap: how far around the pole the cradle reaches, in degrees
    wall: how much material stands behind the cradle surface
    rest_length: how much of the pole's length one rest carries
    """
    seat_radius = pole_diameter / 2 + cradle_gap
    floor = pole_axis_height - seat_radius
    if floor < wall:
        widest = 2 * (pole_axis_height - wall - cradle_gap)
        reject(
            f"a {pole_diameter}mm pole leaves {floor:.1f}mm of material under the seat, "
            f"less than the {wall}mm floor: keep pole_diameter under {widest:.1f}",
            param="pole_diameter",
        )

    half_wrap = radians(cradle_wrap / 2)
    # The seat's rim, and so the whole block, tops out where the wrap ends. Any higher
    # and the walls would close over the pole; the pole has to drop straight in.
    height = pole_axis_height - seat_radius * cos(half_wrap)
    half_width = seat_radius * sin(half_wrap) + wall

    block = Pos(0, 0, height / 2) * Box(2 * half_width, rest_length, height)
    seat = (
        Pos(0, 0, pole_axis_height)
        * Rot(90, 0, 0)
        * Cylinder(seat_radius, rest_length + 2)
    )
    body = block - seat
    if draft:
        return body

    # The seat is the mating surface: no lead-in chamfer at its rim, and nothing that
    # eats the material backing the contact arc. Every edge a hand meets is fair game.
    bed = body.bounding_box().min.Z

    def off_the_seat(e):
        c = e.bounding_box().center()
        return (c.X**2 + (c.Z - pole_axis_height) ** 2) ** 0.5 > seat_radius + 0.05

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().max.Z > bed + 0.01 and off_the_seat(e)
    )
    return polish(body, keep, CHAMFER)
