"""A mesh as a part's starting solid, in the one case where it can be one.

`import_stl` is the name a model reaches for the moment a downloaded file lands in a
project, and build123d's returns a `Face`: a triangulated sheet with no inside.
Subtracting from one does not raise, it segfaults, and a part builds inside the `nurb
dev` process, so that takes the watcher down with no traceback. An error that kills the
loop and prints nothing is the worst one this codebase can produce, which is what makes
this import worth owning.

What it can honestly do is narrow, because a mesh carries no design. A wall thickness
in an STL is a distance between two sheets of triangles, not a number anyone can
change, so nothing here recovers a parameter. What does survive is flat faces, and
those survive exactly: a box returns as six planar faces at its original size, an
L-bracket as fourteen, a box already chamfered as twenty-six, and every one of those
faces chamfers again. Curves do not survive at all. A cylinder returns as a 126-sided
prism with no circular edge left to select, so the selector that would grab its rim
finds nothing, and a 3mm fillet becomes nine thousand facets.

So the flat-faced case returns a solid and everything else is refused by name, pointing
at `nurb scan`. Measuring the file and rebuilding it in code is the only path that ends
with parameters, and a part with parameters is the whole point.
"""

import math
import pathlib
import shlex
import shutil
import tempfile

import numpy as np

# Above this many triangles the file is refused instead of converted. The conversion is
# superlinear and a part reruns it on every save: 500 triangles takes 0.06s, 9,500 takes
# 1.1s, 82,000 takes 42s, and a 226,000-triangle download off a model site takes 111s to
# read and another 51s for a single boolean. Flat-faced geometry, the only kind that
# survives the trip, sits far below this: a box is 12 triangles, an L-bracket 44, a
# plate with four holes 92. So the ceiling costs the good case nothing and catches the
# case that would otherwise look like a hang.
TRIANGLE_CEILING = 2_000

# What converts to a solid, which is narrower than what `nurb scan` measures. OBJ, GLB
# and PLY are measurable and not convertible, and saying so beats letting the kernel
# fail with "Null TopoDS_Shape object", which reads as a complaint about the triangles.
CONVERTIBLE = (".stl",)


def refusal(suffix, mesh):
    """Why this mesh cannot be a part's solid, or None when it can.

    Takes the trimesh both callers already hold, rather than a couple of facts off it,
    so that adding a reason here cannot leave `nurb scan` promising an import that
    `import_stl` then refuses. It reads on from "<file> is", and carries neither the
    filename nor the next step, because the two callers owe the reader different ones:
    the exception sends them to `nurb scan`, and `nurb scan` is what they ran.
    """
    triangles = len(mesh.faces)
    if suffix.lower() not in CONVERTIBLE:
        return (
            f"a {suffix.lower()}, and only {' and '.join(CONVERTIBLE)} converts to a "
            f"solid. Every other mesh format is measured and not imported"
        )
    if not mesh.is_watertight:
        return (
            f"not closed: {triangles:,} triangles with holes in the surface, and a "
            f"surface with holes has no inside to make solid"
        )
    if triangles > TRIANGLE_CEILING:
        return (
            f"{triangles:,} triangles, over the {TRIANGLE_CEILING:,} a part can afford "
            f"to convert on every save, and a mesh this dense is curved anyway, so its "
            f"curves would come back as facets with no edge left to select"
        )
    # Signed volume settles the last two, and both are closed, so nothing above catches
    # them. Zero or NaN means the triangles enclose nothing; negative means they enclose
    # it inside out, and that one is the dangerous one because nothing downstream
    # objects: cutting a hole in an inverted solid *adds* material, and the part builds,
    # checks and exports. The errstate is for the NaN case, where trimesh divides by the
    # volume it just computed and numpy announces it on the way past the user.
    with np.errstate(invalid="ignore", divide="ignore"):
        volume = float(mesh.volume)
    if not math.isfinite(volume) or volume == 0.0:
        return (
            "closed, but its triangles enclose nothing, which means degenerate or "
            "zero-area ones among them"
        )
    if volume < 0:
        return (
            "inside out: closed, but its triangles face inward, so every boolean "
            "against it does the opposite of what it reads like. Most slicers and mesh "
            "repair tools fix the winding, and re-exporting is enough"
        )
    return None


def _refuse(path, problem):
    """The refusal, returned rather than raised so the `raise` stays at the call site."""
    path = pathlib.Path(path)
    return ValueError(
        f"{path.name} is {problem}. `{shlex.join(('nurb', 'scan', str(path)))}` "
        f"measures it instead, and a part "
        f"rebuilt from those measurements is the one with parameters"
    )


def conversion(path):
    """The cleaned, valid kernel solid for `path`, or the reason none came out.

    This is shared with `nurb scan`: passing the inexpensive mesh checks is not proof
    that OCCT can build a body, so the report must run the same final conversion before
    it promises one. Lib3MF dispatches on a case-sensitive extension even though file
    formats are not case-sensitive, so uppercase STL files get a temporary normalized
    name for the duration of the read.
    """
    from build123d import Mesher

    path = pathlib.Path(path)
    try:
        if path.suffix == ".stl":
            shapes = Mesher().read(str(path))
        else:
            with tempfile.TemporaryDirectory(prefix="nurb-stl-") as directory:
                normalized = pathlib.Path(directory) / "mesh.stl"
                shutil.copyfile(path, normalized)
                shapes = Mesher().read(str(normalized))
        # `clean` is what makes the result editable rather than merely correct: it
        # merges the coplanar triangles back into the faces they were cut from. Without
        # it a box is twelve triangles, and chamfering its edges chamfers the
        # triangulation's diagonal seams too, for 44 faces where 26 is right.
        solid = shapes[0].clean() if shapes else None
        if solid is None or not solid.is_valid or solid.volume <= 0:
            solid = None
    except Exception:
        solid = None
    if solid is None:
        # The backstop, for a mesh trimesh is happy with that the kernel still will not
        # take: self-intersections and multiple incompatible shells, mostly. Lib3MF can
        # also return a positive-volume shape that OCCT itself marks invalid, so volume
        # alone is not enough to call the result a solid.
        return None, (
            "closed, but the kernel could not build a valid body from these triangles, "
            "which usually means they intersect each other or contain incompatible shells"
        )
    return solid, None


def import_stl(file_name, units=None):
    """A closed, flat-faced STL as a real solid, or a refusal that names `nurb scan`.

    build123d's `import_stl` returns a `Face` with no volume, and subtracting from that
    segfaults rather than raising. `units` is `nurb scan --units`, and means the same
    thing: the file's own unit, when the size guess would get it wrong.
    """
    from . import scan

    path = pathlib.Path(file_name)
    # Read through `scan`, not trimesh directly, so a file measured by `nurb scan` and
    # then imported comes back at the size that was reported. An STL carries no unit,
    # scan apps export metres, and importing those raw is a part 1,000x too small that
    # builds and checks clean. It also buys the point-cloud message for free.
    mesh, unit, _ = scan.load(path, units=units)
    # The inexpensive reasons live in `refusal`; `nurb scan` shares both that gate and
    # `conversion`, so it cannot promise a body that this call then refuses. OCCT would
    # refuse almost none of the mesh-level problems: it builds a solid from an open
    # surface and reports a volume for it, it takes a quarter-million triangles given
    # two minutes, and an inverted mesh converts silently into a body whose booleans run
    # backwards.
    problem = refusal(path.suffix, mesh)
    if problem:
        raise _refuse(path, problem)
    solid, problem = conversion(path)
    if problem:
        raise _refuse(path, problem)
    factor = scan.UNITS[unit]
    return solid.scale(factor) if factor != 1.0 else solid
