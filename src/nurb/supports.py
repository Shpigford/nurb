"""`supported()`, and how a mark on one feature survives the booleans that follow it.

The doctrine's answer to an overhang is a corbel or a tilt, and both are better than
support material because both are free after printing. Some features refuse either: a
corbel would land where something else has to go, and a tilt that fixes one face breaks
a fit somewhere else. Those get marked, and the marking says which feature and why, so
the rest of the part keeps failing the overhang rule the way it should.

The hard part is that a part file is algebra. `body + shelf` builds a new solid and
anything set on `shelf` is gone, so a mark cannot ride on the geometry it marks. It
rides beside it instead: `supported()` records the shape it was handed into a
build-scoped list, and `builder` hangs the collected list on the finished part as
`_nurb_supported`, which is the same trick `@assembly` already plays with `_nurb_scene`.

A ContextVar rather than a module global because the server builds off the main thread
and two parts can be in flight at once; a global would let one part's marks land on the
other's geometry, which would be silent and would look like a rule misfiring.
"""

import contextlib
import contextvars
from dataclasses import dataclass, replace

# None means nothing is collecting, which is every call outside a build. `supported()`
# then does nothing but hand the shape back, so a part file is still importable and
# runnable on its own.
_MARKED = contextvars.ContextVar("nurb_supported", default=None)


@dataclass(frozen=True)
class Region:
    """Geometry that prints on support material, and the sentence that earns it."""

    shape: object
    why: str

    def box(self, slack=0.0):
        """The region's extent, grown by `slack` on every side.

        Computed here rather than stored because a whole-part transform can run after
        the mark (see `remap`), and a box is only true of the pose it was measured in.
        """
        box = self.shape.bounding_box()
        return (
            (box.min.X - slack, box.min.Y - slack, box.min.Z - slack),
            (box.max.X + slack, box.max.Y + slack, box.max.Z + slack),
        )


def supported(shape, why):
    """Mark geometry that prints on support material, and say why.

    Returns `shape` untouched, so it drops into an expression wherever the feature is
    built:

        arm = supported(Pos(20, 0, 30) * Box(24, 10, 3), "a corbel would block the switch")
        return body + arm

    Only overhang findings inside the marked region are excused, and they become notes
    rather than disappearing, because support material is a cost paid on every print
    rather than a fault that got fixed. A cantilever anywhere else in the part still
    fails, which is the whole reason to mark a feature instead of the part.

    `why` is required. The card's other allowances are numbers that mean nothing without
    the sentence beside them, and this one is a bare yes, so the sentence is the only
    thing carrying the reason at all.
    """
    if not hasattr(shape, "bounding_box"):
        raise TypeError(
            f"supported() marks geometry, got {type(shape).__name__}. Wrap the shape "
            "the feature is built from."
        )
    if not str(why).strip():
        raise ValueError(
            "supported() needs a reason: what stops a corbel or a tilt from carrying "
            "this feature. It is what the card and the checker quote back."
        )
    marked = _MARKED.get()
    if marked is not None:
        marked.append(Region(shape, str(why).strip()))
    return shape


@contextlib.contextmanager
def collecting():
    """Collect the marks a part makes while it builds. Used by `builder.build`."""
    token = _MARKED.set([])
    try:
        yield _MARKED.get()
    finally:
        _MARKED.reset(token)


def remap(move):
    """Move every mark recorded so far, for an operation that moves the whole part.

    `stand()` is the one that does this: it rotates and seats the finished part, so
    marks made while modelling upright would otherwise describe where the feature used
    to be. Anything else that repositions a whole part has the same duty, and forgetting
    it does not raise. It fails toward noise rather than silence, though: the marks stop
    matching, the real findings come back, and the unused-mark note names the mark that
    went stale, which is the pair that points at this function.
    """
    marked = _MARKED.get()
    if not marked:
        return
    marked[:] = [replace(region, shape=move(region.shape)) for region in marked]


def regions(shape):
    """The marks a built shape carries. Empty for anything built without them."""
    return getattr(shape, "_nurb_supported", ()) or ()


def covering(regions, point, slack=0.0):
    """The first region whose grown box contains `point`, or None.

    Boxes rather than solid containment because the point being tested is the centre of
    a downward face, which lies exactly on the marked shape's own boundary, where an
    inside test is a coin flip. `slack` absorbs the polish pass, which moves faces near
    a mark's edges by about a chamfer.
    """
    for region in regions:
        low, high = region.box(slack)
        if all(low[i] - 1e-6 <= point[i] <= high[i] + 1e-6 for i in range(3)):
            return region
    return None
