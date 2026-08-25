from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall holder for a cable bundle running along Y.

    bundle_diameter: diameter of the cable bundle that the holder retains
    """
    if bundle_diameter < 2.0:
        reject("bundle_diameter must be at least 2.0 mm for a printable holder", param="bundle_diameter")

    # The holder is a shallow, grounded channel. Its rear spine carries the
    # screw boss; the two short end sections are intentionally open around the
    # screw head so the M4 driver can pass through the holder.
    length = 18.0
    back_depth = 2.4
    shelf_x = 12.5
    shelf_level = 10.5
    shelf_thickness = 2.6
    rail_x = 9.8
    rail_thickness = shelf_x - rail_x
    boss_y = 3.75
    boss_width = 10.5
    boss_height = 10.5
    screw_y = boss_y + boss_width / 2.0
    screw_z = boss_height / 2.0

    # Leave 0.4 mm total clearance below the bundle. The bundle is placed over
    # the shelf for the retention checks; its X centre is inside the front rail
    # by 0.8 mm, so a 1 mm outward move strikes the rail.
    bundle_clearance = 0.4
    bundle_bottom = shelf_level + shelf_thickness + bundle_clearance
    bundle_center_z = bundle_bottom + bundle_diameter / 2.0
    rail_height = max(6.4, bundle_center_z + 1.0 - (shelf_level + shelf_thickness))

    def box_at(x, y, z, dx, dy, dz):
        return Pos(x, y, z) * Box(dx, dy, dz, align=(Align.MIN, Align.MIN, Align.MIN))

    # A continuous rear spine is grounded and gives a large flat wall face.
    body = box_at(0.0, 0.0, 0.0, back_depth, length, shelf_level)

    # Two end shelves and rails retain the bundle while leaving a clear driver
    # corridor around the screw head.
    for y in (0.0, length - 4.0):
        # Grounded ribs carry the shelf in short, printable spans rather than
        # asking the printer to bridge the full reach from the rear spine.
        body += box_at(rail_x, y, 0.0, rail_thickness, 4.0, shelf_level)
        body += box_at(4.8, y, 0.0, 1.2, 4.0, shelf_level)
        body += box_at(7.2, y, 0.0, 1.2, 4.0, shelf_level)
        body += box_at(back_depth, y, shelf_level, shelf_x - back_depth, 4.0, shelf_thickness)
        body += box_at(rail_x, y, shelf_level + shelf_thickness, rail_thickness, 4.0, rail_height)

    # The M4 boss is below the bundle, so the installed screw and cable can
    # coexist without sharing the cable's retained volume.
    body += box_at(0.0, boss_y, 0.0, 5.0, boss_width, boss_height)

    # 4.4 mm through-bore from the wall-facing side. The wider recess starts
    # after 3.0 mm of material, giving the pan head a solid seating ring.
    bore = Pos(0.0, screw_y, screw_z) * Rot(Y=90) * Cylinder(
        2.2, 5.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    head_pocket = Pos(3.0, screw_y, screw_z) * Rot(Y=90) * Cylinder(
        4.25, 2.3, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    body = body - bore - head_pocket

    # The screw seat, rail tips, and narrow support ribs are all fit-critical;
    # leaving these edges sharp avoids chamfer slivers and keeps every wall at
    # or above the printer's reliable 1 mm section threshold.
    return body
