"""Static stress under one load: where a part concentrates it, and how much margin is left.

The part is voxelized off the same tessellation the viewer draws, each voxel becomes a
linear-elastic brick element, and one sparse solve gives the whole displacement field.
No tet mesher: the classic route needs gmsh or netgen, both heavy native dependencies,
and a heat map for a printed part does not need their accuracy. Validated against the
analytic cantilever in tests/test_stress.py, this lands within a few percent on
deflection and finds stress concentrations at the right features; the peak magnitude
is honest to about +/-30%, which the viewer says out loud.

Units are mm / N / MPa throughout. Material is PLA, the workshop default; other
filaments mostly scale these numbers rather than move the hot spots.
"""

import numpy as np

# Room-temperature textbook values, MPa. `yield` is the bulk plastic letting go;
# `layer` is the weaker glue between printed layers, the seam an FDM part actually
# splits at when the load pulls its layers apart. TPU is deliberately absent: it
# bends instead of breaking, and a linear solver would print fiction about it.
MATERIALS = {
    "PLA": {"E": 3500.0, "yield": 50.0, "layer": 25.0},
    "PETG": {"E": 2100.0, "yield": 47.0, "layer": 30.0},
    "ABS": {"E": 2200.0, "yield": 40.0, "layer": 18.0},
    "ASA": {"E": 2400.0, "yield": 43.0, "layer": 20.0},
    "Nylon": {"E": 1700.0, "yield": 45.0, "layer": 30.0},
    "PC": {"E": 2300.0, "yield": 60.0, "layer": 30.0},
}
E_PLA = MATERIALS["PLA"]["E"]  # the calibration tests speak PLA
NU = 0.35
GRAVITY = 9.81


def material_named(name):
    """The MATERIALS row for a name, case-blind, with a real sentence for the misses."""
    for key, props in MATERIALS.items():
        if key.lower() == str(name).lower():
            return key, props
    if str(name).lower() == "tpu":
        raise ValueError(
            "TPU bends instead of breaking, so this solver has no honest answer for it. "
            f"Pick one of {', '.join(MATERIALS)}."
        )
    raise ValueError(f"no material called {name!r}. Have: {', '.join(MATERIALS)}.")

# Corner order for the brick element; the shape functions below index against it.
_CORNERS = np.array([
    (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
    (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
])


def _elastic_C(E, nu):
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    C = np.zeros((6, 6))
    C[:3, :3] = lam
    C[np.arange(3), np.arange(3)] = lam + 2 * mu
    C[3:, 3:] = np.eye(3) * mu
    return C


def _B_matrix(xi, eta, zeta, h):
    """Strain-displacement matrix at one natural-coordinate point of a cube of edge h."""
    g = np.zeros((8, 3))
    for a, (i, j, k) in enumerate(_CORNERS):
        fx = xi if i else (1 - xi)
        fy = eta if j else (1 - eta)
        fz = zeta if k else (1 - zeta)
        g[a] = ((1 if i else -1) * fy * fz, fx * (1 if j else -1) * fz, fx * fy * (1 if k else -1))
    g /= h
    B = np.zeros((6, 24))
    for a in range(8):
        dNx, dNy, dNz = g[a]
        c = 3 * a
        B[0, c] = dNx
        B[1, c + 1] = dNy
        B[2, c + 2] = dNz
        B[3, c] = dNy
        B[3, c + 1] = dNx
        B[4, c + 1] = dNz
        B[4, c + 2] = dNy
        B[5, c] = dNz
        B[5, c + 2] = dNx
    return B


def _hex_KE(E, nu, h):
    """24x24 stiffness of one cubic element, 2x2x2 Gauss quadrature."""
    C = _elastic_C(E, nu)
    gp = [0.5 - 0.5 / np.sqrt(3), 0.5 + 0.5 / np.sqrt(3)]
    KE = np.zeros((24, 24))
    w = (h / 2) ** 3
    for xi in gp:
        for eta in gp:
            for zeta in gp:
                B = _B_matrix(xi, eta, zeta, h)
                KE += B.T @ C @ B * w
    return KE


class _Voxels:
    """A filled voxel grid as a finite-element model: nodes, elements, one solve."""

    def __init__(self, filled, pitch, origin):
        self.filled = filled
        self.pitch = pitch
        self.origin = np.asarray(origin, float)
        nx, ny, nz = filled.shape
        self.elems = np.argwhere(filled)
        corners = self.elems[:, None, :] + _CORNERS[None, :, :]
        flat = corners.reshape(-1, 3)
        # Number only the nodes an element touches, so empty space costs nothing.
        nid = -np.ones((nx + 1, ny + 1, nz + 1), dtype=np.int64)
        nid[flat[:, 0], flat[:, 1], flat[:, 2]] = 0
        used = np.argwhere(nid == 0)
        nid[used[:, 0], used[:, 1], used[:, 2]] = np.arange(len(used))
        self.n_nodes = len(used)
        self.node_xyz = self.origin + used * pitch
        self.enodes = nid[corners[:, :, 0], corners[:, :, 1], corners[:, :, 2]]
        self.edofs = (self.enodes[:, :, None] * 3 + np.arange(3)[None, None, :]).reshape(-1, 24)
        self.centers = self.origin + (self.elems + 0.5) * pitch

    def solve(self, fixed_nodes, loaded_nodes, force, E=E_PLA):
        """Displacements under `force` (a 3-vector, N total) spread over the loaded nodes."""
        import scipy.sparse as sp
        import scipy.sparse.linalg as spla

        # A face pair can share nodes along an edge, and coarse voxels can make thin,
        # distinct faces share whole rows. Loads assigned to fixed DOFs disappear when
        # the reduced system is formed, so remove them before dividing the requested
        # force. Otherwise the answer quietly solves for less weight than it reports.
        loaded_nodes = np.setdiff1d(loaded_nodes, fixed_nodes)
        if not len(loaded_nodes):
            raise ValueError(
                "the loaded face overlaps the held face at this analysis resolution. "
                "Pick faces farther apart or use a finer --pitch."
            )

        KE = _hex_KE(E, NU, self.pitch)
        rows = np.repeat(self.edofs, 24, axis=1).ravel()
        cols = np.tile(self.edofs, (1, 24)).ravel()
        data = np.tile(KE.ravel(), len(self.elems))
        K = sp.coo_matrix((data, (rows, cols)), shape=(3 * self.n_nodes,) * 2).tocsr()

        F = np.zeros(3 * self.n_nodes)
        for axis in range(3):
            if force[axis]:
                F[loaded_nodes * 3 + axis] = force[axis] / len(loaded_nodes)
        fixed_dofs = (np.asarray(fixed_nodes)[:, None] * 3 + np.arange(3)).ravel()
        free = np.setdiff1d(np.arange(3 * self.n_nodes), fixed_dofs)
        Kff = K[free][:, free]
        # Jacobi-preconditioned CG: measured faster than SuperLU on these systems at
        # every size tried, and it never materializes a factor.
        M = sp.diags(1.0 / Kff.diagonal())
        u_free, info = spla.cg(Kff, F[free], M=M, rtol=1e-6, maxiter=20000)
        if info != 0:
            raise ValueError(
                "the solve did not converge, which usually means the held face does "
                "not actually restrain the part. Pick a hold spot on solid material."
            )
        u = np.zeros(3 * self.n_nodes)
        u[free] = u_free
        return u

    def stresses(self, u, E=E_PLA):
        """(von Mises, full tensor rows) per element, evaluated at element centers."""
        C = _elastic_C(E, NU)
        B = _B_matrix(0.5, 0.5, 0.5, self.pitch)
        s = u[self.edofs] @ (C @ B).T
        vm = np.sqrt(
            0.5 * ((s[:, 0] - s[:, 1]) ** 2 + (s[:, 1] - s[:, 2]) ** 2 + (s[:, 2] - s[:, 0]) ** 2)
            + 3 * (s[:, 3] ** 2 + s[:, 4] ** 2 + s[:, 5] ** 2)
        )
        return vm, s

    def von_mises(self, u, E=E_PLA):
        return self.stresses(u, E)[0]


def face_at(shape, point):
    """The B-rep face nearest a point, which is how a click names a face."""
    faces = shape.faces()
    if not faces:
        raise ValueError("this part has no faces to analyze")
    return min(faces, key=lambda f: f.distance_to(tuple(point)))


def _face_nodes(face, model):
    """The model nodes lying on a face: the set a pick fixes or loads."""
    bb = face.bounding_box()
    slack = model.pitch
    xyz = model.node_xyz
    near = np.where(
        (xyz[:, 0] > bb.min.X - slack) & (xyz[:, 0] < bb.max.X + slack)
        & (xyz[:, 1] > bb.min.Y - slack) & (xyz[:, 1] < bb.max.Y + slack)
        & (xyz[:, 2] > bb.min.Z - slack) & (xyz[:, 2] < bb.max.Z + slack)
    )[0]
    # Voxel surfaces sit up to half a pitch off the true face, so the tolerance has
    # to reach past that or a coarse grid finds no nodes on a perfectly good face.
    keep = [n for n in near if face.distance_to(tuple(xyz[n])) < 0.87 * model.pitch]
    return np.array(keep, dtype=np.int64)


def _auto_pitch(mesh):
    """A resolution that solves in a few seconds, from the part's solid volume."""
    volume = abs(float(mesh.volume)) or 1.0
    return float(min(3.0, max(0.8, (volume / 15000.0) ** (1 / 3))))


def _voxel_model(shape, mesh, pitch):
    """Voxel FEM material, preserving voids enclosed by the part.

    Trimesh first voxelizes only the boundary. Its ordinary ``fill()`` then uses a
    binary hole fill, which cannot distinguish solid interior from a sealed cavity.
    Instead, label the empty regions separated by that boundary and ask OCCT about one
    representative from each. Material regions fill; exterior space and voids stay
    empty. Boundary voxels stay because thin printable walls may have no cell center
    strictly inside them at this pitch.
    """
    import trimesh
    from scipy import ndimage

    vox = mesh.voxelized(pitch)
    surface = np.asarray(vox.matrix, dtype=bool).copy()
    regions, _ = ndimage.label(~surface)
    labels, first = np.unique(regions, return_index=True)
    nonzero = labels != 0
    labels, first = labels[nonzero], first[nonzero]
    representatives = np.column_stack(np.unravel_index(first, regions.shape))
    xyz = trimesh.transform_points(representatives, vox.transform)
    inside = np.fromiter(
        (shape.is_inside(tuple(point)) for point in xyz),
        dtype=bool,
        count=len(representatives),
    )
    filled = surface | np.isin(regions, labels[inside])
    origin = vox.transform[:3, 3] - pitch / 2
    return _Voxels(filled, pitch, origin)


def analyze(shape, hold, load, kg, tolerance=0.1, pitch=None, material="PLA", up=(0, 0, 1)):
    """Stress in `shape` from `kg` pressing down on the face at `load`, held at `hold`.

    `hold` is a list of points, one per spot that carries the part: a shelf on wall
    brackets is held at each hook, and fixing one big back face instead would hide the
    stress at the joints, which is where a print actually fails.

    `up` is the print orientation, the direction layers stack in. The tension across
    that plane is checked against the material's layer adhesion separately from the
    bulk yield, because a print whose load peels its layers apart fails well before
    the plastic itself would, and one whose load runs along the grain does not.

    Returns per-vertex stress in the exact vertex order `builder._triangulate` produces
    at this tolerance, which is the order the viewer's GLB holds, plus the summary
    numbers. Raises ValueError with a user-facing sentence for everything expected.
    """
    import trimesh

    from . import builder

    if not kg or kg <= 0:
        raise ValueError("the load has to be a positive weight in kg")
    if not hold:
        raise ValueError("say at least one spot where the part is held")
    material, props = material_named(material)
    if getattr(shape, "_nurb_scene", None) is not None:
        raise ValueError("stress runs on one solid part; pick one of the parts this assembly places")

    points, tris, _ = builder._triangulate(shape, tolerance)
    if not points:
        raise ValueError("this part has no geometry to analyze")
    mesh = trimesh.Trimesh(
        vertices=np.asarray(points, float), faces=np.asarray(tris, np.int64), process=False
    )
    if pitch is None:
        pitch = _auto_pitch(mesh)
    model = _voxel_model(shape, mesh, pitch)
    if not len(model.elems):
        raise ValueError("the part voxelized to nothing; it may be thinner than the analysis grid")

    load_face = face_at(shape, load)
    hold_faces = []
    for point in hold:
        face = face_at(shape, point)
        if face.is_same(load_face):
            raise ValueError("the weight and a hold landed on the same face; pick two different spots")
        if not any(face.is_same(seen) for seen in hold_faces):
            hold_faces.append(face)
    fixed = np.unique(np.concatenate([_face_nodes(f, model) for f in hold_faces])).astype(np.int64)
    loaded = _face_nodes(load_face, model)
    if not len(fixed) or not len(loaded):
        raise ValueError("a picked face is thinner than the analysis grid; pick a larger face")

    u = model.solve(fixed, loaded, (0.0, 0.0, -kg * GRAVITY), E=props["E"])
    vm, tensor = model.stresses(u, E=props["E"])

    # Tension across the layer plane: n.sigma.n with n the stacking direction, kept
    # only where positive, because layers part under pull and shrug off being pressed.
    n = np.asarray(up, float)
    n = n / (np.linalg.norm(n) or 1.0)
    across = (
        tensor[:, 0] * n[0] ** 2 + tensor[:, 1] * n[1] ** 2 + tensor[:, 2] * n[2] ** 2
        + 2 * (tensor[:, 3] * n[0] * n[1] + tensor[:, 4] * n[1] * n[2] + tensor[:, 5] * n[2] * n[0])
    )
    across_max = float(np.maximum(across, 0.0).max())

    # Element stress onto the display mesh: each vertex reads its nearest element.
    from scipy.spatial import cKDTree

    _, nearest = cKDTree(model.centers).query(np.asarray(points, float))
    per_vertex = vm[nearest]

    peak = int(np.argmax(vm))
    max_mpa = float(vm[peak])
    # Load multiples to each failure: the plastic yielding, and the layer seams
    # parting. Whichever is smaller is how this print actually breaks.
    yield_factor = props["yield"] / max_mpa if max_mpa > 1e-9 else None
    layer_factor = props["layer"] / across_max if across_max > 1e-9 else None
    candidates = [(f, mode) for f, mode in ((yield_factor, "plastic"), (layer_factor, "layers")) if f]
    factor, gives = min(candidates) if candidates else (None, None)
    return {
        "values": [round(float(v), 4) for v in per_vertex],
        "max_mpa": round(max_mpa, 3),
        "across_mpa": round(across_max, 3),
        "hotspot": [round(float(c), 1) for c in model.centers[peak]],
        "deflection_mm": round(float(-u[2::3].min()), 4),
        "material": material,
        "factor": round(factor, 1) if factor else None,
        "gives": gives,
        "yield_factor": round(yield_factor, 1) if yield_factor else None,
        "layer_factor": round(layer_factor, 1) if layer_factor else None,
        "kg": kg,
        "pitch": round(float(pitch), 2),
        "elements": int(len(model.elems)),
        "hold_centers": [[round(float(v), 1) for v in tuple(f.center())] for f in hold_faces],
        "load_center": [round(float(v), 1) for v in tuple(load_face.center())],
    }


def default_spots(shape):
    """(holds, load) points for a run nobody aimed: the largest downward or side face
    holds the part, and the highest big upward face takes the weight. The CLI names
    both choices, so a wrong guess is visible and a point override is one flag away."""
    faces = shape.faces()
    if not faces:
        raise ValueError("this part has no faces to analyze")

    def upward(f):
        try:
            return f.normal_at(f.center()).Z > 0.7
        except Exception:
            return False

    # A part is held from below or behind and loaded from above, so the hold never
    # competes with the load for the same face.
    down = [f for f in faces if not upward(f)]
    if not down:
        raise ValueError("no face to hold this part by; say where with --hold x,y,z")
    hold = max(down, key=lambda f: f.area)
    up = [f for f in faces if upward(f)]
    if not up:
        raise ValueError(
            "no upward face to load; say where the weight sits with --at x,y,z"
        )
    # The largest upward face, not the highest: things rest on shelves, arms, bin
    # floors and hook bars, and on a wall-hung part the highest face is usually the
    # top of the wall plate, which carries nothing.
    load = max(up, key=lambda f: f.area)
    return [tuple(hold.center())], tuple(load.center())
