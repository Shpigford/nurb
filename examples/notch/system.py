"""Notch: the constants and shared geometry every part in this library hangs on.

Notch parts mount on Wall Control pegboard brackets. Every part carries the same
dovetail channels in its back, so the channels live here and nowhere else. Sizing
belongs to the parts.

Datums. Land these three and the hanging interface is correct for free:

    slab top face at z = 0, the part extends down
    back face at x = 0, the part extends forward in -x
    first channel centered on y = 0, the rest march +y on BLOCK_WIDTH pitch
"""

from build123d import Box, Part, Polygon, Pos, extrude

# --- measured hardware -------------------------------------------------------

BLOCK_WIDTH = 25.16    # bracket pitch on-center, measured off a real wall
BRACKET_HEIGHT = 25.0  # physical bracket height, drives the minimum slab
PITCH_SLOP = 0.12      # per-interval scatter allowance across a run of brackets

POCKET_WIDTH = 20.56       # bracket plate width where it meets the part
POCKET_NECK_WIDTH = 12.16  # dovetail opening at the back face
POCKET_DEPTH = 4.0         # plate thickness

# --- fit ---------------------------------------------------------------------

TOP_MARGIN = 3.0  # solid material above the channel ceiling: this is the stop
MIN_ITEM_HEIGHT = BRACKET_HEIGHT + TOP_MARGIN  # 28mm for full engagement

CLEARANCE = 0.2        # slide fit, depth
SIDE_CLEARANCE = 0.25  # slide fit, width

# 0.25 is the middle of the window, not a preference. 0.20 printed too tight to seat
# and 0.30 slid on loosely, so the whole usable band is about 0.1mm wide -- the same
# order as FDM extrusion variation. Sitting in the middle is what leaves margin when a
# print drifts either way, and it is why chasing a finer number is not worth a plate:
# the printer moves further than the increment would.

# One clearance, every channel, every part. Printed runs of 2, 4 and 6 brackets all
# slid on at the same fit, so a real wall's pitch does not need compensating for and a
# longer run costs nothing. PITCH_SLOP above is what an allowance would have been built
# from; it stays in the table as measured hardware data, but nothing spends it.
#
# Getting here took three wrong versions, all of them variations on giving later
# channels more room: relief accumulating per channel, then relief capped, then a
# clearance that scaled with run length. The first printed looser at the far end of a
# 4x than anything the library ever shipped. All three solved a problem the wall does
# not have.

# The channel is the pocket plus clearance. Its walls come out at exactly 45
# degrees, which is what lets the dovetail print with no support:
# CHANNEL_NECK == CHANNEL_WIDTH - 2 * CHANNEL_DEPTH. Side clearance drops out of that
# identity, so widening it keeps the 45; depth clearance does not, so 0.2 is pinned.
CHANNEL_DEPTH = POCKET_DEPTH + CLEARANCE               # 4.2, the floor plane
CHANNEL_WIDTH = POCKET_WIDTH + 2 * SIDE_CLEARANCE      # 21.16 at channel 0's floor
CHANNEL_NECK = POCKET_NECK_WIDTH + 2 * SIDE_CLEARANCE  # 12.76 at channel 0's mouth

FLOOR_X = -CHANNEL_DEPTH  # -4.2, the coordinate every fit check is written against

# Where a forward feature stops when it reaches back into the slab. It has to
# overlap solid material to merge cleanly, and it has to stay clear of the channel
# floor or it fills the dovetail and the part will not go on the wall.
MERGE_X = FLOOR_X - 1.0

# A slab thinner than this has no material at MERGE_X at all, so a forward feature
# lands in front of it and never touches. That builds and exports without complaint,
# in two loose pieces, so parts check it.
MIN_ITEM_DEPTH = -MERGE_X

# Anti-lift detent. Gravity-drop dovetails resist pulling a part off the wall but
# nothing resists pulling it up, so the shared bracket plate carries a ramped nub
# and every channel floor carries this dimple. Slide down and it clicks in; pull
# up and the nub has to climb out.
DETENT_Z = -10.0
DETENT_WIDTH = 6.0
DETENT_HEIGHT = 5.0
DETENT_DEPTH = 0.8

OVERSHOOT = 1.0  # cuts run past the bottom face; coincident faces make brittle booleans
EPS = 1e-4       # slack for "is this coordinate on that plane"


def pitch(count, step=1):
    """Y centers of the channels, which is also where anything bracket-aligned goes."""
    return [k * step * BLOCK_WIDTH for k in range(count)]


def span(count, step=1):
    """Y midpoint of the bracket run. Loads hang balanced when they center here."""
    return (count - 1) * step * BLOCK_WIDTH / 2


def channels(count, height, step=1, side_clearance=SIDE_CLEARANCE):
    """The dovetail negative. Subtract it from a slab.

    `height` is the slab height, so the cut can run out through the bottom face.
    Fusion needed a fixed 16-lobe comb here because its combine tool lists never
    pick up new pattern instances. In code it is a loop.

    `side_clearance` is here so a part can be built at a fit other than the shipped
    one, which is what the calibration coupon does. Widening moves both walls equally,
    so they stay at 45 degrees whatever you pass.
    """
    width = POCKET_WIDTH + 2 * side_clearance
    neck = POCKET_NECK_WIDTH + 2 * side_clearance
    profile = Polygon(
        (0, neck / 2),
        (FLOOR_X, width / 2),
        (FLOOR_X, -width / 2),
        (0, -neck / 2),
        align=None,
    )
    one = Pos(0, 0, -TOP_MARGIN) * extrude(profile, -(height - TOP_MARGIN + OVERSHOOT))
    return Part() + [Pos(0, y, 0) * one for y in pitch(count, step)]


def polish_edges(shape, height):
    """Every edge the cosmetic pass is allowed to touch.

    Three standing vetoes, all of them Notch rather than taste: the back face sits
    flat against the wall, the bottom face is the first layer, and the channels are
    the fit. What is excluded is an edge *lying in* one of those, not one that
    merely ends there, so the vertical corners still get polished. Parts subtract
    their own exclusions (structural chamfers, sockets) from what comes back.

    The channel veto runs a detent deep, since the dimple is fit too. It is also
    where a 1mm chamfer fails outright: the dimple walls are 0.8mm.
    """
    interface = FLOOR_X - DETENT_DEPTH

    def allowed(edge):
        bb = edge.bounding_box()
        if bb.min.X > -EPS:  # in the back face
            return False
        if bb.max.Z < -height + EPS:  # in the bottom face
            return False
        if bb.min.X > interface - EPS and bb.max.Z < -TOP_MARGIN + EPS:  # in a channel
            return False
        return True

    return shape.edges().filter_by(allowed)


def detent_dimples(count, step=1):
    """The mating half of the anti-lift detent, one per channel floor.

    Separate from `channels` so a part that should lift off freely can leave it out.
    """
    one = Pos(FLOOR_X - DETENT_DEPTH / 2, 0, DETENT_Z) * Box(
        DETENT_DEPTH, DETENT_WIDTH, DETENT_HEIGHT
    )
    return Part() + [Pos(0, y, 0) * one for y in pitch(count, step)]
