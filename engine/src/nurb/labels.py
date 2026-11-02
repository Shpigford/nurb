"""Labels: names a person gives to spots on a part, held against each new build.

A label is a point and a normal in the part's own mm. It is never a B-rep face,
because face ids do not survive an edit. So each read measures how far the point now
sits from the surface the latest build made, and a label the part moved away from says
so instead of naming empty air.
"""

import collections
import io

import numpy as np

# Further than this from the new surface and the label no longer marks what it named.
# Well over the 0.1 mm meshing tolerance, well under any feature worth a name.
OFF_MM = 0.5


# A run's geometry never changes, so its triangles are kept by run id: a page reads the
# project on every change, and loading the GLB each time would be most of that read.
_LOADED = collections.OrderedDict()


def _triangles(run):
    found = _LOADED.get(run["id"])
    if found is None:
        import trimesh

        mesh = trimesh.load(io.BytesIO(run["glb"]), file_type="glb", force="mesh")
        found = _LOADED[run["id"]] = np.asarray(mesh.triangles)
        while len(_LOADED) > 32:
            _LOADED.popitem(last=False)
    return found


def _nearest(triangles, point):
    """(closest surface point, its triangle's unit normal, distance) for one point."""
    import trimesh

    point = np.asarray(point, dtype=float)
    closest = trimesh.triangles.closest_point(triangles, np.broadcast_to(point, (len(triangles), 3)))
    distance = np.linalg.norm(closest - point, axis=1)
    i = int(distance.argmin())
    a, b, c = triangles[i]
    normal = np.cross(b - a, c - a)
    length = np.linalg.norm(normal)
    return closest[i], normal / length if length else np.array([0.0, 0.0, 1.0]), float(distance[i])


def snap(run, point):
    """The spot on the run's surface nearest `point`, and the way that surface faces."""
    triangles = _triangles(run)
    if not len(triangles):
        raise ValueError("the part has no surface to label")
    at, normal, _ = _nearest(triangles, point)
    return [round(float(v), 3) for v in at], [round(float(v), 4) for v in normal]


def facing(normal):
    """Which way a spot faces, in the words spot.ts gives the chat."""
    x, y, z = normal
    if abs(z) > 0.9:
        return "up" if z > 0 else "down"
    if abs(x) > 0.9:
        return "+X" if x > 0 else "-X"
    if abs(y) > 0.9:
        return "+Y" if y > 0 else "-Y"
    return "sloped"


def placed(rows, run):
    """Each label as a page and an agent read it, measured against `run`'s surface.

    `off_mm` is how far the spot now sits from the part; `on_part` is whether that is
    close enough to still mean what it named. Without a run there is nothing to measure.
    """
    # Most parts have no labels, and a page reads every part on each change.
    if not rows:
        return []
    triangles = _triangles(run) if run is not None and run["glb"] else None
    out = []
    for row in rows:
        point = [row["x"], row["y"], row["z"]]
        normal = [row["nx"], row["ny"], row["nz"]]
        entry = {"name": row["name"], "point": point, "normal": normal, "facing": facing(normal)}
        if triangles is not None and len(triangles):
            off = _nearest(triangles, point)[2]
            entry["off_mm"] = round(off, 2)
            entry["on_part"] = off <= OFF_MM
        out.append(entry)
    return out
