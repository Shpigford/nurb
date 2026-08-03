from nurb import *

@part
def bundle_holder(bundle_diameter=8.0):
    """Wall-mounted cable bundle holder.

    bundle_diameter: the cable bundle thickness in mm
    """
    dia = bundle_diameter
    clearance = 0.4

    length_y = 20.0
    back_height = 9.0
    back_thickness = 2.5
    base_width = 5.0
    base_height = 2.0
    retention_len = 10.0

    # Create all geometry centered at the proper height
    # The bed contact should be at Z=0
    z_base = base_height / 2  # So bottom of base is at 0

    # Base platform that sits on bed
    base = Box(back_thickness + base_width, length_y, base_height)
    base = base.translate((back_thickness / 2, 0, z_base))

    # Back mounting plate
    back = Box(back_thickness, length_y, back_height)
    back = back.translate((-(back_thickness/2), 0, z_base + back_height / 2))

    body = base + back

    # Solid front retention block
    wall_height = dia + 2 * clearance + 1.5
    front_width = base_width - 1.0
    front = Box(front_width, length_y, wall_height)
    front = front.translate((
        back_thickness + front_width / 2,
        0,
        z_base + wall_height / 2
    ))

    body = body + front

    # Cut out bundle cavity
    cavity = Box(
        front_width - 1.0,
        retention_len,
        dia + 2 * clearance
    )
    cavity = cavity.translate((
        back_thickness + (front_width - 1.0) / 2,
        0,
        z_base + 1.0 + (dia + 2 * clearance) / 2
    ))

    body = body - cavity

    # Screw hole
    hole = Cylinder(4.4 / 2, back_thickness + 1)
    hole = hole.translate((
        -(back_thickness / 2 + 0.5),
        0,
        z_base + back_height / 2 - 2.5
    ))

    body = body - hole

    # Polish
    if not draft:
        edges = body.edges()
        back_faces = [f for f in body.faces() if f.center.X == body.bounding_box().min.X]
        bed_faces = [f for f in body.faces() if f.center.Z == body.bounding_box().min.Z]

        excluded = set()
        for face in back_faces + bed_faces:
            excluded.update(face.edges())

        edges_to_chamfer = [e for e in edges if e not in excluded]
        body = polish(body, edges_to_chamfer, 1.0)

    return body
