"""How far a part is from the mesh it is remodelling.

Remodelling an existing thing is a loop: measure the mesh, build the part, look at
what still differs, adjust. The looking is what this module does with numbers. The
mesh is the ground truth, the part is the attempt, and the two questions that decide
whether the attempt is done point in opposite directions: where does the part have
surface the mesh does not (material an original never had), and where does the mesh
have surface the part misses (detail not yet modelled). An average blurs the two
into one reassuring number, which is exactly how a part grows a boss the original
never had while the score improves.

The target is declared in the part's card, next to the other things a part has
justified, so the dev loop and the CLI read the same choice:

    ```toml
    target = "scans/bracket.stl"
    ```

or, when the file's units need saying, `target = { file = "scans/bracket.stl",
units = "mm" }`.

Frames are the honest limitation. The two shapes are compared after translating the
target's bounding-box center onto the part's, and nothing is rotated or scaled: a
part modelled in the mesh's own orientation lines up, one modelled sideways reports
large numbers that mean "rotated", not "wrong". The applied shift is reported and
also feeds the viewer, which draws the target as a ghost at exactly the alignment
these numbers used.
"""

import pathlib

import numpy as np

# Enough samples that the 95th percentile means something, few enough that the dev
# loop's check pass stays a beat, not a wait.
SAMPLES = 1500

# Prefilter geometry: edges longer than this get split before the distance queries,
# which bounds how far a triangle's surface can sit from its own corners and is what
# makes the candidate radius below provably catch the true nearest triangle.
MAX_EDGE = 3.0


def setting(settings):
    """The card's target, as (file, units-or-None), or None when the card names none."""
    raw = settings.get("target")
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw, None
    if isinstance(raw, dict) and isinstance(raw.get("file"), str):
        return raw["file"], raw.get("units")
    raise ValueError(
        'target is a path in quotes, or a table: target = { file = "scans/x.stl", units = "mm" }'
    )


def load(root, file, units=None):
    """The target mesh in millimetres, resolved against the project root."""
    from . import scan

    path = pathlib.Path(file)
    if not path.is_absolute():
        path = pathlib.Path(root) / path
    return scan.load(path, units=units)


def against(shape, mesh, tolerance=0.1):
    """The deviation between a built part and its target mesh, both directions.

    Returns the offset that centered the target on the part (in the part's frame,
    where the ghost draws), and for each direction the worst, the typical, and the
    95th-percentile distance in mm over surface samples.
    """
    from . import builder

    part = builder.to_mesh(shape, tolerance)
    if not len(part.faces):
        raise ValueError("the part has no surface to compare")
    offset = _center(part) - _center(mesh)
    moved = mesh.copy()
    moved.apply_translation(offset)
    part_d = _to_surface(_sample(part), moved)
    target_d = _to_surface(_sample(moved), part)
    return {
        "offset": [round(float(v), 2) for v in offset],
        "part": _stats(part_d),
        "target": _stats(target_d),
        "samples": SAMPLES,
    }


def report(name, file, metrics, unit, source):
    """The comparison as lines, facts only: the doctrine judges, this measures."""
    from .scan import LONG

    said = {
        "file": "declared by the file format",
        "argument": "said by the card or --units",
        "guess": "guessed from the file's span; wrong means set units",
    }
    moved = ", ".join(f"{v:g}" for v in metrics["offset"])
    lines = [
        f"  {name} against {file}  (read as {LONG[unit]}, {said[source]})",
        f"      target centered on the part, moved ({moved}) mm; nothing rotated or scaled",
        f"      part off the target:  {_line(metrics['part'])}   surface the target does not have",
        f"      target off the part:  {_line(metrics['target'])}   detail the part does not cover",
    ]
    return lines


def _line(s):
    return f"worst {s['max']:.2f}mm, typical {s['median']:.2f}mm, 95% within {s['p95']:.2f}mm"


def _stats(d):
    return {
        "max": round(float(d.max()), 2),
        "median": round(float(np.median(d)), 2),
        "p95": round(float(np.percentile(d, 95)), 2),
    }


def _center(mesh):
    return mesh.bounds.mean(axis=0)


def _sample(mesh):
    import trimesh

    # Seeded, so rerunning on unchanged geometry prints the same numbers and a moved
    # figure in the output always means moved geometry.
    points, _ = trimesh.sample.sample_surface(mesh, SAMPLES, seed=0)
    return np.asarray(points)


def _to_surface(points, mesh):
    """Unsigned distance from each point to the mesh's surface.

    Exact point-to-triangle distance, prefiltered through a KD-tree of triangle
    corners. The candidate ball is complete by construction: the nearest triangle
    has a corner within the true distance plus one edge length, the nearest corner
    already bounds the true distance from above, and subdivision caps the edge
    length. A fixed k-nearest prefilter is not sound here, because a fan of sliver
    triangles can crowd out the corners of the triangle a point actually lies on.
    rtree would hand trimesh the same query, but it is a native dependency this repo
    does not carry, while scipy already arrives with build123d.
    """
    import trimesh
    from scipy.spatial import cKDTree

    vertices, faces = trimesh.remesh.subdivide_to_size(
        mesh.vertices, mesh.faces, max_edge=MAX_EDGE
    )
    triangles = vertices[faces]
    corners = triangles.reshape(-1, 3)
    tree = cKDTree(corners)
    nearest, _ = tree.query(points)
    out = np.empty(len(points))
    for i, (point, ball) in enumerate(
        zip(points, tree.query_ball_point(points, nearest + MAX_EDGE + 1e-6))
    ):
        near = triangles[np.unique(np.asarray(ball) // 3)]
        closest = trimesh.triangles.closest_point(near, np.broadcast_to(point, near.shape[:1] + (3,)))
        out[i] = np.linalg.norm(closest - point, axis=1).min()
    return out
