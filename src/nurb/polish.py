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

import collections.abc
import functools

from build123d import chamfer as _chamfer

# What OCCT says when a chamfer will not land. The same strings `nurb verify`
# matches on, because both are asking the same question: did the kernel refuse, or did
# the part refuse in its own words.
KERNEL = ("Failed creating a chamfer", "BRep_API")


def _advice(count, size, word):
    """What the doctrine knows about this failure, said at the moment it happens.

    The kernel's own message is "try a smaller length value(s)", and the doctrine is
    explicit that following it would never have found the real rule: a chamfer fails
    for room, not for length. Shrinking it is the one response that makes a part quietly
    worse, because a 0.4mm chamfer lands and then reads as a defect on the print.

    So the rule goes here rather than only in `nurb rules`. This is the most common way
    a part stops building, and an error is the one place a reader is guaranteed to be
    looking.
    """
    lines = [
        "",
        f"  A {word} fails for room, not for length, and shrinking it is usually the",
        f"  wrong fix. Two {word}ed convex edges need more than {2 * size:g}mm of face between",
        f"  them, and a single one needs more than {size:g}mm.",
    ]
    if count > 1:
        lines += [
            "",
            f"  This call passed {count} edges as one batch, and a batch is all or nothing:",
            "  one edge that cannot land takes the whole call down. Every edge in it very",
            "  likely chamfers fine on its own, so testing them one at a time will report",
            "  that nothing is wrong.",
            "",
            # `!r` not `:g`: a size is a measurement, and this codebase reads a bare `1`
            # as a count. Suggested code has to echo back the float the caller passed.
            f"  polish(shape, edges, {size!r}) bisects the set for you and keeps the halves that",
            "  build, which is what the doctrine prescribes instead of narrowing by hand.",
        ]
    else:
        lines += [
            "",
            "  A single edge that fails at every length is the other case: its end lands on",
            "  a vertex with four faces and only three edges between them, and OCCT has no",
            "  cap for that corner. Chamfer in two passes and reselect from the result.",
        ]
    lines += ["", "  `nurb rules` has both cases in full."]
    return "\n".join(lines)


def _count(objects):
    try:
        return len(list(objects))
    except TypeError:  # a single Edge or Vertex, which is not iterable
        return 1


def _guarded(fn, word, objects, size, *args, **kwargs):
    # A generator would be exhausted by the failing call, so the count in the message
    # would read zero and the advice would describe the wrong case. Lists, ShapeLists
    # and a single Edge are all left alone.
    if isinstance(objects, collections.abc.Iterator):
        objects = list(objects)
    try:
        return fn(objects, size, *args, **kwargs)
    except Exception as exc:
        if not any(k in str(exc) for k in KERNEL):
            raise
        # Same type and same opening line, so `nurb verify`'s kernel matching and any
        # caller catching ValueError still work. `from None` because the original adds
        # nothing a reader wants: it is the same sentence again under a C++ frame.
        raise type(exc)(f"{exc}\n{_advice(_count(objects), size, word)}") from None


@functools.wraps(_chamfer)
def chamfer(objects, length, *args, **kwargs):
    """build123d's `chamfer`, with the doctrine's guidance on failure."""
    return _guarded(_chamfer, "chamfer", objects, length, *args, **kwargs)


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
            # The raw kernel call, not the guarded one: bisecting expects failures and
            # discards them, so building the guidance text here would be advice nobody
            # reads, once per attempt.
            out = _chamfer(candidate, size)
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
