"""Slip-over levelling cup for the workbench's short rectangular leg."""

import tomllib
from pathlib import Path

from nurb import *


def _measured(name):
    """Read a millimetre value from this project's measurement record."""
    with (Path(__file__).parent.parent / "measurements.toml").open("rb") as source:
        return tomllib.load(source)[name]["value"]


@part
def leg_cup():
    """
    A support-free, open-top cup that raises one workbench leg.

    The fit and lift are intentionally read from measurements.toml so the
    manufacturing geometry follows a later shop measurement without editing this
    model.
    """
    leg_width = _measured("leg_width")
    leg_depth = _measured("leg_depth")
    lift = _measured("lift")

    wall_thickness = 2.0
    pocket_clearance = 0.4
    pocket_depth = 8.0

    pocket_width = leg_width + pocket_clearance
    pocket_depth_size = leg_depth + pocket_clearance
    outer_width = pocket_width + 2 * wall_thickness
    outer_depth = pocket_depth_size + 2 * wall_thickness

    outer = Box(outer_width, outer_depth, lift + pocket_depth)
    pocket = Box(pocket_width, pocket_depth_size, pocket_depth).translate(
        # Boxes are centred at the origin.  This puts the cutter equally inside
        # each side wall and makes its bottom sit exactly on the lift floor.
        (0, 0, lift / 2)
    )
    return outer - pocket
