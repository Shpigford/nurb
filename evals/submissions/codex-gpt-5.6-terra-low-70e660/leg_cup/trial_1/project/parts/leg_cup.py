"""Slip-over levelling cup for a rectangular workbench leg."""

from pathlib import Path
import tomllib

from nurb import *
from build123d import Box


def _measurement(name: str) -> float:
    """Read a millimetre value from this project's measurements file."""
    data = tomllib.loads((Path(__file__).parent.parent / "measurements.toml").read_text())
    return float(data[name]["value"])


@part
def leg_cup():
    """A support-free, open-top foot cup.

    The leg clearance, wall thickness, pocket depth, and floor lift are fixed by
    the documented requirements; only the three measurements file values drive
    the resulting size.
    """
    leg_width = _measurement("leg_width")
    leg_depth = _measurement("leg_depth")
    lift = _measurement("lift")

    clearance = 0.4
    wall_thickness = 2.0
    pocket_depth = 8.0
    inner_width = leg_width + clearance
    inner_depth = leg_depth + clearance
    outer_width = inner_width + 2 * wall_thickness
    outer_depth = inner_depth + 2 * wall_thickness

    outer = Box(outer_width, outer_depth, lift + pocket_depth)
    pocket = Box(inner_width, inner_depth, pocket_depth)
    # build123d centers solids on the origin.  The cup floor starts at the
    # outer solid's lower face, so the pocket's centre is lift / 2 above it.
    pocket = pocket.moved(Location((0, 0, lift / 2)))
    return outer - pocket
