"""Color on a part: regions that print in their own filament.

A multi-color printer puts a filament on a body, not on a face, so a color is a solid:
an inlay cut into the part, or a knob added to it. `add_color` keeps each region as its
own body the way `add_text` keeps letters, so the viewer shows it in its color and the
3MF hands it to its own filament. The part is still one solid, every region fused to
it: that is what prints, so it is what every check judges.
"""

import copy
import dataclasses
import re
from dataclasses import dataclass
from typing import Annotated

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
FilamentColor = Annotated[str, "nurb filament color"]

# The color a part's text prints in when it names none, as its own filament.
TEXT_COLOR = "#ffffff"


@dataclass
class Coloring:
    """What `add_color` leaves on the part it returns.

    `base` is the part with every region taken out, or None if nothing is left.
    `base_color` of None prints in the slicer's first filament. The base and the
    (color, solid) pairs in `regions` together are the part.
    """

    base: object | None
    base_color: str | None
    regions: list
    # The exact shape this describes, for the same reason `Lettering` keeps one: a part
    # changed after `add_color` is a new shape, and its old regions no longer fit it.
    owner: object = None
    location: object = None


def checked(color):
    """A color as "#rrggbb", or a refusal that says what a color looks like."""
    if not isinstance(color, str) or not HEX.fullmatch(color):
        raise ValueError(f'a color is written "#rrggbb", like "#e8704a", not {color!r}')
    return color.lower()


def add_color(part, color, region=None):
    """Give a part, or a region of it, its own color and its own filament.

    color: "#rrggbb". Declare `screen_color: FilamentColor = "#1a1a1a"` so the person
        picks it from a swatch in the panel.
    region: a solid. Where it overlaps the part it is cut out of the part and filled
        (an inlay, level with the face); where it stands outside it is added (a knob, a
        trim). Leave it out to set the color of the whole part, everything no region
        claims. A later region wins where two overlap.

    Call it after the polish pass and before `add_text`: anything done to its result
    rebuilds the shape and the regions lose their color.
    """
    from .text import lettering

    color = checked(color)
    if lettering(part) is not None:
        raise ValueError("add_color goes before add_text: the text is cut from the colored part, not the other way round")
    before = coloring(part)
    base = before.base if before else part
    base_color = before.base_color if before else None
    regions = list(before.regions) if before else []
    if region is None:
        whole = copy.copy(part)
        base_color = color
    else:
        whole = part + region
        base = _remaining(base, region)
        # A region a later one covers whole is gone, and must not cost a filament.
        regions = [(c, left) for c, r in regions if (left := _remaining(r, region)) is not None]
        regions.append((color, region))
    whole._nurb_color = Coloring(base, base_color, regions, owner=whole.wrapped, location=whole.location)
    return whole


def _remaining(body, cut):
    if body is None:
        return None
    left = body - cut
    return left if left.volume > 1e-6 else None


def coloring(shape):
    """The colors a part carries, or None once anything has changed the shape since."""
    found = getattr(shape, "_nurb_color", None)
    wrapped = getattr(shape, "wrapped", None)
    if found is None or wrapped is None or not wrapped.IsEqual(found.owner) or shape.location != found.location:
        return None
    return found


def carry(before, after, cut=None):
    """Put `before`'s colors on `after`, with `cut` taken out of every body.

    For `add_text`, which rebuilds the part: raised letters add to it and leave the
    colors as they were, while engraved and flush letters cut into whatever body they
    land on.
    """
    found = coloring(before)
    if found is None:
        return
    base, regions = found.base, found.regions
    if cut is not None:
        base = _remaining(base, cut)
        regions = [(c, left) for c, r in regions if (left := _remaining(r, cut)) is not None]
    after._nurb_color = dataclasses.replace(found, base=base, regions=regions, owner=after.wrapped, location=after.location)


def bodies(shape):
    """The part split by filament as [(color, solid)], the base first, or None for a
    part in one color. A color of None is the part's own; "text" is uncolored letters."""
    from .text import lettering

    lettered = lettering(shape)
    letters = lettered.letters if lettered is not None else None
    found = coloring(shape)
    if found is None and letters is None:
        return None
    if found is not None:
        out = [(found.base_color, found.base)] if found.base is not None else []
        out.extend(found.regions)
    else:
        out = [(None, lettered.base)] if lettered.base.volume > 1e-6 else []
    if letters is not None and letters.volume > 1e-6:
        out.append((lettered.color or "text", letters))
    return out or None


def moved(shape, location):
    """`location * shape`, with its text and colors moved along with it.

    For laying parts out on a plate, where the move is nurb's own and the regions
    should keep their color through it.
    """
    from .text import moved as text_moved

    out = text_moved(shape, location)
    found = coloring(shape)
    if found is not None:
        out._nurb_color = dataclasses.replace(
            found,
            base=location * found.base if found.base is not None else None,
            regions=[(c, location * r) for c, r in found.regions],
            owner=out.wrapped,
            location=out.location,
        )
    return out


def slots(colors):
    """Filament slots for a plate's colors: [slot 1's color, slot 2's, ...].

    Slot 1 is the part's own color. Every other distinct color gets the next slot, so
    two regions in one color share a filament.
    """
    out = []
    for color in colors:
        color = TEXT_COLOR if color == "text" else color
        if color not in out:
            out.append(color)
    if None in out:
        out.remove(None)
        out.insert(0, None)
    return out
