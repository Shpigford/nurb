"""Load a part file, build it, turn it into something a browser can show."""

import importlib.util
import pathlib
import sys
import time

import numpy as np
import trimesh


class BuildError(Exception):
    pass


class UnknownParams(BuildError):
    """An override named a parameter the part does not declare.

    Its own type because the viewer has to tell this apart from a real build failure:
    a slider left on a parameter that a later edit renamed is the file moving on, not
    the part breaking, and reporting it as a broken part names a parameter the user
    never typed.
    """

    def __init__(self, names):
        self.names = sorted(names)
        super().__init__(f"unknown parameter(s): {', '.join(self.names)}")


def _in_project(module, root):
    """A module the project owns, as opposed to one installed into its venv.

    The venv usually sits inside the project, so location alone would call every
    installed package a project module and re-import it on every rebuild.
    """
    file = getattr(module, "__file__", None)
    if not file:
        return False
    path = pathlib.Path(file)
    return path.is_relative_to(root) and "site-packages" not in path.parts


def load(path):
    """Import a part file fresh and return its @part function."""
    path = pathlib.Path(path).resolve()
    root = path.parent.parent if path.parent.name == "parts" else path.parent
    modname = f"_nurb_part_{path.stem}_{time.time_ns()}"
    spec = importlib.util.spec_from_file_location(modname, path)
    if spec is None or spec.loader is None:
        raise BuildError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    written = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # keep __pycache__ out of the user's parts/
    sys.path.insert(0, str(root))  # so a part can `from system import ...`
    known = set(sys.modules)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = written
        sys.path.remove(str(root))
        # Forget the project's own modules, so editing a shared one lands on the
        # next rebuild instead of the next restart.
        for name in set(sys.modules) - known:
            if _in_project(sys.modules[name], root):
                del sys.modules[name]
        sys.modules.pop(modname, None)

    for value in vars(mod).values():
        if callable(value) and hasattr(value, "_nurb"):
            return value
    raise BuildError(f"no @part function in {path.name}")


def _kind(value):
    """What control this parameter can carry.

    Read off the declared default, never off the current value: a float parameter whose
    slider happens to be sitting on 2 would otherwise report `int` and come back after a
    reload with an integer slider, which is the distinction this exists to preserve.

    bool before int, because bool is an int subclass and a checkbox is not a slider.
    """
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "other"


def _safe(value):
    """A parameter value the payload can carry.

    A default can be any Python object, and one that json cannot encode would take the
    whole websocket message down with it rather than just its own row.
    """
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return repr(value)


def build(path, overrides=None, draft=False):
    """Build a part. Returns (shape, params, milliseconds).

    `params` is one row per parameter: what the file declares, what this build used,
    and what kind of control it can carry. The keyword defaults are the parameters, so
    this list is derived, never declared.
    """
    fn = load(path)
    defn = fn._nurb
    kwargs = dict(defn.params)
    if overrides:
        unknown = set(overrides) - set(kwargs)
        if unknown:
            raise UnknownParams(unknown)
        kwargs.update(overrides)
    call = dict(kwargs)
    if defn.accepts_draft:
        call["draft"] = draft

    started = time.perf_counter()
    shape = fn(**call)
    elapsed = (time.perf_counter() - started) * 1000
    if shape is None:
        raise BuildError(f"{defn.name}() returned None")

    params = [
        {
            "name": name,
            "default": _safe(default),
            "value": _safe(kwargs[name]),
            "kind": _kind(default),
            "doc": defn.docs.get(name),
        }
        for name, default in defn.params.items()
    ]
    return shape, params, elapsed


def _triangulate(shape, tolerance):
    """Vertices and triangles, read straight out of OCCT.

    This is what `Shape.tessellate` does, and it exists because of one line in it.
    build123d reads the triangles with `for t in poly.Triangles()`, and OCP's iterator
    over that array is pathological: measured on the gridfinity shelf, the same 7790
    triangles cost 536ms to iterate and 6.8ms to read by index. Meshing itself is 10ms.
    So the loop's dominant cost was never geometry, it was an iterator, and Phase 1's
    "tessellation is the loop" conclusion was measuring this.

    Everything else here matches `tessellate` deliberately, including the winding flip
    on a reversed face and the per-face vertex offset.
    """
    from OCP.BRep import BRep_Tool
    from OCP.TopAbs import TopAbs_Orientation
    from OCP.TopLoc import TopLoc_Location

    shape.mesh(tolerance)
    points, faces, offset = [], [], 0
    for face in shape.faces():
        loc = TopLoc_Location()
        poly = BRep_Tool.Triangulation_s(face.wrapped, loc)
        if poly is None:  # a face OCCT declined to triangulate takes no vertices with it
            continue
        trsf = loc.Transformation()
        reverse = face.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED
        for i in range(1, poly.NbNodes() + 1):
            node = poly.Node(i).Transformed(trsf)
            points.append((node.X(), node.Y(), node.Z()))
        triangles = poly.Triangles()
        for i in range(1, poly.NbTriangles() + 1):
            tri = triangles.Value(i)
            a, b, c = tri.Value(1), tri.Value(2), tri.Value(3)
            if reverse:
                b, c = c, b
            faces.append((a + offset - 1, b + offset - 1, c + offset - 1))
        offset += poly.NbNodes()
    return points, faces


def to_mesh(shape, tolerance=0.1):
    """Tessellate to a triangle mesh.

    process=False matters: OCCT already splits vertices at face boundaries, which
    is exactly the layout we want (crisp edges, smooth curves). Letting trimesh
    weld them merges the box corners and smears the normals across perpendicular
    faces, which renders as a shadeless blob.
    """
    points, faces = _triangulate(shape, tolerance)
    mesh = trimesh.Trimesh(
        vertices=np.array(points, dtype=np.float64),
        faces=np.array(faces, dtype=np.int64),
        process=False,
    )
    mesh.vertex_normals  # populate before export, or the GLB ships without normals
    return mesh


def to_glb(shape, tolerance=0.1):
    """One GLB. A part is one blob; an assembly keeps its movers as named nodes.

    The scene rides on the compound the same way checks.run reads it: an attribute,
    not an import, so this file stays ignorant of how assemblies work. The node
    names are the contract with the viewer -- `joint<i>` for each hinged solid in
    declaration order, `fixed` for everything static, `context` for obstacles --
    which is what lets a slider pose a joint client-side without a rebuild.
    """
    scene = getattr(shape, "_nurb_scene", None)
    if scene is None:
        return trimesh.Scene([to_mesh(shape, tolerance)]).export(file_type="glb")
    from .assembly import NODE

    out = trimesh.Scene()
    for i, h in enumerate(scene.hinges):
        name = NODE.format(i)
        out.add_geometry(to_mesh(h.solid, tolerance), node_name=name, geom_name=name)
    for name, group in (("fixed", scene.statics), ("context", scene.obstacles)):
        if group:
            merged = trimesh.util.concatenate([to_mesh(s, tolerance) for s in group])
            out.add_geometry(merged, node_name=name, geom_name=name)
    return out.export(file_type="glb")


def stats(shape):
    bb = shape.bounding_box()
    return {
        "bbox": [round(bb.size.X, 2), round(bb.size.Y, 2), round(bb.size.Z, 2)],
        "volume": round(shape.volume, 1),
    }


def find_parts(root):
    """Every part file in a project."""
    parts_dir = pathlib.Path(root) / "parts"
    if not parts_dir.is_dir():
        return []
    return sorted(p for p in parts_dir.glob("*.py") if not p.name.startswith("_"))
