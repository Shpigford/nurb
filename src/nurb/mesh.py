"""Measure a downloaded mesh, and grade a rebuild against it.

Most models on the sharing sites are distributed as meshes, and editing one for real
means rebuilding it as a part. The expensive step is not the modelling, it is the
measuring: an agent with only a viewer reverse-engineers dimensions one throwaway
script at a time. `nurb inspect <file.stl>` is those scripts, once, in the package,
in the same voice `nurb inspect <part>` uses, and `nurb compare <part> <file>` closes
the loop by measuring the rebuild against the original.

Two rules from the first real port, both learned the hard way. The distributed mesh
is the ground truth: a bundled STEP can carry features that never shipped, so compare
grades against the mesh and nothing else. And added material is its own failure:
averages stay quiet while an invented feature sticks 2mm out of a wall, so the
rebuilt-to-original direction gets a hard verdict line, not just percentiles.

Tessellation vertices lie on the true surface, so dimensions fitted through them are
exact; only chord count limits confidence. That is why the probe reports fitted
diameters at face value instead of hedging them.
"""

import zipfile
from collections import defaultdict
from xml.etree import ElementTree as ET

import numpy as np
import trimesh


def load(path):
    """Every solid in the file, as [(name, trimesh.Trimesh)].

    STL is one anonymous solid. 3MF is a zip of XML and may hold several objects,
    including the slicer flavour that stores each object in its own model file;
    trimesh's own 3MF loader wants networkx, which is not a dependency, and the
    format is simple enough to read directly.
    """
    suffix = path.suffix.lower()
    if suffix == ".stl":
        mesh = trimesh.load(str(path), file_type="stl")
        return [(path.name, mesh)]
    if suffix == ".3mf":
        return _load_3mf(path)
    raise ValueError(f"{path.name}: expected .stl or .3mf")


def _load_3mf(path):
    out = []
    with zipfile.ZipFile(path) as z:
        for name in sorted(n for n in z.namelist() if n.endswith(".model")):
            root = ET.fromstring(z.read(name))
            ns = {"m": root.tag.split("}")[0][1:]}
            for obj in root.iter(f"{{{ns['m']}}}object"):
                geom = obj.find("m:mesh", ns)
                if geom is None:
                    continue
                vs = np.array(
                    [
                        [float(v.get("x")), float(v.get("y")), float(v.get("z"))]
                        for v in geom.find("m:vertices", ns)
                    ]
                )
                ts = np.array(
                    [
                        [int(t.get("v1")), int(t.get("v2")), int(t.get("v3"))]
                        for t in geom.find("m:triangles", ns)
                    ]
                )
                out.append(
                    (
                        f"object {obj.get('id')}",
                        trimesh.Trimesh(vertices=vs, faces=ts, process=True),
                    )
                )
    if not out:
        raise ValueError(f"{path.name}: no mesh objects in the file")
    return out


class _Union:
    """Union-find over face indices, so grouping needs neither scipy nor networkx."""

    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def join(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def groups(self):
        out = defaultdict(list)
        for i in range(len(self.parent)):
            out[self.find(i)].append(i)
        return list(out.values())


def _fit_circle(pts):
    """Least-squares circle through 2D points: center, radius, rms residual."""
    A = np.column_stack([2 * pts, np.ones(len(pts))])
    b = (pts**2).sum(axis=1)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    center = sol[:2]
    r = float(np.sqrt(sol[2] + center @ center))
    resid = float(np.sqrt(np.mean((np.linalg.norm(pts - center, axis=1) - r) ** 2)))
    return center, r, resid


_AXES = {"X": np.array([1.0, 0, 0]), "Y": np.array([0, 1.0, 0]), "Z": np.array([0, 0, 1.0])}


def _basis(axis):
    a = np.array([1.0, 0, 0]) if abs(axis[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(axis, a)
    u /= np.linalg.norm(u)
    return u, np.cross(axis, u)


def planes(mesh, min_area=25.0):
    """Adjacent coplanar faces grouped into planes, largest first.

    Returns (plane rows, set of face indices they cover). Grouping is by adjacency,
    not by normal alone, so two parallel walls stay two planes.
    """
    normals = mesh.face_normals
    uf = _Union(len(mesh.faces))
    for a, b in mesh.face_adjacency:
        if normals[a] @ normals[b] > 0.99999:
            uf.join(a, b)
    areas = mesh.area_faces
    rows, covered = [], set()
    for group in uf.groups():
        area = float(areas[group].sum())
        if area < min_area:
            continue
        n = normals[group[0]]
        point = mesh.vertices[mesh.faces[group[0]][0]]
        rows.append({"normal": n, "offset": float(n @ point), "area": area, "faces": group})
        covered.update(group)
    rows.sort(key=lambda r: -r["area"])
    return rows, covered


def _split_by_curvature(mesh, faces, adjacency):
    """Split a mixed strip where the implied bend radius jumps.

    A wall profile arrives as one connected band of curved faces holding several
    arcs. Between adjacent faces the angle and distance imply a bend radius;
    clustering those radii on a log scale and cutting at gaps splits the band into
    single-curvature pieces a circle fit can accept.
    """
    normals, centroids = mesh.face_normals, mesh.triangles_center
    implied = {}
    fset = set(faces)
    for a, b in adjacency:
        if a not in fset or b not in fset:
            continue
        sin_half = np.linalg.norm(np.cross(normals[a], normals[b])) / 2
        if sin_half < 1e-4:
            continue
        implied[(a, b)] = float(
            np.linalg.norm(centroids[a] - centroids[b]) / (2 * sin_half)
        )
    if not implied:
        return []
    radii = np.sort(np.array(list(implied.values())))
    logs = np.log(radii)
    cuts = radii[1:][np.diff(logs) > np.log(1.8)]
    index = {f: i for i, f in enumerate(faces)}
    pieces = []
    for c in range(len(cuts) + 1):
        uf = _Union(len(faces))
        lo = cuts[c - 1] if c else 0.0
        hi = cuts[c] if c < len(cuts) else np.inf
        for (a, b), r in implied.items():
            if lo <= r < hi:
                uf.join(index[a], index[b])
        pieces += [
            [faces[i] for i in g] for g in uf.groups() if len(g) >= 4
        ]
    return pieces


def cylinders(mesh, planar_faces, min_radius=0.4):
    """Cylindrical regions along the principal axes: holes, bosses, corner rounds.

    Faces whose normals are perpendicular to an axis are clustered by adjacency,
    mixed-curvature strips are split, and each piece gets a circle fit through its
    vertices. Concavity comes from which way the faces look relative to the fitted
    center, coverage from the angular span, so a bore reads 360 and a corner 90.
    """
    normals = mesh.face_normals
    adjacency = mesh.face_adjacency
    ext = float(max(mesh.bounds[1] - mesh.bounds[0]))
    found = []
    for axname, axis in _AXES.items():
        perp = np.abs(normals @ axis) < 0.02
        cand = [f for f in np.where(perp)[0] if f not in planar_faces]
        if len(cand) < 4:
            continue
        index = {f: i for i, f in enumerate(cand)}
        uf = _Union(len(cand))
        for a, b in adjacency:
            if a in index and b in index:
                uf.join(index[a], index[b])
        u, v = _basis(axis)
        for group in uf.groups():
            group = [cand[i] for i in group]
            if len(group) < 4:
                continue
            for piece in [group, *(_split_by_curvature(mesh, group, adjacency) or [])]:
                verts = np.unique(mesh.faces[piece])
                pts = mesh.vertices[verts]
                flat = np.column_stack([pts @ u, pts @ v])
                center, r, resid = _fit_circle(flat)
                if resid > 0.02 * r or not min_radius <= r <= 0.6 * ext:
                    continue
                # a near-flat strip fits a huge circle centered far outside the
                # part; a real bore or round has its axis inside it
                lo = np.array([mesh.bounds[0] @ u, mesh.bounds[0] @ v])
                hi = np.array([mesh.bounds[1] @ u, mesh.bounds[1] @ v])
                lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
                if not ((lo - 0.05 * ext <= center) & (center <= hi + 0.05 * ext)).all():
                    continue
                centroids = mesh.triangles_center[piece]
                look = np.column_stack([normals[piece] @ u, normals[piece] @ v])
                toward = center - np.column_stack([centroids @ u, centroids @ v])
                concave = float(np.mean(np.einsum("ij,ij->i", toward, look) > 0)) > 0.5
                angles = np.sort(np.arctan2(flat[:, 1] - center[1], flat[:, 0] - center[0]))
                gap = np.diff(np.concatenate([angles, [angles[0] + 2 * np.pi]])).max()
                span = np.degrees(2 * np.pi - gap) + 360 / max(len(verts), 8)
                along = pts @ axis
                at = center[0] * u + center[1] * v + along.min() * axis
                found.append(
                    {
                        "axis": axname,
                        "radius": r,
                        "at": at,
                        "span": min(float(span), 360.0),
                        "depth": float(along.max() - along.min()),
                        "concave": concave,
                        "faces": piece,
                    }
                )
                if piece is group:
                    break  # whole group fit clean, no need for the split pieces
    return found


def _pitches(rounds):
    """Repeated spacings among full bores of one diameter, the grid a part is on."""
    lines = []
    groups = defaultdict(list)
    for r in rounds:
        if r["concave"] and r["span"] > 270:
            groups[(round(2 * r["radius"], 1), r["axis"])].append(r["at"])
    for (d, axname), centers in sorted(groups.items()):
        if len(centers) < 2:
            continue
        centers = np.array(centers)
        for i, coord in enumerate("XYZ"):
            values = np.unique(np.round(centers[:, i], 2))
            steps = np.diff(np.sort(values))
            steps = steps[steps > 1]
            if len(steps):
                shown = ", ".join(f"{s:.2f}" for s in np.unique(np.round(steps, 2)))
                lines.append(f"      d={d} bores along {axname}: {coord} spacing {shown}")
    return lines


def _label(n):
    key = tuple(int(round(c)) for c in n)
    if np.allclose(n, key, atol=1e-4) and sum(map(abs, key)) == 1:
        return {(1, 0, 0): "+X", (-1, 0, 0): "-X", (0, 1, 0): "+Y",
                (0, -1, 0): "-Y", (0, 0, 1): "+Z", (0, 0, -1): "-Z"}[key]
    return f"({n[0]:+.2f}, {n[1]:+.2f}, {n[2]:+.2f})"


def report(name, mesh, limit=12):
    """The probe report for a mesh, in `nurb inspect`'s voice."""
    size = mesh.bounds[1] - mesh.bounds[0]
    lines = [
        f"  {name}  {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm"
        f"  {mesh.volume:.1f}mm3  {len(mesh.faces)} triangles"
        f"{'' if mesh.is_watertight else ', NOT watertight'}",
        "  mesh vertices lie on the surfaces they sample, so fitted numbers below are"
        " dimensions, not estimates",
        "",
    ]

    plane_rows, planar_faces = planes(mesh)
    shown = plane_rows[:limit]
    lines.append(f"  planes  showing {len(shown)} of {len(plane_rows)}, largest first")
    for row in shown:
        lines.append(
            f"      {_label(row['normal']):>22}  offset {row['offset']:8.2f}"
            f"  {row['area']:9.1f}mm2"
        )
    lines.append("")

    rounds = cylinders(mesh, planar_faces)
    merged = defaultdict(list)
    for r in rounds:
        merged[
            (round(2 * r["radius"], 1), r["axis"], r["concave"], round(r["span"] / 45) * 45)
        ].append(r)
    lines.append(
        "  round features  360deg of coverage is a bore or a boss, less is a corner"
        " or a groove"
    )
    if merged:
        for (d, axname, concave, span), rs in sorted(merged.items()):
            kind = "concave" if concave else "convex"
            where = ", ".join(
                f"({r['at'][0]:.2f}, {r['at'][1]:.2f}, {r['at'][2]:.2f})" for r in rs[:4]
            )
            more = f" and {len(rs) - 4} more" if len(rs) > 4 else ""
            lines.append(
                f"      d={d:6.2f} along {axname}  {len(rs)}x  {kind}"
                f"  ~{span:.0f}deg  depth {rs[0]['depth']:.1f}  at {where}{more}"
            )
    else:
        lines.append("      none found")
    pitch_lines = _pitches(rounds)
    if pitch_lines:
        lines += ["", "  pitches"] + pitch_lines

    classified = set(planar_faces)
    for r in rounds:
        classified.update(r["faces"])
    loose = [f for f in range(len(mesh.faces)) if f not in classified]
    area = float(mesh.area_faces[loose].sum()) if loose else 0.0
    if area > 25:
        center = mesh.triangles_center[loose].mean(axis=0)
        lines += [
            "",
            f"  unclassified detail  {area:.0f}mm2 of curved faces near"
            f" ({center[0]:.1f}, {center[1]:.1f}, {center[2]:.1f})",
            "      embossed text, sculpted surfaces and organic shapes read as this;"
            " rebuild them deliberately or drop them and say so",
        ]
    return lines


def _nearest(query, reference):
    """Distance from each query point to the nearest reference point.

    scipy is not in nurb's own dependency list but build123d requires it, so it is
    always installed wherever a part can build.
    """
    from scipy.spatial import cKDTree

    return cKDTree(reference).query(query, workers=-1)[0]


def _exact(points, mesh, bounds):
    """True point-to-surface distance, for the points a verdict hangs on.

    Point-cloud distances carry the sampling spacing as noise, which is fine for
    percentiles and fatal for a max compared against a threshold. Each candidate is
    re-measured against real triangles. The cloud distance is an upper bound on the
    surface distance, so every triangle that could hold the nearest point has its
    centroid within that bound plus the largest centroid-to-vertex reach; nearest-k
    centroids alone are not enough, one huge triangle breaks them.
    """
    from scipy.spatial import cKDTree

    triangles = mesh.triangles
    centers = triangles.mean(axis=1)
    reach = float(np.linalg.norm(triangles - centers[:, None, :], axis=2).max())
    tree = cKDTree(centers)
    out = np.empty(len(points))
    for i, (p, bound) in enumerate(zip(points, bounds)):
        idx = tree.query_ball_point(p, bound + reach + 1e-9)
        cand = triangles[idx] if idx else triangles
        closest = trimesh.triangles.closest_point(cand, np.tile(p, (len(cand), 1)))
        out[i] = float(np.linalg.norm(closest - p, axis=1).min())
    return out


ADDED_LIMIT = 0.5  # mm of rebuilt surface with no original counterpart before compare fails


def _closed(mesh):
    welded = mesh.copy()
    welded.merge_vertices()
    return welded.is_watertight


def shift_onto(mover, target):
    """The translation that lays `mover` onto `target`: XY by centers of mass, Z by
    bottoms, which is the bed's frame.

    Centers of mass, not bounding boxes: one small protrusion drags a box center
    half its own size sideways and every wall reads as misplaced. Closedness is
    tested on a welded copy, because builder.to_mesh keeps vertices split at face
    borders for rendering and that alone fails is_watertight.
    """
    if _closed(mover) and _closed(target):
        xy = target.center_mass[:2] - mover.center_mass[:2]
    else:
        xy = (target.bounds[0][:2] + target.bounds[1][:2]) / 2 - (
            mover.bounds[0][:2] + mover.bounds[1][:2]
        ) / 2
    return np.append(xy, target.bounds[0][2] - mover.bounds[0][2])


def ghost_glb(part_mesh, original):
    """The original mesh laid onto the rebuild, as GLB bytes for the viewer's ghost.

    The viewer draws it translucent over the solid, so invented geometry pokes
    through the ghost and dropped detail shows as ghost with nothing under it. The
    alignment is the one compare grades with, so what the eye sees and what the
    verdict measured are the same frame.
    """
    ghost = original.copy()
    ghost.apply_translation(shift_onto(ghost, part_mesh))
    ghost.vertex_normals  # populate before export, or the GLB ships without normals
    return trimesh.Scene([ghost]).export(file_type="glb")


def best_match(loaded, like):
    """Which of a file's objects a part rebuilds: bounding box first, volume as the
    tie-break, because a download's size siblings share a box and differ only in
    what is inside it."""
    size = like.bounds[1] - like.bounds[0]
    return min(
        loaded,
        key=lambda nm: (
            round(float(np.abs((nm[1].bounds[1] - nm[1].bounds[0]) - size).sum()), 1),
            abs(float(nm[1].volume) - float(like.volume)),
        ),
    )


def _inside(points, mesh):
    """Whether each point is inside the mesh, by generalized winding number.

    trimesh's own contains() wants rtree even on its pure ray path. The
    van Oosterom-Strackee solid angle sum needs only the triangles, is exact for a
    closed oriented mesh, and the callers only ever ask about a handful of points.
    """
    out = np.empty(len(points), dtype=bool)
    for i, p in enumerate(points):
        t = mesh.triangles - p
        a, b, c = t[:, 0], t[:, 1], t[:, 2]
        la, lb, lc = (np.linalg.norm(v, axis=1) for v in (a, b, c))
        numer = np.einsum("ij,ij->i", a, np.cross(b, c))
        denom = (
            la * lb * lc
            + np.einsum("ij,ij->i", a, b) * lc
            + np.einsum("ij,ij->i", b, c) * la
            + np.einsum("ij,ij->i", c, a) * lb
        )
        winding = np.arctan2(numer, denom).sum() / (2 * np.pi)
        out[i] = winding > 0.5
    return out


def compare(part_mesh, original, samples=40000):
    """Grade a rebuild against the mesh it was rebuilt from.

    Alignment is XY centers and Z bottoms, which is the bed's frame; no rotation
    search, so a rebuild modelled sideways fails loudly instead of matching quietly.
    The two directions mean different things: original-to-rebuilt distance is detail
    the rebuild dropped, rebuilt-to-original is material the rebuild INVENTED, and
    invented material past ADDED_LIMIT is a failure on its own no matter how good
    the averages look, because that is exactly the error averages hide.
    """
    a, b = original.copy(), part_mesh.copy()
    shift = shift_onto(b, a)
    b.apply_translation(shift)

    # the reference cloud sets the measurement floor: aim for 0.15mm spacing so a
    # 0.5mm verdict is measuring geometry, not sampling noise
    dense = min(int(max(a.area, b.area) / 0.15**2), 5_000_000)
    ref_a, _ = trimesh.sample.sample_surface(a, dense)
    ref_b, _ = trimesh.sample.sample_surface(b, dense)
    qa, _ = trimesh.sample.sample_surface(a, samples)
    qb, _ = trimesh.sample.sample_surface(b, samples)
    dropped = _nearest(qa, ref_b)
    added = _nearest(qb, ref_a)

    # exact point-to-triangle distances where they matter: the worst tail of each
    # direction, and every added candidate that could cross the verdict line, since
    # a cloud distance is an upper bound and only exact numbers may fail a rebuild
    for values, points, target, limit in (
        (dropped, qa, b, None),
        (added, qb, a, ADDED_LIMIT),
    ):
        worst = set(np.argsort(values)[-min(200, len(values)):])
        if limit is not None:
            worst |= set(np.where(values > 0.8 * limit)[0][:2000])
        worst = np.fromiter(worst, dtype=np.int64)
        values[worst] = _exact(points[worst], target, values[worst])

    # far rebuilt surface is only INVENTED if it lies outside the original solid;
    # far but inside means omitted detail seen from its own footprint, which is the
    # advisory direction's business. The wall under a dropped boss is the case: the
    # original has no surface there, but the material is all hers.
    offenders = np.where(added > ADDED_LIMIT)[0]
    if len(offenders):
        offenders = offenders[~_inside(qb[offenders], a)]
    worst = int(offenders[np.argmax(added[offenders])]) if len(offenders) else int(np.argmax(added))

    floor = np.sqrt(a.area / dense)  # mean reference sample spacing, the resolution
    return {
        "shift": shift,
        "volume": (float(b.volume), float(a.volume)),
        "dropped": dropped,
        "added": added,
        "resolution": float(floor),
        "worst_added": float(added[worst]),
        "worst_added_at": qb[worst],
        "ok": len(offenders) == 0,
    }


def compare_report(part_name, mesh_name, result):
    added, dropped = result["added"], result["dropped"]
    rebuilt_v, orig_v = result["volume"]
    dx, dy, dz = result["shift"]
    lines = [
        f"  {part_name} vs {mesh_name}, aligned by XY center and bottom"
        f" (moved {dx:+.2f}, {dy:+.2f}, {dz:+.2f})",
        f"  volume  rebuilt {rebuilt_v:.0f}mm3, original {orig_v:.0f}mm3,"
        f" {100 * (rebuilt_v - orig_v) / orig_v:+.1f}%",
        f"  measured against sampling with ~{result['resolution']:.2f}mm resolution",
        "",
        f"  original -> rebuilt, detail the rebuild dropped:"
        f"  median {np.median(dropped):.2f}  p95 {np.percentile(dropped, 95):.2f}"
        f"  max {dropped.max():.2f} mm",
        f"  rebuilt -> original, material the rebuild invented:"
        f"  median {np.median(added):.2f}  p95 {np.percentile(added, 95):.2f}"
        f"  max {added.max():.2f} mm",
    ]
    if result["ok"]:
        lines.append(f"  no invented material past {ADDED_LIMIT}mm")
    else:
        x, y, z = result["worst_added_at"]
        lines.append(
            f"  FAIL: the rebuild has surface {result['worst_added']:.2f}mm outside"
            f" anything in the original, near ({x:.1f}, {y:.1f}, {z:.1f})."
        )
        lines.append(
            "      That is invented geometry. The mesh is the ground truth; remove or"
            " justify the feature before trusting this rebuild."
        )
    return lines
