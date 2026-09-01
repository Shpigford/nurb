"""nurb -- agentic CAD for 3D printing.

A part file needs one import:

    from nurb import *

    @part
    def dispenser(width=80, height=120, wall=2):
        return Box(width, height, wall)
"""

import importlib.metadata as _metadata

import build123d as _b3d
from build123d import *  # noqa: F401,F403  -- geometry vocabulary

from .assembly import assembly, hinge, obstacle, use  # noqa: E402
from .checks import concave_edges, is_convex  # noqa: E402
from .crown import crown  # noqa: E402
from .holes import counterbore  # noqa: E402
from .measurements import measured  # noqa: E402
from .mesh import import_stl  # noqa: E402  -- must win, see below
from .orient import stand  # noqa: E402
from .polish import chamfer, polish  # noqa: E402  -- must win, see below
from .registry import part, reject  # noqa: E402  -- must win over any build123d name
from .supports import supported  # noqa: E402

# `polish` is here because the doctrine prescribes the algorithm and every project
# would otherwise write it: chamfer is all or nothing, so one edge that cannot land
# takes the pass down and the set gets narrowed by hand until it builds.
# `from nurb import *` hands a part file the whole build123d vocabulary, @part, the
# convexity test, and `measured`. The convexity test is here because a polish pass cannot
# be written without it: chamfering an inside corner is the one polish mistake that looks
# fine in code. `measured` is here because the alternative to asking for a dimension is
# inventing one, and an invented one builds, checks clean and prints.
# `stand` is here because a diagonal print variant cannot be written without it: the
# rotation is trivial, but the bed facet it cuts is a doctrine rule (2mm of flat, or the
# first layer is one extrusion line wide and peels), and a part file left to tilt by
# hand ships the knife edge.
# `crown` is here because rounding a variable-height rim by hand is an eight-step sweep
# construction (issue #55), and every direct fillet of such a rim dies in OCCT's corner
# capping. It is the doctrine's one sanctioned round-edge treatment.
# `counterbore` is here because the naive alternative is two cylinders that build,
# check as an ordinary bridge, and print a screw seat on sagging air: the stepped
# bridging stack is fixed print-farm practice, not a judgement, so it is generated.
# `supported` is here because the alternative to marking one feature is declaring the
# whole part on supports, which excuses next month's mistake as readily as this month's
# decision. Scoping it needs the mark to survive the booleans that follow, and a part
# file cannot arrange that for itself: the tag has to be collected by the builder.
# `reject` is here because a part that knows a configuration cannot work (a hole
# narrower than the tool it holds) has to be able to say so, and the alternative is a
# bare ValueError that the viewer can only present as a crash. A refusal through
# `reject` keeps its message and the parameter it names, and is shown as a limit of
# the design.
# `chamfer` deliberately shadows build123d's. Same behaviour, same exception type;
# what it adds is the doctrine's rule on the way out of a failure, because the kernel's
# own advice is "try a smaller length value(s)" and following it is how a part ends up
# with a 0.4mm chamfer that lands and prints as a defect. It is the most common way a
# part stops building, so it is the one message worth owning. `fillet` is deliberately
# not wrapped: build123d's fillet error already names `max_fillet()` and a smaller
# radius really is the fix there, so the chamfer rule would be wrong half the time.
# `import_stl` shadows build123d's for a blunter reason: build123d's returns a `Face`,
# a sheet of triangles with no inside, and subtracting from one segfaults instead of
# raising. A part builds inside the `nurb dev` process, so the whole watcher dies
# without printing anything. It is also the first name a model tries when a downloaded
# file lands in a project. This one returns a real solid for the flat-faced meshes that
# survive the trip, and refuses the rest pointing at `nurb scan`.
__all__ = [
    *getattr(_b3d, "__all__", [n for n in dir(_b3d) if not n.startswith("_")]),
    "part",
    "reject",
    "is_convex",
    "concave_edges",
    "measured",
    "polish",
    "crown",
    "stand",
    "counterbore",
    "supported",
    "assembly",
    "use",
    "hinge",
    "obstacle",
]
# The version lives in pyproject.toml and nowhere else; a second copy here would drift.
try:
    __version__ = _metadata.version("nurb")
except _metadata.PackageNotFoundError:  # a source tree on PYTHONPATH, never installed
    __version__ = "0.0.0"
