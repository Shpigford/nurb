"""Load a part file, build it, turn it into something a browser can show."""

import importlib.util
import pathlib
import sys
import time

import numpy as np
import trimesh

from . import supports
from .registry import Rejected


class BuildError(Exception):
    pass


# What a bridge surface multiplies the part color by in the viewer. Blue, because that
# is what every slicer's preview paints bridges, so the association is already learned.
BRIDGE_TINT = (89, 166, 255, 255)


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

    started = time.perf_counter()
    try:
        # `supported()` marks cannot ride on the geometry, because the booleans that
        # follow build new solids. They are collected around the call instead and hung
        # on the result, the same way an assembly carries its scene.
        with supports.collecting() as marked:
            shape = fn(**call)
    except Rejected as exc:
        # A refused build still needs to describe the attempted values: they are the
        # controls the viewer offers to get back into the part's valid range.
        exc.params = params
        raise
    elapsed = (time.perf_counter() - started) * 1000
    if shape is None:
        raise BuildError(f"{defn.name}() returned None")
    if marked:
        shape._nurb_supported = tuple(marked)

    return shape, params, elapsed


def _triangulate(shape, tolerance, up=(0, 0, 1)):
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
    from build123d import GeomType, Vector
    from OCP.BRep import BRep_Tool
    from OCP.TopAbs import TopAbs_Orientation
    from OCP.TopLoc import TopLoc_Location

    shape.mesh(tolerance)
    up = Vector(*up).normalized()
    # Flat ceilings above the bed get tinted, the way a slicer previews bridges: these
    # are the surfaces the printer lays on air, and they are otherwise invisible in a
    # shaded render. This is how a stepped counterbore shows its work: the sacrificial
    # shelves light up where a naive pocket shows one floating ceiling. The colors are
    # multipliers over the viewer's material, so white is "no tint". Classified off the
    # triangulation's own nodes in a second pass, never off bounding_box(): that call
    # quietly destroys the cached triangulation, at shape and face level both, and the
    # symptom is an empty mesh with no error anywhere.
    points, faces, ceilings, offset = [], [], [], 0
    for face in shape.faces():
        loc = TopLoc_Location()
        poly = BRep_Tool.Triangulation_s(face.wrapped, loc)
        if poly is None:  # a face OCCT declined to triangulate takes no vertices with it
            continue
        try:
            flat_ceiling = (
                face.geom_type == GeomType.PLANE
                and face.normal_at(face.center()).dot(up) < -0.97
            )
        except Exception:
            flat_ceiling = False
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
        if flat_ceiling:
            ceilings.append((offset, poly.NbNodes()))
        offset += poly.NbNodes()
    colors = [(255, 255, 255, 255)] * len(points)
    if points:
        def height(p):
            return p[0] * up.X + p[1] * up.Y + p[2] * up.Z

        bed = min(height(p) for p in points)
        for start, count in ceilings:
            if min(height(points[i]) for i in range(start, start + count)) > bed + 1e-4:
                colors[start : start + count] = [BRIDGE_TINT] * count
    return points, faces, colors


def face_triangles(face):
    """One face's triangles, as a flat vertex list ready for a BufferGeometry.

    Read the way `_triangulate` reads, from the triangulation OCCT already cached:
    every shape this is asked about was tessellated whole on its way to the viewer, so
    an empty answer means a face OCCT declined, not a missing meshing pass.
    """
    from OCP.BRep import BRep_Tool
    from OCP.TopAbs import TopAbs_Orientation
    from OCP.TopLoc import TopLoc_Location

    loc = TopLoc_Location()
    poly = BRep_Tool.Triangulation_s(face.wrapped, loc)
    if poly is None:
        return []
    trsf = loc.Transformation()
    reverse = face.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED
    nodes = []
    for i in range(1, poly.NbNodes() + 1):
        node = poly.Node(i).Transformed(trsf)
        nodes.append((node.X(), node.Y(), node.Z()))
    out = []
    triangles = poly.Triangles()
    for i in range(1, poly.NbTriangles() + 1):
        tri = triangles.Value(i)
        a, b, c = tri.Value(1), tri.Value(2), tri.Value(3)
        if reverse:
            b, c = c, b
        for corner in (a, b, c):
            out.extend(nodes[corner - 1])
    return out


def to_mesh(shape, tolerance=0.1, up=(0, 0, 1)):
    """Tessellate to a triangle mesh.

    process=False matters: OCCT already splits vertices at face boundaries, which
    is exactly the layout we want (crisp edges, smooth curves). Letting trimesh
    weld them merges the box corners and smears the normals across perpendicular
    faces, which renders as a shadeless blob.
    """
    points, faces, colors = _triangulate(shape, tolerance, up)
    mesh = trimesh.Trimesh(
        vertices=np.array(points, dtype=np.float64).reshape(-1, 3),
        faces=np.array(faces, dtype=np.int64).reshape(-1, 3),
        vertex_colors=np.array(colors, dtype=np.uint8).reshape(-1, 4),
        process=False,
    )
    # A part whose last cut removed everything tessellates to nothing, and asking
    # trimesh for normals over zero triangles raises out of numpy rather than
    # returning an empty answer. The `solids` rule has words for this part; a
    # dev-loop traceback from inside the mesher is not those words.
    if len(mesh.faces):
        mesh.vertex_normals  # populate before export, or the GLB ships without normals
    return mesh


def to_glb(shape, tolerance=0.1, up=(0, 0, 1)):
    """One GLB. A part is one blob; an assembly keeps its movers as named nodes.

    The scene rides on the compound the same way checks.run reads it: an attribute,
    not an import, so this file stays ignorant of how assemblies work. The node
    names are the contract with the viewer -- `joint<i>` for each hinged solid in
    declaration order, `fixed` for everything static, `context` for obstacles --
    which is what lets a slider pose a joint client-side without a rebuild.
    """
    scene = getattr(shape, "_nurb_scene", None)
    if scene is None:
        return trimesh.Scene([to_mesh(shape, tolerance, up)]).export(file_type="glb")
    from .assembly import NODE

    out = trimesh.Scene()
    for i, h in enumerate(scene.hinges):
        name = NODE.format(i)
        out.add_geometry(to_mesh(h.solid, tolerance, up), node_name=name, geom_name=name)
    for name, group in (("fixed", scene.statics), ("context", scene.obstacles)):
        if group:
            merged = trimesh.util.concatenate([to_mesh(s, tolerance, up) for s in group])
            out.add_geometry(merged, node_name=name, geom_name=name)
    return out.export(file_type="glb")


def write_stl(shape, target):
    """Write an STL meshed for printing rather than for archival.

    build123d's export_stl defaults to 1e-3mm linear deflection, an order finer than
    a nozzle reproduces: issue #55's 145x364mm tray meshed to 97k triangles and
    4.7MB, and the slicer turned the micro-segments into constant braking along the
    walls. A 0.01mm chord error is invisible at FDM scale and cuts the mesh to a
    fraction.
    """
    from build123d import export_stl

    export_stl(shape, str(target), tolerance=0.01, angular_tolerance=0.2)


def write_3mf(shape, target):
    """Write a 3MF from the same tessellation the viewer and the STL already use.

    Unlike STL the file names its unit, so a slicer never has to guess the scale.
    lib3mf rides along with build123d, so this costs no dependency.

    Deliberately not build123d's `Mesher.add_shape`, which re-meshes the shape and
    then refuses to write anything whose triangulation is not manifold. OCCT leaves
    the odd seam crack on a curved face, so that check turns one four-edge hole into
    a dead export ("3mf mesh is invalid") with nothing the user can do about it. The
    STL has always carried the same holes and every slicer repairs them on load, so
    a 3MF that matches the STL is the honest file to write. Verified by slicing one:
    Bambu Studio takes the cracked mesh and prices it exactly as it does the STL.
    """
    import lib3mf
    from build123d import Mesher

    target = pathlib.Path(target)
    mesh = to_mesh(shape, 0.01)
    # A 3MF indexes shared vertices, while `to_mesh` splits them per face to keep the
    # viewer's edges crisp. Rebuilding welds them, which is both what the format wants
    # and a third off the file size.
    welded = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=True)
    # lib3mf will happily write an empty model, and a downloaded file that opens to an
    # empty plate is worse than a refusal: it looks like it worked. A part that
    # tessellates to nothing is what the `solids` rule is for, so say that.
    if not len(welded.faces):
        target.unlink(missing_ok=True)
        raise BuildError(f"{target.stem} has no geometry to export; `nurb check` says why")
    # Mesher is still what owns the lib3mf handle, the millimetre unit and the write,
    # so the platform's library layout stays build123d's problem. Only its meshing and
    # its validity gate are skipped.
    mesher = Mesher()
    obj = mesher.model.AddMeshObject()
    obj.SetGeometry(
        [lib3mf.Position(Coordinates=(x, y, z)) for x, y, z in welded.vertices.tolist()],
        [lib3mf.Triangle(Indices=(a, b, c)) for a, b, c in welded.faces.tolist()],
    )
    obj.SetType(lib3mf.ObjectType.Model)
    mesher.model.AddBuildItem(obj, mesher.wrapper.GetIdentityTransform())
    mesher.write(str(target))


def stl_triangles(target):
    """Triangle count of a binary STL, from the header."""
    with open(target, "rb") as f:
        f.seek(80)
        return int.from_bytes(f.read(4), "little")


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
