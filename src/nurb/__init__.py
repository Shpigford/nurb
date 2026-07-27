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

from .checks import concave_edges, is_convex  # noqa: E402
from .measurements import measured  # noqa: E402
from .polish import polish  # noqa: E402
from .registry import part  # noqa: E402  -- must win over any build123d name

# `polish` is here because the doctrine prescribes the algorithm and every project
# would otherwise write it: chamfer is all or nothing, so one edge that cannot land
# takes the pass down and the set gets narrowed by hand until it builds.
# `from nurb import *` hands a part file the whole build123d vocabulary, @part, the
# convexity test, and `measured`. The convexity test is here because a polish pass cannot
# be written without it: chamfering an inside corner is the one polish mistake that looks
# fine in code. `measured` is here because the alternative to asking for a dimension is
# inventing one, and an invented one builds, checks clean and prints.
__all__ = [
    *getattr(_b3d, "__all__", [n for n in dir(_b3d) if not n.startswith("_")]),
    "part",
    "is_convex",
    "concave_edges",
    "measured",
    "polish",
]
# The version lives in pyproject.toml and nowhere else; a second copy here would drift.
try:
    __version__ = _metadata.version("nurb")
except _metadata.PackageNotFoundError:  # a source tree on PYTHONPATH, never installed
    __version__ = "0.0.0"
