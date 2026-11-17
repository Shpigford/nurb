"""A keychain tag with a name on it."""

from nurb import *


@part
def name_tag(
    text="Biscuit",
    style: Literal["raised", "engraved", "flush"] = "raised",
    font: Literal["Standard", "Heavy", "Stencil"] = "Standard",
    length=60.0,
    width=20.0,
    thickness=3.0,
    ring_hole=5.0,
    letter_depth=0.6,
):
    """A flat tag with a hole for the key ring and a name across the rest.

    text: the name on the tag
    style: raised letters stand up, engraved ones are cut in, flush ones are filled level in a second colour
    font: the lettering
    length: tag length, ring end included
    width: tag width
    thickness: plate thickness
    ring_hole: diameter of the key ring hole
    letter_depth: how far the letters stand up or sink in
    """
    if letter_depth >= thickness:
        reject(f"letter_depth {letter_depth} cuts through a {thickness}mm tag: keep it under {thickness}", param="letter_depth")
    corner = width / 4
    tag = extrude(RectangleRounded(length, width, corner), thickness)
    ring = Pos(-length / 2 + width / 2, 0) * Cylinder(ring_hole / 2, thickness * 3)
    tag = tag - ring

    # Write between the ring hole and where the far end starts to round off, so the
    # letters crowd neither.
    start = -length / 2 + width / 2 + ring_hole / 2
    end = length / 2 - corner
    area = Plane.XY.offset(thickness) * Pos((start + end) / 2, 0) * Rectangle(end - start, width)
    return add_text(tag, text, area.face(), style=style, font=font, depth=letter_depth)
