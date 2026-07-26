"""`nurb render` is how an agent sees its own work, so a blank PNG is a silent failure.

The trap this guards is specific. Every piece can look healthy while the image is
useless: the server serves, the page loads, the screenshot writes, and WebGL quietly did
not draw, or the camera never moved to the view that was asked for. Both come out as a
file with the right name and a plausible size.

So the assertion is that two views of one part are two different pictures. Nothing about
that passes if the canvas is blank or the view parameter is ignored.
"""

import pathlib
import struct

import pytest

from nurb import render as renderer
from nurb.builder import BuildError

REAL = pathlib.Path(__file__).parents[1] / "examples" / "notch"
PART = REAL / "parts" / "fit_coupon.py"  # the smallest of the three
SIZE = (400, 300)
FLAT = 816  # a uniform 400x300 PNG, measured, so anything actually drawn clears it


def shoot(tmp_path, view):
    ((_, png),) = renderer.render(REAL, [PART], tmp_path / view, view=view, size=SIZE)
    return png.read_bytes()


def test_an_unknown_view_says_which_ones_exist():
    """Checked before the optional import, so a typo does not read as a missing package."""
    with pytest.raises(BuildError, match="iso"):
        renderer.render(REAL, [PART], "unused", view="sideways")


def test_two_views_of_a_part_are_two_different_pictures(tmp_path):
    pytest.importorskip("playwright", reason="nurb render is an optional extra")
    iso, top = shoot(tmp_path, "iso"), shoot(tmp_path, "top")
    for name, png in (("iso", iso), ("top", top)):
        assert png[:4] == b"\x89PNG", f"{name} is not a PNG"
        assert struct.unpack(">II", png[16:24]) == SIZE, f"{name} is the wrong size"
        assert len(png) > FLAT * 2, f"{name} is blank, so nothing was drawn"
    assert iso != top, "the view parameter did nothing"
