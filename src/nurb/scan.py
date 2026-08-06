"""What a mesh measured, so a part can be modelled against something that exists.

A photo names a shape but carries no millimetres. A mesh carries them, and two kinds
arrive: a ten-second phone scan (Scaniverse, Polycam, and their kind), and a file
downloaded off a model site. This module reads either the same way, because they are
the same question at this stage: overall size in mm with the file's units made
explicit, and a cross-section sliced into a polyline short enough to sketch against.

Where they differ is what the numbers are worth, and that is not visible in the
geometry. A phone scan is reference geometry and its fits stay provisional until a
coupon proves them; a download is exact to the micron. Nothing in the mesh says which
one it is, so this module never guesses. The 3DBenchy, a designed model, scores like a
capture on every statistic worth computing. Provenance is something the user said and
the agent knows, so the judgement lives in the skill, and this reports facts.

The units question is the dangerous one. Scan apps export metres and slicers export
millimetres, and a mesh 0.3 units across does not say which it is. Guessing wrong is a
part a thousand times off that still builds, so the guess is stated in the report and
overridable rather than silent.
"""

import pathlib
import re
from collections import defaultdict

import numpy as np

UNITS = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4}
LONG = {"mm": "millimetres", "cm": "centimetres", "m": "metres", "in": "inches"}
DECLARED = {
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "m": "m",
    "meter": "m",
    "meters": "m",
    "in": "in",
    "inch": "in",
    "inches": "in",
}

# Under this many file units across, a mesh is read as metres: nothing a phone can
# scan is under a centimetre, and metres are what the scan apps export.
METRES_BELOW = 10.0

# The render command's grammar for a cut, reused so an agent learns it once:
# an axis, optionally with a fraction of the span or an absolute millimetre.
CUT = re.compile(r"^[xyz](:-?\d*\.?\d+(mm)?)?$")

# Plane intersection on a scan yields confetti along with the profile: pinholes and
# fold-overs each shed a chain a few segments long. Anything shorter than this
# fraction of the longest chain is reported as a count instead of listed.
FRAGMENT = 0.02


def load(path, units=None):
    """The mesh scaled to millimetres, its input unit, and that unit's source."""
    import trimesh

    path = pathlib.Path(path)
    if not path.is_file():
        raise ValueError(f"no file at {path}")
    if path.suffix.lower() == ".3mf":
        # As common as STL on the model sites, and trimesh reads it only with networkx
        # installed. "No module named 'networkx'" is not something a user can act on,
        # and a dependency is not worth one format the slicer already converts.
        raise ValueError(
            f"{path.name} is a 3MF, which nurb does not read. Open it in your slicer "
            f"and export the plate as STL, then run this on that file"
        )
    try:
        mesh = trimesh.load(str(path), force="mesh")
    except Exception as exc:
        raise ValueError(f"{path.name}: {exc}") from exc
    if not hasattr(mesh, "faces") or len(mesh.faces) == 0:
        # The likeliest way here is a gaussian-splat export, which is what some scan
        # apps offer first and which carries points with no surfaces between them.
        raise ValueError(
            f"{path.name} has no triangles to measure, only points. If this came "
            f"from a scan app, export a mesh format (OBJ, STL or GLB) instead. If "
            f"the app only offers splat or point-cloud formats, the scan itself "
            f"was captured as a splat, and the object needs a quick rescan in the "
            f"app's mesh mode"
        )
    # GLB/glTF defines metres and trimesh carries that declaration in `units`.
    # Prefer any declaration over a size guess: an area scan can legitimately be
    # more than ten metres across, where the heuristic would be wrong by 1,000x.
    declared = DECLARED.get(str(mesh.units).lower()) if mesh.units else None
    if units:
        unit, source = units, "argument"
    elif declared:
        unit, source = declared, "file"
    else:
        unit = "m" if float(mesh.extents.max()) < METRES_BELOW else "mm"
        source = "guess"
    if UNITS[unit] != 1.0:
        mesh.apply_scale(UNITS[unit])
    # Textured GLBs commonly split a physical vertex at normal and UV seams. The
    # geometry is still closed, but the split topology makes `is_watertight` lie.
    # Welding by position changes no measurement and gives topology its true shape.
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    return mesh, unit, source


def report(path, mesh, unit, source):
    path = pathlib.Path(path)
    # .4g, not .1f: a mis-unit mesh read as mm can be 0.04mm across, and a size
    # line that rounds that to 0.0 states a falsehood right where units go wrong.
    size = " x ".join(f"{v:.4g}" for v in mesh.extents)
    surface = "watertight" if mesh.is_watertight else "open surface"
    lines = [f"  {path.name}  {len(mesh.faces):,} triangles, {surface}, {size} mm"]
    if source == "guess":
        span = float(mesh.extents.max()) / UNITS[unit]
        # No longer says "which is what phone scan apps export": that is why the
        # threshold exists, but stating it as the file's origin reads as a verdict on
        # provenance, and a downloaded part is exact however this line is worded.
        lines.append(
            f"      read as {LONG[unit]}: the file spans {span:.3g} units, and only a "
            f"mesh under {METRES_BELOW:.0f} units across is read as metres. "
            f"Wrong? --units says so"
        )
    elif source == "file":
        lines.append(f"      read as {LONG[unit]} (declared by the file format)")
    else:
        lines.append(f"      read as {LONG[unit]} (--units)")
    lines.append(f"      {_solid_line(path, mesh, unit, source)}")
    return lines


def _solid_line(path, mesh, unit, source):
    """Whether this mesh can be a part's solid, answered before the agent tries it.

    The one question a mesh report has to settle, because the alternative is an agent
    guessing at `import_stl` and finding out through a refusal. Flat faces are counted
    only in the case that can import, where they are what the part would be made of;
    counting them on a 226,000-triangle download would take a third of a second to
    report a number nobody can act on.

    The call it prints carries `units` whenever this report only got the size right
    because someone passed it, because the same file imported without that argument is
    a part off by a factor of ten or a thousand that still builds.
    """
    from . import mesh as mesh_module

    problem = mesh_module.refusal(path.suffix, mesh)
    if problem:
        return (
            f"no solid from this one: it is {problem}. "
            f"Rebuild it from these measurements"
        )
    solid, problem = mesh_module.conversion(path)
    if problem:
        return (
            f"no solid from this one: it is {problem}. "
            f"Rebuild it from these measurements"
        )
    argument = f", units={unit!r}" if source == "argument" else ""
    call = f"import_stl({str(path)!r}{argument})"
    flats = len(solid.faces())
    return (
        f"{call} returns this as a solid: {flats} flat "
        f"{'face' if flats == 1 else 'faces'}. Any curve in it comes back as facets"
    )


def section(mesh, spec, tolerance=0.2):
    """A cross-section as polylines an agent can sketch against, longest first.

    Returns axis and position of the cut, the names of the two in-plane axes the
    points are reported in, the profiles as (points, closed, length) dicts, and how
    many sub-fragment chains were dropped at what floor.
    """
    import trimesh

    if not CUT.match(spec or ""):
        raise ValueError(
            f"section {spec!r} is not AXIS[:POS]. z cuts mid-mesh, z:0.7 at a "
            f"fraction of the span, z:40mm at that coordinate in the scan's own frame"
        )
    axis = "xyz".index(spec[0])
    lo, hi = float(mesh.bounds[0][axis]), float(mesh.bounds[1][axis])
    pos = (lo + hi) / 2
    if ":" in spec:
        raw = spec.split(":", 1)[1]
        pos = float(raw[:-2]) if raw.endswith("mm") else lo + float(raw) * (hi - lo)
    normal, origin = np.zeros(3), np.zeros(3)
    normal[axis], origin[axis] = 1.0, pos
    segments = trimesh.intersections.mesh_plane(
        mesh, plane_normal=normal, plane_origin=origin
    )
    keep = [i for i in range(3) if i != axis]
    chains = _chains(np.asarray(segments)[:, :, keep]) if len(segments) else []
    chains.sort(key=_length, reverse=True)
    floor = _length(chains[0]) * FRAGMENT if chains else 0.0
    profiles, skipped = [], 0
    for chain in chains:
        if _length(chain) < floor:
            skipped += 1
            continue
        closed = len(chain) > 3 and _key(chain[0]) == _key(chain[-1])
        profiles.append(
            {
                "points": _simplify(chain, tolerance),
                "raw": len(chain),
                "closed": closed,
                "length": _length(chain),
            }
        )
    return {
        "axis": spec[0],
        "pos": pos,
        "plane": tuple("xyz"[i] for i in keep),
        "profiles": profiles,
        "skipped": skipped,
        "floor": floor,
        "tolerance": tolerance,
    }


# How many points of one profile get printed. A slice of a noisy scan can survive
# simplification hundreds of points long, and a wall of coordinates stops being
# something to sketch against.
LISTED = 120


def section_report(cut):
    u, v = cut["plane"]
    lines = [
        f"  section {cut['axis']} = {cut['pos']:.2f}mm  points are ({u}, {v}) in mm"
    ]
    if not cut["profiles"]:
        lines.append("      the plane misses the mesh")
        return lines
    for prof in cut["profiles"]:
        shape = "closed loop" if prof["closed"] else "open"
        points = prof["points"]
        lines.append(
            f"      {shape}, {prof['length']:.1f}mm, {prof['raw']} points -> "
            f"{len(points)} at {cut['tolerance']}mm tolerance"
        )
        for p in points[:LISTED]:
            lines.append(f"          ({p[0]:8.2f}, {p[1]:8.2f})")
        if len(points) > LISTED:
            lines.append(
                f"          and {len(points) - LISTED} more. Raise --tolerance to thin it"
            )
    if cut["skipped"]:
        lines.append(
            f"      {cut['skipped']} fragment(s) under {cut['floor']:.1f}mm skipped"
        )
    return lines


def _key(p):
    """An endpoint on a 0.001mm grid, so segments that meet actually match."""
    return (round(float(p[0]), 3), round(float(p[1]), 3))


def _length(points):
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


def _chains(segments):
    """Raw plane-intersection segments joined end to end into polylines.

    trimesh chains sections itself, but only through networkx, and a dependency is
    not worth what forty lines cover. A junction where three segments meet takes
    whichever continuation comes first, which is fine at scan fidelity.
    """
    at = defaultdict(list)
    for i, seg in enumerate(segments):
        at[_key(seg[0])].append(i)
        at[_key(seg[1])].append(i)
    used, chains = set(), []
    for start in range(len(segments)):
        if start in used:
            continue
        used.add(start)
        chain = [segments[start][0], segments[start][1]]
        for forward in (True, False):
            while True:
                tip = chain[-1] if forward else chain[0]
                free = [i for i in at[_key(tip)] if i not in used]
                if not free:
                    break
                i = free[0]
                used.add(i)
                a, b = segments[i]
                grown = b if _key(a) == _key(tip) else a
                chain.append(grown) if forward else chain.insert(0, grown)
        chains.append(np.asarray(chain))
    return chains


def _simplify(points, tolerance):
    """Douglas-Peucker, keeping every point that moves the line more than the tolerance."""
    if len(points) < 3:
        return points
    keep = np.zeros(len(points), dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        seg = points[b] - points[a]
        rel = points[a + 1 : b] - points[a]
        span = float(np.hypot(*seg))
        if span == 0:  # a closed loop's ends coincide; distance from the point instead
            d = np.linalg.norm(rel, axis=1)
        else:
            d = np.abs(rel[:, 0] * seg[1] - rel[:, 1] * seg[0]) / span
        worst = int(d.argmax())
        if d[worst] > tolerance:
            i = a + 1 + worst
            keep[i] = True
            stack += [(a, i), (i, b)]
    return points[keep]
