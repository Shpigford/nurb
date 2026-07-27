"""The polish pass: chamfer as much of a set as the kernel will take.

`chamfer` is all or nothing. One edge that cannot land takes the whole call down, and
the natural response is to shrink the set by hand until it builds. That is how a part
with ninety exposed edges ends up with three chamfered ones, and it is why the same
doctrine produces far more chamfers in a GUI, where a human adds them one feature at a
time and works around each collision individually.

The doctrine describes this algorithm and used to leave every project to write it. It
was 35 lines in one `system.py`, which meant the next project would write it again or,
far more likely, skip it and hand-narrow the set, which is exactly what the rule exists
to prevent.
"""

from build123d import chamfer


def polish(shape, edges, size):
    """Chamfer as much of `edges` as will land, and stop there.

    Try the set; where it fails, bisect and keep the halves that build.

    **A batch is refused if it makes a face smaller than a corner triangle.** Three
    chamfers meeting at a convex corner leave about `0.866 * size ** 2`, which the
    doctrine allows outright; anything smaller is chamfers colliding, and that is what
    "keep chamfering until it stops working" would otherwise walk straight into.
    Counted as a delta, so geometry that was already small before the pass does not
    veto every candidate.

    Edges are taken longest first with ties broken on position, so the result does not
    depend on the order they arrived in.

    Every attempt chamfers the original solid with the whole accepted set at once, never
    the result of the last attempt. An edge belongs to the shape it was selected from
    and `chamfer` reads its target off that shape, so applying batches in sequence would
    quietly keep re-chamfering the first body and hand it back.

    This does not choose what to polish. Deciding which edges are exposed, which are
    mating geometry and which are concave is the part's judgement and stays in the part.
    """
    floor = 0.8 * size**2

    def tiny(solid):
        return len([f for f in solid.faces() if f.area < floor])

    allowance = tiny(shape)
    kept, best = [], shape

    def lands(candidate):
        try:
            out = chamfer(candidate, size)
        except Exception:
            return None
        return out if tiny(out) <= allowance else None

    def take(batch):
        nonlocal kept, best
        out = lands(kept + batch)
        if out is not None:
            kept, best = kept + batch, out
            return
        if len(batch) == 1:
            return  # this one cannot land beside what is already there
        half = len(batch) // 2
        take(batch[:half])
        take(batch[half:])

    take(sorted(edges, key=lambda e: (-e.length, e.center().X, e.center().Y, e.center().Z)))
    return best
