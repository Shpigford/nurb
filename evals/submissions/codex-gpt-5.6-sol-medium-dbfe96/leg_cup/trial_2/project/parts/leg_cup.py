from nurb import *
from pathlib import Path
import tomllib


def _measurement(name):
    with (Path(__file__).parent.parent / "measurements.toml").open("rb") as source:
        return tomllib.load(source)[name]["value"]


@part
def leg_cup():
    """Slip-over cup that lifts the short workbench leg level."""
    leg_width = _measurement("leg_width")
    leg_depth = _measurement("leg_depth")
    lift = _measurement("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0
    pocket_width = leg_width + clearance
    pocket_length = leg_depth + clearance

    body = Box(
        pocket_width + 2.0 * wall,
        pocket_length + 2.0 * wall,
        lift + pocket_depth,
    )
    pocket = Box(pocket_width, pocket_length, pocket_depth).translate(
        (0, 0, lift / 2.0)
    )
    return body - pocket
