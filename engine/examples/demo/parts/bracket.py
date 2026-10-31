from nurb import *


@part
def bracket(width=40, depth=30, height=20, wall=2, draft=False):
    body = Box(width, depth, height)
    if not draft:
        body = chamfer(body.edges().filter_by(Axis.Z), length=1)
    return body
