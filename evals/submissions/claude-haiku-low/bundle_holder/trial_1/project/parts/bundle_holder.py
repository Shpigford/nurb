from nurb import *

@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """Wall-mounted cable bundle holder.

    bundle_diameter: diameter of the cable bundle to hold
    """

    # Geometry
    holding_dia = bundle_diameter + 0.8
    hole_radius = 4.4 / 2

    # Main body dimensions
    body_y = 12.0  # Length along bundle (≥ 10mm requirement)
    body_z = 12.0  # Height
    body_x = 7.0   # Depth

    # Create main rectangular body
    body = Box(body_y, body_z, body_x)

    # Create rectangular slot for bundle
    slot_height = holding_dia + 1
    slot = Box(body_y, slot_height, 3)
    slot = slot.translate(Vector(body_x / 2 - 1.5, 0, body_z / 2 - holding_dia / 2))

    # Drill screw hole on back face
    hole = Cylinder(hole_radius, body_x + 1)
    hole = hole.rotate(Axis.X, 90)
    hole = hole.translate(Vector(-body_x / 2, 0, body_z / 2 - 1.5))

    # Combine
    result = body - slot - hole

    if draft:
        return result

    return polish(result, result.edges(), 1.0)
