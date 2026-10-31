"""Both cases, explicitly.

The naive version of this test classifies concave edges as convex, so agreeing with
a box proves nothing on its own. Every shape here has a hand-counted answer.
"""

from build123d import Box, Pos

from nurb.checks import concave_edges, edge_faces, is_convex


def test_box_has_no_concave_edges():
    box = Box(10, 10, 10)
    assert len(box.edges()) == 12
    assert concave_edges(box) == []


def test_notched_box_has_exactly_one_concave_edge():
    """An L in section: the inner corner is concave, the other 11 are not."""
    shape = Box(10, 10, 10) - Pos(3, 0, 3) * Box(4, 20, 4)
    concave = concave_edges(shape)
    assert len(concave) == 1, [e.center() for e in concave]
    assert concave[0].length == 10  # runs the full width of the notch


def test_slot_has_two_concave_edges():
    """A blind slot in the top face: two inner corners along its length."""
    shape = Box(20, 20, 10) - Pos(0, 0, 4) * Box(6, 30, 4)
    concave = concave_edges(shape)
    assert len(concave) == 2, [e.center() for e in concave]
    assert all(round(e.length, 6) == 20 for e in concave)


def test_every_edge_is_classified_one_way_or_the_other():
    shape = Box(10, 10, 10) - Pos(3, 0, 3) * Box(4, 20, 4)
    shared = {e: f for e, f in edge_faces(shape).items() if len(f) == 2}
    verdicts = [is_convex(e, *f) for e, f in shared.items()]
    assert len(verdicts) == len(shared)
    assert verdicts.count(False) == 1
