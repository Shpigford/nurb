from nurb import *


@part
def leg_cup():
    """Slip-over foot cup for the measured rectangular workbench leg.

    leg_width: measured side-to-side leg width, read from measurements.toml
    leg_depth: measured front-to-back leg depth, read from measurements.toml
    lift: floor thickness that raises the bench, read from measurements.toml
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    outer = Box(
        leg_width + 2.4,
        leg_depth + 2.4,
        lift + 8.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Box(
        leg_width + 0.4,
        leg_depth + 0.4,
        8.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, 0, lift))
    return outer - pocket
