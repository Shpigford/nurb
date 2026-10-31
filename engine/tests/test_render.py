"""`nurb render` is how an agent sees its own work, so a blank PNG is a silent failure.

The trap this guards is specific. Every piece can look healthy while the image is
useless: the part builds, the rasterizer returns bytes, the file writes, and nothing was
actually drawn, or the camera never moved to the view that was asked for. Both come out
as a file with the right name and a plausible size.

So the assertion is that two views of one part are two different pictures. Nothing about
that passes if the frame is empty or the view parameter is ignored.
"""

import pathlib
import struct

import numpy
import pytest

from nurb import raster
from nurb import render as renderer
from nurb.builder import BuildError

REAL = pathlib.Path(__file__).parents[1] / "examples" / "notch"
PART = REAL / "parts" / "fit_coupon.py"  # the smallest of the three
SIZE = (400, 300)
# An empty frame of the same size, encoded the same way. Flat shading compresses hard
# (the top view of a flat coupon is one silhouette in one colour), so the bar for
# "something was drawn" is measured against nothing rather than fixed at a byte count.
BLANK = len(raster.encode_png(numpy.zeros((SIZE[1], SIZE[0], 4), "uint8")))


def shoot(tmp_path, view):
    ((_, png),) = renderer.render(REAL, [PART], tmp_path / view, view=view, size=SIZE)
    return png.read_bytes()


def test_an_unknown_view_says_which_ones_exist():
    """Checked before the first build, so a typo costs no geometry."""
    with pytest.raises(BuildError, match="iso"):
        renderer.render(REAL, [PART], "unused", view="sideways")


def test_two_views_of_a_part_are_two_different_pictures(tmp_path):
    iso, top = shoot(tmp_path, "iso"), shoot(tmp_path, "top")
    for name, png in (("iso", iso), ("top", top)):
        assert png[:4] == b"\x89PNG", f"{name} is not a PNG"
        assert struct.unpack(">II", png[16:24]) == SIZE, f"{name} is the wrong size"
        assert len(png) > BLANK * 2, f"{name} is blank, so nothing was drawn"
    assert iso != top, "the view parameter did nothing"


def test_an_unknown_cut_names_the_grammar():
    """Also before the first build, and the message shows a working example."""
    with pytest.raises(BuildError, match="z:4mm"):
        renderer.render(REAL, [PART], "unused", cut="sideways")


def test_a_cut_and_a_computed_view_each_change_the_picture(tmp_path):
    """One build for all three stills, which is the point of snapshots: the section
    must remove pixels the whole part had, and a bare `x,y,z` view must move the camera
    off the iso the first still used."""
    whole, cut, vec = renderer.snapshots(
        REAL,
        [
            {"part": PART, "file": tmp_path / "whole.png", "size": SIZE},
            {"part": PART, "file": tmp_path / "cut.png", "size": SIZE, "cut": "z"},
            {"part": PART, "file": tmp_path / "vec.png", "size": SIZE, "view": "0.2,0.9,0.3"},
        ],
    )
    pngs = {p.name: p.read_bytes() for p in (whole, cut, vec)}
    for name, png in pngs.items():
        assert png[:4] == b"\x89PNG", f"{name} is not a PNG"
        assert len(png) > BLANK * 2, f"{name} is blank, so nothing was drawn"
    assert pngs["whole.png"] != pngs["cut.png"], "the cut removed nothing"
    assert pngs["whole.png"] != pngs["vec.png"], "the view vector did not move the camera"
def test_a_view_that_is_not_a_number_is_refused_before_any_build():
    for bad in ("nan,0,0", "inf,0,0"):
        with pytest.raises(BuildError, match="no view called"):
            renderer._view(bad)


def test_a_named_view_and_a_cut_each_get_their_own_file(tmp_path):
    """`--view top` after a plain render must not overwrite the iso picture."""
    files = []
    for view, cut in (("iso", None), ("top", None), ("1,0,0", None), ("top", "z")):
        ((_, png),) = renderer.render(REAL, [PART], tmp_path, view=view, size=SIZE, cut=cut)
        files.append(png.name)
    stem = PART.stem
    assert files == [f"{stem}.png", f"{stem}.top.png", f"{stem}.view.png", f"{stem}.top.section.png"]
    assert len(set(tmp_path.glob("*.png"))) == 4
