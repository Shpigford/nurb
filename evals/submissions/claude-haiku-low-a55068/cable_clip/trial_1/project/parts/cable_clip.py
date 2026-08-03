from nurb import *

@part
def cable_clip(bundle_diameter: float = 8.0, draft: bool = False):
    """
    Screw-down cable clip for bundled cables.

    bundle_diameter: diameter of the cable bundle in mm
    """
    # Dimensions
    ch_w = bundle_diameter + 0.4  # Channel inner width
    ch_d = bundle_diameter  # Channel inner depth
    wall_t = 2.4  # Wall thickness
    base_t = 3.0  # Base thickness
    len_y = 12.0  # Length along Y (cable direction)
    tab_l = 10.0  # Tab length
    hole_d = 4.2  # Hole diameter

    # Derived dimensions
    ch_tot_w = ch_w + 2 * wall_t  # Total channel structure width: 8.4 + 4.8 = 13.2
    tot_w = ch_tot_w + tab_l  # Total width: 13.2 + 10 = 23.2
    tot_h = base_t + ch_d  # Total height: 3 + 8 = 11

    # Channel structure center in centered coordinates
    ch_center = -tot_w/2 + ch_tot_w/2

    # Create base box (full footprint at bottom)
    base = Box(tot_w, len_y, base_t).moved(Pos(0, 0, base_t / 2))

    # Create left channel wall (2.4 x 12 x 8)
    left_wall = Box(wall_t, len_y, ch_d).moved(
        Pos(ch_center - ch_tot_w/2 + wall_t/2, 0, base_t + ch_d/2)
    )

    # Create right channel wall (2.4 x 12 x 8)
    right_wall = Box(wall_t, len_y, ch_d).moved(
        Pos(ch_center + ch_tot_w/2 - wall_t/2, 0, base_t + ch_d/2)
    )

    # Create mounting tab (10 x 12 x 3)
    tab = Box(tab_l, len_y, base_t).moved(
        Pos(tot_w/2 - tab_l/2, 0, base_t/2)
    )

    # Combine all solids
    clip = base + left_wall + right_wall + tab

    # Create and subtract through-hole in tab (centered in tab)
    hole_center_x = ch_tot_w / 2  # Center of the tab
    hole = Cylinder(hole_d / 2, tot_h + 2).moved(
        Pos(hole_center_x, 0, -1)
    )

    clip = clip - hole

    return clip
