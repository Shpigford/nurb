"""Holder - Bambu Scraper - 2x. Read holder_bambu_scraper.md before changing anything."""

from nurb import *

from system import (
    BLOCK_WIDTH,
    CHANNEL_DEPTH,
    CHANNEL_WIDTH,
    DETENT_DEPTH,
    OVERSHOOT,
    POCKET_WIDTH,
    channels,
    detent_dimples,
    polish_edges,
    span,
)

# Material that has to survive beside a dovetail. Below this the plate edge prints as a
# sliver rather than a wall, which is what a 47mm plate did on the first fit print.
MIN_WEB = 1.0


@part
def holder_bambu_scraper(
    bracket_count=2,
    item_height=32.0,
    item_depth=18.5,
    slab_width=50.0,
    slot_len=35.0,
    clamp_len=22.0,
    floor_thick=2.0,
    nest_back=6.5,
    front_wall=3.0,
    sill_depth=14.0,
    ramp_kick=4.0,
    ramp_rise=8.0,
    chamfer_size=1.0,
    draft=False,
):
    mid = span(bracket_count)

    # `slab_width` is the only dimension in this library that does not follow the
    # bracket run, and both ends of its band are physical. Narrow, and the plate edge
    # lands beside a dovetail with nothing printable between them. Wide, and it reaches
    # into where the next bracket on the wall sits. Fusion called the far end "clipping
    # the third comb lobe", which is that same wall constraint wearing the comb's
    # clothes rather than a modelling artifact.
    web = slab_width / 2 - mid - CHANNEL_WIDTH / 2
    if web < MIN_WEB:
        raise ValueError(
            f"slab_width {slab_width} leaves {web:.2f}mm of plate beside the outer "
            f"channel, which prints as a sliver against the dovetail rather than a wall. "
            f"At bracket_count {bracket_count} it has to be at least "
            f"{2 * (MIN_WEB + mid + CHANNEL_WIDTH / 2):.2f}."
        )
    reach = BLOCK_WIDTH * (bracket_count + 1) - POCKET_WIDTH
    if slab_width > reach:
        raise ValueError(
            f"slab_width {slab_width} runs into where the next bracket sits on the wall. "
            f"At bracket_count {bracket_count} it has to stay under {reach:.2f}."
        )
    if (slab_width - slot_len) / 2 < MIN_WEB:
        raise ValueError(
            f"a {slot_len}mm pocket in a {slab_width}mm plate leaves "
            f"{(slab_width - slot_len) / 2:.2f}mm of side rail, so the cavity opens out "
            f"the sides. Widen slab_width past {slot_len + 2 * MIN_WEB} or shorten slot_len."
        )

    cavity_depth = item_depth - nest_back - front_wall
    if cavity_depth <= 0:
        raise ValueError(
            f"nest_back {nest_back} plus front_wall {front_wall} is all of the "
            f"{item_depth}mm depth, so there is no pocket left. Raise item_depth above "
            f"{nest_back + front_wall}."
        )

    # The pocket's back wall stands in front of the detent dimple, not just in front of
    # the channel floor. That web is the thinnest section on the part.
    behind = nest_back - CHANNEL_DEPTH - DETENT_DEPTH
    if behind < MIN_WEB:
        raise ValueError(
            f"nest_back {nest_back} leaves {behind:.2f}mm between the pocket and the "
            f"detent dimple. Keep it at or above {CHANNEL_DEPTH + DETENT_DEPTH + MIN_WEB:.1f}."
        )

    floor_z = -(item_height - floor_thick)
    if sill_depth >= -floor_z:
        raise ValueError(
            f"sill_depth {sill_depth} cuts the front wall down to the pocket floor, which "
            f"opens the bottom of the part and lets the blade out. Keep it under "
            f"{-floor_z}, or raise item_height."
        )

    slab = Pos(-item_depth / 2, mid, -item_height / 2) * Box(
        item_depth, slab_width, item_height
    )
    back = slab - channels(bracket_count, item_height) - detent_dimples(bracket_count)

    # One cavity, blind. `floor_thick` of solid under it is what keeps a razor blade
    # inside the part, and it is the reason the pocket is not a through slot.
    pocket_back, pocket_front = -nest_back, -(item_depth - front_wall)
    pocket = Pos((pocket_back + pocket_front) / 2, mid, floor_z / 2) * Box(
        cavity_depth, slot_len, -floor_z
    )

    # The anti-kickback wedge, sitting on the pocket floor against its back wall. It
    # only ever narrows going up, so every layer lands on the one below and it prints
    # with no support. Drawn past the floor and past both side walls so trimming it out
    # of the pocket is never a coincident-face boolean.
    ramp = Plane.XZ * Polygon(
        (0, floor_z - OVERSHOOT),
        (pocket_back - ramp_kick, floor_z - OVERSHOOT),
        (pocket_back - ramp_kick, floor_z),
        (pocket_back, floor_z + ramp_rise),
        (0, floor_z + ramp_rise),
        align=None,
    )
    ramp = Pos(0, mid, 0) * extrude(ramp, slot_len / 2 + OVERSHOOT, both=True)

    # The notch the scraper's collar wing hooks over. Only its first `front_wall` of
    # depth is real material; the rest overlaps the pocket so the two cuts interpenetrate
    # instead of meeting on a shared face.
    notch = Pos((pocket_back - item_depth) / 2, mid, -sill_depth / 2) * Box(
        item_depth - nest_back, clamp_len, sill_depth
    )

    body = back - (pocket - ramp) - notch
    if draft:
        return body

    # Cosmetic only. Nothing here is a loaded junction: the load runs from the sill
    # straight down through a monolithic block, so there is no concave weld to relieve
    # and no structural pass to exclude from the polish set.
    return polish(body, polish_edges(body, item_height), chamfer_size)
