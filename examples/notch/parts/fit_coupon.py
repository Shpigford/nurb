"""Fit coupon: the hanging interface on its own, for dialing channel clearance."""

from nurb import *

from system import (
    SIDE_CLEARANCE,
    channels,
    detent_dimples,
    plate_width,
    span,
)


@part
def fit_coupon(
    side_clearance=SIDE_CLEARANCE,
    bracket_count=1,
    item_height=30.0,
    item_depth=6.0,
    label_size=6.0,
    label_relief=0.5,
    draft=False,
):
    """A bare hanging plate for test-fitting the bracket channel.

    side_clearance: gap between each channel wall and the bracket, the fit being dialed
    bracket_count: how many brackets the coupon spans
    item_height: how tall the plate is
    item_depth: how thick the plate is, wall to front face
    label_size: text height of the raised caption naming the clearance
    label_relief: how far the caption stands off the front face
    """
    plate = Pos(-item_depth / 2, span(bracket_count), -item_height / 2) * Box(
        item_depth, plate_width(bracket_count), item_height
    )
    body = (
        plate
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
        origin=(-item_depth, span(bracket_count), -item_height / 2),
        x_dir=(0, -1, 0),
        z_dir=(-1, 0, 0),
    )
    label = front * Text(caption, label_size)
    return body + extrude(label, label_relief)
