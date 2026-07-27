"""Bin - Small Parts - 3x. Read bin_small_parts.md before changing anything."""

from nurb import *

from system import (
    BLOCK_WIDTH,
    EPS,
    FLOOR_X,
    MIN_ITEM_DEPTH,
    OVERSHOOT,
    plate_width,
    polish as polish_pass,
    polish_edges,
    slab,
    span,
)


@part
def bin_small_parts(
    bracket_count=3,
    item_height=60.0,
    item_depth=6.0,
    bin_depth=65.0,
    wall_thick=2.5,
    floor_thick=3.0,
    front_drop=20.0,
    bin_overlap=1.0,
    structural_chamfer=3.0,
    scoop_fillet=5.0,
    chamfer_size=1.0,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material behind the channel floor, so the "
            f"bin would not reach the slab. Raise it above {MIN_ITEM_DEPTH}."
        )

    # The body reaches back into the slab so the two interpenetrate and fuse to one
    # solid. It must still stop short of the dovetail, or the part will not go on.
    block_back = -(item_depth - bin_overlap)
    if block_back >= FLOOR_X:
        raise ValueError(
            f"bin_overlap {bin_overlap} puts the body's back face at x={block_back:.2f}, "
            f"in the dovetail, which starts at x={FLOOR_X}. Keep item_depth - bin_overlap "
            f"above {-FLOOR_X}."
        )

    if bin_depth <= item_depth + 2 * wall_thick:
        raise ValueError(
            f"bin_depth {bin_depth} is not deep enough for a {wall_thick}mm front wall "
            f"behind a {item_depth}mm slab, so there is no cavity. Raise it above "
            f"{item_depth + 2 * wall_thick}."
        )

    # Two different things limit the drop, and both fail as geometry rather than as an
    # error: too tall and the front wall goes under the floor, too deep and the ramp
    # runs back into the slab.
    drop_limit = min(item_height - floor_thick, bin_depth - item_depth)
    if front_drop >= drop_limit:
        raise ValueError(
            f"front_drop {front_drop} is past the {drop_limit}mm this bin has room for: "
            f"the wall is {item_height - floor_thick}mm tall above the floor and the 45 "
            f"degree ramp has {bin_depth - item_depth}mm of run before it reaches the slab."
        )

    interior_depth = bin_depth - wall_thick - item_depth
    interior_height = item_height - floor_thick - front_drop
    if scoop_fillet >= min(interior_depth, interior_height):
        raise ValueError(
            f"scoop_fillet {scoop_fillet} does not fit the corner it rounds: the floor is "
            f"{interior_depth}mm long and the front wall {interior_height}mm tall above it. "
            f"Keep it under {min(interior_depth, interior_height)}."
        )

    y0 = -BLOCK_WIDTH / 2  # the plate's own datum, since its boxes build from a corner
    width = plate_width(bracket_count)
    mid = span(bracket_count)

    back = slab(bracket_count, item_height, item_depth)

    # The bin is a solid block hollowed out, not four walls assembled. Same footprint as
    # the slab: anything wider clips the next bracket's comb lobe.
    block = Pos(-bin_depth, y0, -item_height) * Box(
        bin_depth + block_back, width, item_height, align=None
    )
    body = back + block

    # The cavity stops at the slab front, x = -item_depth, and not at the block's back
    # face. That 1.8mm of slab left standing is the web behind each channel, and the
    # detent dimple eats 0.8 of it.
    floor_z = -item_height + floor_thick
    cavity = Pos(-(bin_depth - wall_thick), y0 + wall_thick, floor_z) * Box(
        interior_depth, width - 2 * wall_thick, OVERSHOOT - floor_z, align=None
    )

    # The front wall comes down between the side walls only. Full width instead and the
    # ramp lands on a flat instead of on the front corner, leaving a wall_thick step.
    lower = Pos(-bin_depth - OVERSHOOT, y0 + wall_thick, -front_drop) * Box(
        wall_thick + 2 * OVERSHOOT, width - 2 * wall_thick, front_drop + OVERSHOOT, align=None
    )

    # The 45 degree ramps, run equal to rise, landing on the front face at -front_drop.
    # Cut across the whole width in one two-sided extrude. A one-directional cut from a
    # section on y=0 reaches the far wall and silently leaves the near one square, which
    # is a bug that builds, exports and looks fine from one side.
    section = Plane.XZ * Polygon(
        (-bin_depth - OVERSHOOT, -front_drop - OVERSHOOT),
        (-(bin_depth - front_drop) + OVERSHOOT, OVERSHOOT),
        (-bin_depth - OVERSHOOT, OVERSHOOT),
        align=None,
    )
    taper = Pos(0, mid, 0) * extrude(section, width / 2 + OVERSHOOT, both=True)

    body = body - [cavity, lower, taper]

    # Small parts sweep out of a rounded crease and jam in a sharp one.
    scoop = body.edges().filter_by(Axis.Y).filter_by(
        lambda e: abs(e.center().X + bin_depth - wall_thick) < EPS
        and abs(e.center().Z - floor_z) < EPS
    )
    body = fillet(scoop, scoop_fillet)

    # Structural, 3mm, at the one corner the load runs through: a full cup of hardware
    # hangs off the floor and pries it away from the slab. The side walls are the
    # gussets, so at this ratio nothing else is needed.
    load = body.edges().filter_by(Axis.Y).filter_by(
        lambda e: abs(e.center().X + item_depth) < EPS
        and abs(e.center().Z - floor_z) < EPS
    )
    body = chamfer(load, structural_chamfer)
    if draft:
        return body

    # Cosmetic, 1mm. The bin's outside is three kinds of face: the front and the two
    # flanks (OUTER), anything looking up (TOP), and the two ramps (TAPER). Bevel every
    # edge where two of them meet, which keeps the cavity rim sharp, and drop the
    # TOP/TAPER pair: those are only wall_thick long and a bevel there has nowhere to
    # land.
    slope = Vector(-1, 0, 1).normalized()

    def facing(face):
        return face.normal_at(face.center())

    def is_front(face):
        return abs(facing(face).X + 1) < EPS and abs(face.center().X + bin_depth) < EPS

    def is_outer(face):
        n, c = facing(face), face.center()
        return (
            is_front(face)
            or (abs(n.Y + 1) < EPS and abs(c.Y - y0) < EPS)
            or (abs(n.Y - 1) < EPS and abs(c.Y - (y0 + width)) < EPS)
        )

    # A ramp is the slope-facing face that reaches the top. The test matters because a
    # 1mm bevel on a top rim faces exactly the same way a 45 degree ramp does, so once
    # the first pass has run the two are indistinguishable by normal alone.
    def is_ramp(face):
        return (facing(face) - slope).length < EPS and face.bounding_box().max.Z > -EPS

    def between(shape, left, right):
        pair = {e for f in shape.faces() if left(f) for e in f.edges()}
        return pair & {e for f in shape.faces() if right(f) for e in f.edges()}

    tops = [f for f in body.faces() if abs(facing(f).Z - 1) < EPS]
    skin = {}
    for face in [f for f in body.faces() if is_outer(f) or is_ramp(f)] + tops:
        for edge in face.edges():
            skin[edge] = skin.get(edge, 0) + 1
    junction = between(body, is_ramp, lambda f: abs(facing(f).Z - 1) < EPS)

    # The bevel where the ramp lands on the front face has to wait for a second pass.
    # It cannot be cut on a clean body at any size: its inner end is a point where four
    # faces meet and only three edges do, since the front face and the side wall's inner
    # face touch there without sharing an edge, and OCCT has no cap for that. The first
    # pass takes the front rim's own bevel down past that point, which gives the two
    # faces a real edge between them, and then the wrap builds.
    wrap = between(body, is_ramp, is_front)
    polish = polish_edges(body, item_height).filter_by(
        lambda e: skin.get(e, 0) == 2 and e not in junction and e not in wrap
    )
    body = chamfer(polish, chamfer_size)
    return polish_pass(body, list(between(body, is_ramp, is_front)), chamfer_size)
