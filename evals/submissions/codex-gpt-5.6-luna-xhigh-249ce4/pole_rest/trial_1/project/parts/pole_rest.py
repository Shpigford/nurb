import math

from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter")):
    """
    A support-free U-shaped cradle for a freshly finished pole.

    pole_diameter: diameter of the pole being dried
    """
    pole_radius = pole_diameter / 2.0
    clearance = 0.15
    material = 1.2
    inner_radius = pole_radius + clearance
    outer_radius = inner_radius + material

    length = 30.0
    base_width = 28.0
    base_height = 7.5
    axis_height = 18.0

    # The base is deliberately wider than the cradle and gives a large, flat
    # first layer.  Its top stops below the pole's lowest point, leaving the
    # curved inner face as the actual seating surface.
    base = Box(
        base_width,
        length,
        base_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Approximate a 140 degree lower arc with short tangent facets.  Each
    # facet stays at least `clearance` outside the pole, while the printable
    # outer sides rise at less than 45 degrees instead of making an unsupported
    # circular overhang.
    facet_angle = 10.0
    facet_radius = inner_radius / math.cos(math.radians(facet_angle / 2.0))
    arc_angles = [200.0 + i * facet_angle for i in range(15)]
    inner_points = [
        (
            facet_radius * math.cos(math.radians(angle)),
            axis_height + facet_radius * math.sin(math.radians(angle)),
        )
        for angle in arc_angles
    ]
    endpoint_z = inner_points[0][1]
    outer_bottom_z = 6.5
    outer_bottom_x = 6.0
    outer_slope = 0.95
    outer_top_x = outer_bottom_x + outer_slope * (endpoint_z - outer_bottom_z)
    profile_points = list(reversed(inner_points))
    profile_points.extend(
        [
            (-outer_top_x, endpoint_z),
            (-outer_bottom_x, outer_bottom_z),
            (outer_bottom_x, outer_bottom_z),
            (outer_top_x, endpoint_z),
        ]
    )
    profile = make_face(Polygon(*profile_points, align=None))
    cradle = extrude(profile, amount=length)
    cradle = cradle.rotate(Axis.X, 90).translate((0, length / 2.0, 0))

    body = base + cradle

    # Keep the bed face and the functional cradle facets exact.  Chamfering the
    # repeated concave seat edges would create cosmetic strips and thin the
    # 1.2 mm backing below the printer's reliable wall threshold.
    return body
