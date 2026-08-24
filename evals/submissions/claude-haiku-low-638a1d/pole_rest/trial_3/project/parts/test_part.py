from nurb import *


@part
def test_part(width=40.0, depth=30.0, height=20.0, wall=2.0, draft=False):
    body = Box(width, depth, height)
    if draft:
        return body
    # Name what must stay sharp, then let `polish` chamfer whatever the kernel takes.
    # A bare `chamfer(...)` is all or nothing: one edge that cannot land loses the lot.
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    return polish(body, keep, 1.0)
