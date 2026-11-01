"""Build one plate carrying every fit variant worth trying, instead of iterating.

    uv run --project ../.. python calibrate.py

Edit SWEEP and SPANS, re-run, reprint. Each coupon carries its own settings raised on
its face, so the plate is still readable once it is a pile of parts on the bench.

Two different questions, which is why there are two groups:

  SWEEP  one bracket, varying clearance. A judgement about feel. Empty by default:
         0.30 is settled, and steps finer than about 0.1 are below what an FDM
         printer resolves anyway, so a fine sweep measures extrusion noise rather
         than fit. Put values back here only if the base number is in question again.
  SPANS  a full-length run at one clearance. Pass or fail, not a feel: either the
         part slides onto real brackets or it binds. The answer you want is the
         longest run that still goes on at the tightest clearance.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from build123d import Pos, Part, export_stl  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "src"))
from nurb import builder  # noqa: E402

from system import BLOCK_WIDTH  # noqa: E402

SWEEP = [0.25]
SPANS = [(2, 0.25), (3, 0.25), (4, 0.25), (5, 0.25), (6, 0.25)]

BED = 250.0  # usable width, minus a margin
GAP = 6.0
ROW_PITCH = 40.0  # coupons are 30mm tall, and height is what separates rows

HERE = pathlib.Path(__file__).parent
COUPON = HERE / "parts" / "fit_coupon.py"


def rows(items):
    """Pack widest-first into rows that fit the bed."""
    row, used = [], 0.0
    for width, shape in sorted(items, key=lambda i: -i[0]):
        if row and used + width + GAP > BED:
            yield row
            row, used = [], 0.0
        row.append((width, shape))
        used += width + GAP
    if row:
        yield row


def main():
    built = []
    for count, clearance in [(1, c) for c in SWEEP] + SPANS:
        shape, _, ms = builder.build(
            COUPON, overrides={"bracket_count": count, "side_clearance": clearance}
        )
        width = count * BLOCK_WIDTH
        built.append((width, shape))
        print(f"  {count}x  {clearance:.2f}   {width:6.1f}mm wide   {ms:5.0f}ms")

    plate = Part()
    for r, row in enumerate(rows(built)):
        y = 0.0
        for width, shape in row:
            plate += Pos(0, y, -r * ROW_PITCH) * shape
            y += width + GAP

    out = HERE / "build"
    out.mkdir(exist_ok=True)
    target = out / "calibration_plate.stl"
    export_stl(plate, str(target))
    bb = plate.bounding_box()
    print(
        f"\n  {target.name}: {len(built)} coupons, "
        f"{bb.size.Y:.0f} x {bb.size.Z:.0f}mm footprint, {plate.volume / 1000:.1f}cm3"
    )
    print("  Slice it the way you slice a part, so the fits are comparable.")


if __name__ == "__main__":
    main()
