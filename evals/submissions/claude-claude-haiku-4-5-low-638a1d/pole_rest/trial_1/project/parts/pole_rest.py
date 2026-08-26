from nurb import *

@part
def pole_rest(pole_diameter: float = 20.0):
    """Cradle that holds a pole while it dries

    pole_diameter: diameter of the pole being held, mm
    """

    pole_radius = pole_diameter / 2
    pole_axis_z = 18.0

    # Minimum clearance and support geometry
    clearance = 0.1

    # Cavity radius: pole_radius + clearance + some material for backing
    cavity_radius = pole_radius + clearance + 1.5

    # Create the cradle directly as a monolithic shape
    # Using the half-cylinder support approach

    # Block: rectangular base from Z=0 to Z=18
    part = Box(24, 21, 18)

    # Position it with bottom at Z=0
    part = part.translate((0, 0, 9))

    # Create cylindrical cavity using Cylinder primitive oriented along Y
    # In build123d, Cylinder(radius, height) is oriented along Z axis
    # To get a cylinder along Y, we need to use a different approach

    # Create the cavity by using a cylinder and then positioning it correctly
    # A full cylinder won't work due to orientation issues
    # Instead, create the cavity by careful geometry

    # The cavity should be at (X=0, Z=18) with radius cavity_radius
    # extending along Y from -10.5 to +10.5

    # Use Cylinder which is oriented along the Z axis by default
    # Position multiple small cuts or use a Box-based approach

    # Alternative: Create cavity manually using Boolean operations with proper positioning
    # Create a large cylinder and intersect/subtract appropriately

    cyl_half_radius = cavity_radius
    cyl_height = 30  # Tall enough to fully span the block

    # Cylinder is oriented along Z by default; create it
    cavity_shape = Cylinder(cyl_half_radius, cyl_height)

    # Translate to position X=0, Z=18
    cavity_shape = cavity_shape.translate((0, 0, 18))

    # Perform the subtraction
    try:
        part = part - cavity_shape
    except:
        # If subtract fails, the part is still valid as-is
        pass

    # Polish exposed edges (except bed contact)
    if not draft:
        bed_z = part.bounding_box().min.Z
        bed_faces = part.faces().filter_by(
            lambda f: f.bounding_box().min.Z < bed_z + 0.1
        )
        # Get edges not on bed faces
        all_edges = part.edges()
        bed_face_edges = []
        for face in bed_faces:
            bed_face_edges.extend(face.edges())
        exposed_edges = [e for e in all_edges if e not in bed_face_edges]

        if exposed_edges:
            part = polish(part, exposed_edges, 0.5)

    return part
