from nurb import *

@part
def pole_rest(pole_diameter=20.0):
    """
    Cradle rest that holds a drying pole horizontally.
    The pole's axis runs along Y at a fixed height (Z=18.0 mm) above the bed,
    centered over the part. The cradle supports it from below without blocking
    drop-in from above.

    pole_diameter: diameter of the pole (mm)
    """

    pole_radius = pole_diameter / 2.0
    pole_center_z = 18.0

    inner_radius = pole_radius + 0.1
    outer_radius = inner_radius + 1.2

    # Build base platform (sits on bed at Z=0, sized for volume efficiency)
    # Base width must cover cradle (~22.6mm across), minimum footprint 200 mm², minimum Y 20mm
    base_height = 4.5  # Must reach cradle bottom
    base = Box(26, 60, base_height).translate((0, 0, base_height / 2))

    # Build cradle shell (cylinder height is 2x outer_radius for semicircular support)
    cyl_height = outer_radius * 2.4  # ~23mm for 20mm pole
    outer_cyl = Cylinder(outer_radius, cyl_height).translate((0, 0, pole_center_z))
    inner_cyl = Cylinder(inner_radius, cyl_height).translate((0, 0, pole_center_z))

    # Create cylindrical shell
    shell = outer_cyl - inner_cyl

    # Cut away upper hemisphere to create open cradle allowing drop-in
    # Box positioned so it cuts from Z=pole_center_z upward
    upper_cut = Box(1000, 60, 1000).translate((0, 0, 500 + pole_center_z))
    cradle = shell - upper_cut

    # Combine base and cradle
    result = base.fuse(cradle)

    return result
