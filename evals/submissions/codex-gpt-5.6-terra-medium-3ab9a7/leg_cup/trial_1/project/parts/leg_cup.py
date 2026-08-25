from nurb import *
from pathlib import Path
import tomllib


_measurements = tomllib.loads(
    (Path(__file__).parent.parent / "measurements.toml").read_text()
)


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for a rectangular workbench leg.

    The leg pocket includes 0.2 mm clearance per side.  Its solid floor uses the
    provisional `lift` measurement, so changing measurements.toml changes the
    amount of leveling without editing this model.
    """
    leg_width = _measurements["leg_width"]["value"]
    leg_depth = _measurements["leg_depth"]["value"]
    lift = _measurements["lift"]["value"]

    wall = 2.0
    clearance = 0.4
    pocket_depth = 8.0
    pocket_width = leg_width + clearance
    pocket_depth_y = leg_depth + clearance

    outer = Box(pocket_width + 2 * wall, pocket_depth_y + 2 * wall, lift + pocket_depth)
    # Boxes are centered on their origins: center the pocket in X/Y and raise
    # its center by half the floor thickness so its bottom is exactly `lift`
    # above the exterior bottom.
    pocket = Box(pocket_width, pocket_depth_y, pocket_depth).translate((0, 0, lift / 2))
    return outer.cut(pocket)
