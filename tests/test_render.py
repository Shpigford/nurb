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
from types import SimpleNamespace

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


def test_an_unknown_cut_names_the_grammar():
    """Also before the optional import, and the message shows a working example."""
    with pytest.raises(BuildError, match="z:0.7"):
        renderer.render(REAL, [PART], "unused", cut="sideways")


def test_a_browser_launch_failure_is_a_build_error():
    """Callers can write a text-only report when Playwright has no browser installed."""

    def refuse():
        raise RuntimeError("browser executable is missing")

    pw = SimpleNamespace(chromium=SimpleNamespace(launch=refuse))
    with pytest.raises(BuildError, match="could not launch Chromium"):
        renderer._launch(pw)


def test_a_cut_and_a_computed_view_each_change_the_picture(tmp_path):
    """One browser for all three stills, which is the whole point of snapshots: the
    section must remove pixels the whole part had, and a bare `x,y,z` view must move
    the camera off the iso the first still used."""
    pytest.importorskip("playwright", reason="nurb render is an optional extra")
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
        assert len(png) > FLAT * 2, f"{name} is blank, so nothing was drawn"
    assert pngs["whole.png"] != pngs["cut.png"], "the cut removed nothing"
    assert pngs["whole.png"] != pngs["vec.png"], "the view vector did not move the camera"
