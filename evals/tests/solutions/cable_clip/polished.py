from nurb import *

# Fable's first real trial, verbatim except the measured() default: the doctrine's
# polish pass on every outside edge, fit geometry kept square. The scorer must
# score this 1.0; a task that punishes the shipped skill is measuring obedience
# to an unstated rule.


@part
def cable_clip(
    bundle_diameter=8.0,
    cable_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    tab_thickness=3.0,
    screw_hole_width=4.2,
    chamfer_size=1.0,
    draft=False,
):
    """A screw-down clip: an open-top channel for the cable, a flat tab for the screw.

    bundle_diameter: how wide the cable bundle measures across
    cable_clearance: extra channel width so the bundle drops in without forcing
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable
    clip_length: how long the clip runs along the cable
    tab_length: how far the mounting tab sticks out sideways
    tab_thickness: how thick the mounting tab is
    screw_hole_width: the diameter of the screw hole in the tab
    chamfer_size: the chamfer on outside edges
    """
    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth

    body = Box(body_width, clip_length, height,
               align=(Align.MIN, Align.MIN, Align.MIN))
    body -= Pos(wall_thickness, 0, base_thickness) * Box(
        channel_width, clip_length, channel_depth + 1.0,
        align=(Align.MIN, Align.MIN, Align.MIN))

    tab = Pos(body_width, 0, 0) * Box(
        tab_length, clip_length, tab_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN))
    hole_x = body_width + tab_length / 2
    hole_y = clip_length / 2
    clip = (body + tab) - Pos(hole_x, hole_y, tab_thickness / 2) * Cylinder(
        screw_hole_width / 2, tab_thickness + 2.0)

    if draft:
        return clip

    # The channel is fit geometry and stays square; the bottom is the bed face;
    # the screw hole keeps its measured diameter; concave junctions are never polished.
    tol = 0.01
    concave = concave_edges(clip)

    def is_concave(e):
        c = e.center()
        return any((c - ce.center()).length < tol for ce in concave)

    def on_bottom(e):
        return e.bounding_box().max.Z < tol

    def in_channel(e):
        bb = e.bounding_box()
        return (bb.min.X > wall_thickness - tol
                and bb.max.X < wall_thickness + channel_width + tol
                and bb.min.Z > base_thickness - tol)

    def on_hole(e):
        c = e.center()
        return Vector(c.X - hole_x, c.Y - hole_y, 0).length < screw_hole_width

    def lands_on_tab(e):
        # The wall's vertical corners above the tab: chamfering them runs out
        # into the tab's top face as a compound-angle notch, so they stay sharp.
        bb = e.bounding_box()
        return (abs(bb.min.X - body_width) < tol
                and abs(bb.max.X - body_width) < tol
                and abs(bb.min.Z - tab_thickness) < tol
                and bb.max.Z > bb.min.Z + tol)

    def crosses_the_part(e):
        # Horizontal edges running along X sit on the wall tops and tab top at
        # the part's ends: chamfering one shaves the channel depth and tab
        # thickness at the ends, and those dimensions hold everywhere.
        bb = e.bounding_box()
        return bb.max.Y - bb.min.Y < tol and bb.max.Z - bb.min.Z < tol

    keep = clip.edges().filter_by(
        lambda e: not (on_bottom(e) or in_channel(e) or on_hole(e)
                       or is_concave(e) or lands_on_tab(e)
                       or crosses_the_part(e)))
    return polish(clip, keep, chamfer_size)
