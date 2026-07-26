"""nurb -- agentic CAD for 3D printing.

A part file needs one import:

    from nurb import *

    @part
    def dispenser(width=80, height=120, wall=2):
        return Box(width, height, wall)
"""

import build123d as _b3d
from build123d import *  # noqa: F401,F403  -- geometry vocabulary

from .checks import concave_edges, is_convex  # noqa: E402
from .registry import part  # noqa: E402  -- must win over any build123d name

# `from nurb import *` hands a part file the whole build123d vocabulary, @part, and the
# convexity test. That last one is here because a polish pass cannot be written without
# it: chamfering an inside corner is the one polish mistake that looks fine in code.
__all__ = [
    *getattr(_b3d, "__all__", [n for n in dir(_b3d) if not n.startswith("_")]),
    "part",
    "is_convex",
    "concave_edges",
]
__version__ = "0.1.0"
