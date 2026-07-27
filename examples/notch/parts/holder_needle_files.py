"""Holder - Needle Files - 2x. Read holder_needle_files.md before changing anything."""

from math import ceil

from nurb import *

from system import (
    BLOCK_WIDTH,
    EPS,
    MIN_ITEM_DEPTH,
    OVERSHOOT,
    plate_width,
    polish as polish_pass,
    polish_edges,
    slab,
    span,
)

# The mouth of each throat flares out at 45 degrees over this much before it becomes
# the throat proper. A sketch dimension in the Fusion part rather than a parameter,
# and it is what lets a file neck find the slot without being aimed at it. It is not
# a lead-in chamfer laid on afterwards: it is drawn in the profile, which is where a
# shape problem on a thin web gets fixed.
MOUTH_FLARE = 0.5

# How far the ledge reaches back into the slab. It has to overlap solid material to
# fuse into one body, and it has to stop short of the channel floor at -4.2 or it
# fills the dovetail. One millimetre is what the Fusion part used, and it is what
# pins the projection at 20.5 given a 15.5mm ledge on a 6mm slab.
LEDGE_BURY = 1.0


def keyhole(front, seat_x, seat_width, throat_width):
    """One clip's plan-view cut: a round pocket reached through a flared slot.

    Drawn centered on y = 0 and moved into place. The pocket being wider than the
    throat is the entire retention mechanism, so the two are independent numbers and
    there are no bumps anywhere. The file's neck spreads the throat on the way in and
    the throat closes behind it.
    """
    # Counterclockwise, and that is load bearing: a `Polygon` faces whichever way its
    # winding says, and `extrude` follows the face normal. Wound the other way this
    # slot extrudes downward, lands under the part, cuts nothing, and leaves a plain
    # round hole that still builds and still measures 20.5 x 50.32 x 28.
    half, mouth = throat_width / 2, throat_width / 2 + MOUTH_FLARE
    slot = Polygon(
        (front - OVERSHOOT, -mouth),
        (front, -mouth),
        (front + MOUTH_FLARE, -half),
        (seat_x, -half),
        (seat_x, half),
        (front + MOUTH_FLARE, half),
        (front, mouth),
        (front - OVERSHOOT, mouth),
        align=None,
    )
    # The slot's back edge sits inside the circle, so the union is a real overlap and
    # the pocket-to-throat transition comes out as an arc rather than a tangency.
    return Pos(seat_x, 0) * Circle(seat_width / 2) + slot


@part
def holder_needle_files(
    bracket_count=2,
    item_height=28.0,
    item_depth=6.0,
    ledge_depth=15.5,
    ledge_height=6.0,
    clip_count=4,
    clip_pitch=14.0,
    seat_width=3.5,
    throat_width=2.9,
    pocket_inset=3.5,
    finger_thick=1.5,
    finger_root_inset=8.5,
    chamfer_size=1.0,
    structural_chamfer=3.0,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material behind the channel floor, so the "
            f"ledge would fill the dovetail rather than fuse to the slab. Raise it above "
            f"{MIN_ITEM_DEPTH}."
        )

    if throat_width >= seat_width:
        raise ValueError(
            f"a {throat_width}mm throat into a {seat_width}mm pocket has nothing to snap "
            f"past, so the clip does not retain. The pocket has to be the wider of the "
            f"two. Drop throat_width below {seat_width}, or raise seat_width."
        )

    relief_width = clip_pitch - seat_width - 2 * finger_thick
    if relief_width <= 0:
        raise ValueError(
            f"clip_pitch {clip_pitch} has no room left for an air gap once a {seat_width}mm "
            f"seat and two {finger_thick}mm fingers are in it. Raise clip_pitch above "
            f"{seat_width + 2 * finger_thick}, or narrow the fingers."
        )

    # The clip row is allowed to be wider than the plate: at the shipped numbers the
    # outermost handles overhang by about 2mm, which is air. What is not allowed is a
    # seat hanging off the edge, because then the clip is a notch in the end of the
    # ledge rather than a pair of fingers.
    half_plate = bracket_count * BLOCK_WIDTH / 2
    reach = (clip_count - 1) * clip_pitch / 2 + seat_width / 2 + finger_thick
    if reach > half_plate:
        need = ceil(2 * reach / BLOCK_WIDTH)
        fits = int(2 * (half_plate - seat_width / 2 - finger_thick) / clip_pitch) + 1
        raise ValueError(
            f"{clip_count} clips at {clip_pitch}mm pitch need a {2 * reach:.2f}mm plate and "
            f"bracket_count {bracket_count} gives {2 * half_plate:.2f}mm, so the outer seats "
            f"fall off the end. Raise bracket_count to {need}, or drop clip_count to {fits}."
        )

    back = slab(bracket_count, item_height, item_depth)

    # The ledge is a plain full-width bar along the bottom, and every clip in it is
    # cut out afterwards. Nothing here is built up finger by finger.
    ledge_back = -(item_depth - LEDGE_BURY)
    ledge_front = ledge_back - ledge_depth
    ledge_top = -item_height + ledge_height
    bar = Pos(
        (ledge_back + ledge_front) / 2, span(bracket_count), ledge_top - ledge_height / 2
    ) * Box(ledge_depth, plate_width(bracket_count), ledge_height)
    joined = back + bar

    # Structural, 3mm, at the one concave junction the load runs through: the weight
    # of four files sits on the ledge top and pries it off the slab face. `new_edges`
    # names that weld exactly, which no coordinate selector does once bracket_count
    # moves. The bottom faces of bar and slab are coplanar and merge, so the filter
    # keeps the edge at the ledge top and drops whatever the fuse left down there.
    weld = new_edges(back, bar, combined=joined).filter_by(Axis.Y).filter_by(
        lambda e: abs(e.center().Z - ledge_top) < EPS
    )
    body = chamfer(weld, structural_chamfer)

    # Everything forward hangs off the bracket run's midpoint, never off y = 0, so a
    # row of files stays balanced between the brackets. The reliefs interleave with
    # the seats, one more of them than there are clips, so every finger has air on
    # its outboard side.
    mid = span(bracket_count)
    seats = [mid + (k - (clip_count - 1) / 2) * clip_pitch for k in range(clip_count)]
    gaps = [mid + (k - clip_count / 2) * clip_pitch for k in range(clip_count + 1)]

    # The clips are cut vertically through the ledge, which is also the print's layer
    # plane, so a finger flexes across the layers rather than peeling them apart.
    floor = -item_height - OVERSHOOT
    depth = ledge_height + 2 * OVERSHOOT
    plan = keyhole(ledge_front, ledge_front + pocket_inset, seat_width, throat_width)
    clips = Part() + [Pos(0, y, floor) * extrude(plan, depth) for y in seats]

    gap = Pos(
        ledge_front + (finger_root_inset - OVERSHOOT) / 2, 0, floor + depth / 2
    ) * Box(finger_root_inset + OVERSHOOT, relief_width, depth)
    body = body - clips - (Part() + [Pos(0, y, 0) * gap for y in gaps])

    if draft:
        return body

    # Cosmetic, 1mm, on the slab's top face and nowhere else on the part.
    #
    # Nothing in the clip band can be polished at any size the doctrine allows. The two
    # ledge-top edges bounding one finger are `finger_thick` apart, each chamfers fine
    # alone, and together they need `2 * chamfer_size < finger_thick` exactly: at 1.5mm
    # fingers the pair builds at 0.749 and fails at 0.750. The smallest cosmetic chamfer
    # this library permits is 0.8, which wants 1.6mm of finger. The finger roots are left
    # sharp for a second reason anyway, since a relief there stiffens the hinge the clip
    # works by.
    #
    # The slab-front verticals are left out rather than vetoed. OCCT blends them even
    # though Fusion could not, and the only cost is two corner-triangle slivers, but the
    # print Josh signed off was built without them.
    polish = polish_edges(body, item_height).filter_by(
        lambda e: e.bounding_box().min.Z > -EPS
    )
    return polish_pass(body, polish, chamfer_size)
