from nurb import *


@part
def pole_rest(pole_diameter=20.0, cradle_clearance=0.2, cradle_wall=1.6):
    """A low, continuous saddle for a freshly finished pole.

    pole_diameter: measured diameter of the pole the rest cradles
    cradle_clearance: radial air gap protecting the soft finish
    cradle_wall: material behind the seating surface
    """
    if pole_diameter <= 0:
        reject("pole diameter must be positive", "pole_diameter")
    if cradle_clearance < 0.1:
        reject("clearance must be at least 0.1 mm", "cradle_clearance")
    if cradle_wall < 1.2:
        reject("cradle wall must be at least 1.2 mm", "cradle_wall")

    # The pole axis is deliberately fixed at z=18.  The annular lower half
    # supplies a 180 degree, 1.6 mm-thick bearing arc; its open top lets the
    # pole descend vertically into the seat.
    axis_height = 18.0
    pole_radius = pole_diameter / 2
    inner_radius = pole_radius + cradle_clearance
    outer_radius = inner_radius + cradle_wall
    length = 26.0

    base = Box(2 * outer_radius + 2.0, length, 4.0).moved(Location((0, 0, 2.0)))
    spine_height = axis_height - inner_radius - 0.1
    spine = Box(8.0, length - 0.2, spine_height).moved(
        Location((0, 0, spine_height / 2))
    )
    lower_half = Box(2 * outer_radius + 2.0, length, axis_height).moved(
        Location((0, 0, axis_height / 2))
    )

    def saddle_band(y):
        """A short self-bridging section of the annular saddle."""
        band_length = 1.0
        outer = Cylinder(
            outer_radius,
            band_length,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            rotation=(90, 0, 0),
        ).moved(Location((0, y, axis_height)))
        clip = Box(2 * outer_radius + 2.0, band_length, axis_height).moved(
            Location((0, y, axis_height / 2))
        )
        return outer & clip

    # Nineteen one-millimetre bridges cover 73% of the rest's length. Their
    # small gaps make the steepest part of the circular seat self-bridging.
    seat = saddle_band(-12.4)
    for index in range(1, 19):
        seat = seat + saddle_band(-12.4 + index * 1.36)

    # Keep the complete pole envelope clear, including in the bridge gaps.
    full_clearance = Cylinder(
        inner_radius,
        length + 0.4,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        rotation=(90, 0, 0),
    ).moved(Location((0, 0, axis_height)))
    return (base + spine + seat) - full_clearance
