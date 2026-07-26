"""Fit coupon: the hanging interface on its own, for dialing channel clearance."""

from nurb import *

from system import BLOCK_WIDTH, SIDE_CLEARANCE, channels, detent_dimples


@part
def fit_coupon(
    side_clearance=SIDE_CLEARANCE,
    bracket_count=1,
    item_height=30,
    item_depth=6,
    label_size=6,
    label_relief=0.5,
    draft=False,
):
    y0, y1 = -BLOCK_WIDTH / 2, (bracket_count - 0.5) * BLOCK_WIDTH
    slab = Pos(-item_depth / 2, (y0 + y1) / 2, -item_height / 2) * Box(
        item_depth, y1 - y0, item_height
    )
    body = (
        slab
        - channels(bracket_count, item_height, side_clearance=side_clearance)
        - detent_dimples(bracket_count)
    )
    if draft:
        return body

    # What it is, raised on the front face. A plate of these comes out looking
    # identical, and a coupon you cannot identify afterwards is no use. Raised rather
    # than cut: the web in front of the channel is only 1.8mm and debossing would take
    # a third of it.
    caption = f"{side_clearance:.2f}" if bracket_count == 1 else (
        f"{bracket_count}x {side_clearance:.2f}"
    )
    front = Plane(
        origin=(-item_depth, (y0 + y1) / 2, -item_height / 2),
        x_dir=(0, -1, 0),
        z_dir=(-1, 0, 0),
    )
    label = front * Text(caption, label_size)
    return body + extrude(label, label_relief)
