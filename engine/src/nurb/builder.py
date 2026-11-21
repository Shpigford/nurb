"""Load a part file, build it, turn it into something a browser can show."""

import copy
import importlib.util
import pathlib
import sys
import time

import numpy as np
import trimesh


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
    if isinstance(value, str):
        return "str"
    return "other"


def _safe(value):
    """A parameter value the payload can carry.

    A default can be any Python object, and one that json cannot encode would take the
    whole websocket message down with it rather than just its own row.
    """
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return repr(value)


def describe(defn, values):
    """One row per parameter: what the file declares, what a build uses, what control it
    can carry. The keyword defaults are the parameters, so this is derived, never
    declared, and it needs no build: a part the kernel crashed on still gets its sliders."""
    rows = []
    for name, default in defn.params.items():
        row = {
            "name": name,
            "default": _safe(default),
            "value": _safe(values[name]),
            "kind": _kind(default),
            "doc": defn.docs.get(name),
        }
        if name in defn.choices:
            row["kind"] = "choice"
            row["options"] = defn.choices[name]
        elif name in defn.colors:
            row["kind"] = "color"
        rows.append(row)
    return rows


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

    params = describe(defn, kwargs)

    started = time.perf_counter()
    try:
        shape = fn(**call)
    except Exception as exc:
        # A refused or broken build still needs to describe the attempted values: they
        # are the controls the parameter panel offers to get back to a part that builds.
        exc._nurb_params = params
        raise
    elapsed = (time.perf_counter() - started) * 1000
    if shape is None:
        raise BuildError(f"{defn.name}() returned None")

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
        first, canon = {}, []
        for i in range(1, poly.NbNodes() + 1):
            node = poly.Node(i).Transformed(trsf)
            xyz = (node.X(), node.Y(), node.Z())
            points.append(xyz)
            # OCCT duplicates a node where a face meets itself (a cylinder's seam), and
            # which duplicate a triangle names differs between x86 and arm64. Naming the
            # first one everywhere keeps the GLB bytes the same on every machine.
            canon.append(first.setdefault(xyz, i))
        triangles = poly.Triangles()
        for i in range(1, poly.NbTriangles() + 1):
            tri = triangles.Value(i)
            a, b, c = canon[tri.Value(1) - 1], canon[tri.Value(2) - 1], canon[tri.Value(3) - 1]
            if reverse:
                b, c = c, b
            # OCCT can emit a triangle whose nodes are distinct indices at the
            # same xyz (a zero-area needle). Skip on the transformed points, not
            # on a==b: the measured failures already have three different indices.
            pa = points[offset + a - 1]
            pb = points[offset + b - 1]
            pc = points[offset + c - 1]
            if pa == pb or pb == pc or pc == pa:
                continue
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
    faces = np.array(faces, dtype=np.int64).reshape(-1, 3)
    if len(faces):
        # OCCT emits the same triangles on every platform but starts a triple at a
        # different corner on x86 than on arm64. Rotating each to its lowest index
        # (orientation intact) and sorting the list makes the GLB bytes, and so the
        # hash a desktop pushes and the hash the worker computes, one number.
        start = faces.argmin(axis=1)
        rows = np.arange(len(faces))
        faces = np.stack([faces[rows, (start + j) % 3] for j in range(3)], axis=1)
        faces = faces[np.lexsort(faces.T[::-1])]
    mesh = trimesh.Trimesh(
        vertices=np.array(points, dtype=np.float64).reshape(-1, 3),
        faces=faces,
        vertex_colors=np.array(colors, dtype=np.uint8).reshape(-1, 4),
        process=False,
    )
    # A part whose last cut removed everything tessellates to nothing, and asking
    # trimesh for normals over zero triangles raises out of numpy rather than
    # returning an empty answer. The `solids` rule has words for this part; a
    # dev-loop traceback from inside the mesher is not those words.
    if len(mesh.faces):
        # Populated before export, or the GLB ships without normals. Rounded because
        # the cross products behind them differ in the last bit between an arm64 Mac
        # and the x86 worker, and a GLB hash is only worth pushing if the desktop and
        # the worker compute the same one. `+ 0.0` turns a rounded -0.0 into 0.0.
        mesh.vertex_normals = np.round(mesh.vertex_normals, 6) + 0.0
    return mesh


def to_glb(shape, tolerance=0.1, up=(0, 0, 1)):
    """One GLB. A part is one blob, or one node per filament when it carries text or
    color; an assembly keeps its movers as named nodes.

    The scene rides on the compound the same way checks.run reads it: an attribute,
    not an import, so this file stays ignorant of how assemblies work. The node
    names are the contract with the viewer -- `joint<i>` for each hinged solid in
    declaration order, `fixed` for everything static, `context` for obstacles, and for
    a part `part`, `text`, and `color-<rrggbb>-<i>` for a body in its own color --
    which is what lets a slider pose a joint client-side without a rebuild.
    """
    scene = getattr(shape, "_nurb_scene", None)
    if scene is None:
        from .color import bodies

        split = bodies(shape)
        shown = getattr(shape, "_nurb_shown", None)
        if split is None and not shown:
            return trimesh.Scene([to_mesh(shape, tolerance, up)]).export(file_type="glb")
        # Each filament is its own node, so the viewer paints it. The meshes together
        # are the part: the base with its pockets, and what fills or stands on them.
        out = trimesh.Scene()
        for i, (color, body) in enumerate(split or [(None, shape)]):
            name = node_name(color, i)
            out.add_geometry(to_mesh(body, tolerance, up), node_name=name, geom_name=name)
        if shown:
            # What show_with() put beside the part is scenery, the same node an obstacle uses.
            context = trimesh.util.concatenate([to_mesh(s, tolerance, up) for s in shown])
            out.add_geometry(context, node_name="context", geom_name="context")
        return out.export(file_type="glb")
    from .assembly import NODE
    from .color import placed_bodies

    # A placed part keeps its colors and text, merged per color across the scene: the
    # viewer reads a node's paint from its name, so one node per color is enough.
    nodes = {}
    placed = [(NODE.format(i), h.solid) for i, h in enumerate(scene.hinges)]
    placed += [("fixed", s) for s in scene.statics]
    for name, solid in placed:
        for color, body in placed_bodies(solid) or [(None, solid)]:
            key = name if color is None else node_name(color, 0)
            nodes.setdefault(key, []).append(to_mesh(body, tolerance, up))
    if scene.obstacles:
        nodes["context"] = [to_mesh(s, tolerance, up) for s in scene.obstacles]
    out = trimesh.Scene()
    for name, meshes in nodes.items():
        out.add_geometry(trimesh.util.concatenate(meshes), node_name=name, geom_name=name)
    return out.export(file_type="glb")


def node_name(color, i):
    """The GLB node for one filament's body: see `to_glb`."""
    # Only the base can be uncolored, so "part" is never repeated.
    if color is None:
        return "part"
    if color == "text":
        return "text"
    return f"color-{color[1:]}-{i}"


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


def print_set(shape, bed=(256.0, 256.0, 256.0), gap=5.0):
    """What actually goes on the plate: one solid per physical part, laid out flat.

    A part is itself. An assembly is the parts it placed, each back in the orientation
    it was modelled to print in, because the assembled scene is for checking fit: its
    screw is threaded through its nut and its jaw stands on its clamping face, and a
    slicer handed that scene prints the pose instead of the parts. Repeats print as
    many times as they were placed; obstacles were never use()d, so they never print.

    Rows run along X and wrap at the bed's width, centred on the origin the way a
    single part is. A slicer that arranges on load will repack them, and one that
    does not still opens a plate with nothing overlapping.
    """
    from build123d import Pos

    scene = getattr(shape, "_nurb_scene", None)
    if scene is None:
        return [shape]
    out, x, y, row, width = [], 0.0, 0.0, 0.0, 0.0
    for instance in scene.instances:
        solid = instance.solid
        box = solid.bounding_box()
        if x and x + box.size.X > bed[0]:
            x, y, row = 0.0, y + row + gap, 0.0
        out.append((instance.path, (x - box.min.X, y - box.min.Y, -box.min.Z), solid))
        width = max(width, x + box.size.X)
        x += box.size.X + gap
        row = max(row, box.size.Y)
    depth = y + row
    from .color import moved as carried

    placed = []
    for path, (dx, dy, dz), solid in out:
        moved = carried(solid, Pos(dx - width / 2, dy - depth / 2, dz))
        moved.label = pathlib.Path(path).stem
        placed.append(moved)
    return placed


def by_filament(plate):
    """The plate split by filament, and the color each filament slot holds.

    Returns (entries, colors). An entry is a part in one color, or a list of
    (slot, body, name) for a part with text or colored regions: a 3MF object made of
    several parts is how Bambu Studio and OrcaSlicer put a region on its own filament
    and still keep it on the part. Written as separate objects, the slicer's arrange
    moves them about 25mm off the plate. `colors[i]` is slot i+1's "#rrggbb", or None
    for the slicer's own first filament; it is None when everything prints in one.
    """
    from .color import TEXT_COLOR, bodies, slots
    from .text import lettering

    split = [bodies(shape) for shape in plate]
    found = [c for s in split if s for c, _ in s]
    # A part in one color prints on the slicer's own first filament, so it keeps slot 1.
    if any(s is None for s in split):
        found.insert(0, None)
    colors = slots(found)
    out = []
    for shape, parts in zip(plate, split):
        if parts is None:
            out.append(shape)
            continue
        entry = []
        lettered = lettering(shape)
        letters = lettered.letters if lettered is not None else None
        for i, (color, body) in enumerate(parts):
            slot = colors.index(TEXT_COLOR if color == "text" else color) + 1
            name = (getattr(shape, "label", "") or "part") if i == 0 else ("text" if body is letters else f"color {slot}")
            body = copy.copy(body)
            entry.append((slot, body, name))
        out.append(entry)
    return out, (colors if len(colors) > 1 or (colors and colors[0]) else None)


def write_3mf(shape, target, colors=None):
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

    A plate entry that is a list of (slot, body, name) is one object whose bodies print
    on those filaments (see `by_filament`). Bambu Studio and OrcaSlicer use
    `Metadata/model_settings.config` for slot assignments. Base materials carry
    the chosen colors even when the file has no slicer project settings.
    """
    from xml.sax.saxutils import quoteattr

    import lib3mf
    from build123d import Mesher

    target = pathlib.Path(target)
    # A list is a plate of separate parts (see print_set), and each one stays its own
    # object: welded into one mesh, two parts that touch become one body that a
    # slicer's "split to objects" can no longer pull apart.
    entries = shape if isinstance(shape, list) else [shape]
    plate = []
    for entry in entries:
        bodies = entry if isinstance(entry, list) else [(1, entry, getattr(entry, "label", "") or "")]
        name = bodies[0][2]
        meshes = [(slot, _welded(b), n) for slot, b, n in bodies]
        meshes = [(slot, m, n) for slot, m, n in meshes if len(m.faces)]
        if meshes:
            plate.append((name, meshes))
    # lib3mf will happily write an empty model, and a downloaded file that opens to an
    # empty plate is worse than a refusal: it looks like it worked. A part that
    # tessellates to nothing is what the `solids` rule is for, so say that.
    if not plate:
        target.unlink(missing_ok=True)
        raise BuildError(f"{target.stem} has no geometry to export; the build's findings say why")
    # Mesher is still what owns the lib3mf handle, the millimetre unit and the write,
    # so the platform's library layout stays build123d's problem. Only its meshing and
    # its validity gate are skipped.
    mesher = Mesher()
    model, identity = mesher.model, mesher.wrapper.GetIdentityTransform()
    palette = {}
    if colors:
        materials = model.AddBaseMaterialGroup()
        material_id = materials.GetResourceID()
        for slot, color in enumerate(colors, start=1):
            if color is not None:
                rgba = mesher.wrapper.RGBAToColor(*bytes.fromhex(color[1:]), 255)
                palette[slot] = materials.AddMaterial(color, rgba)
    config = []
    for name, meshes in plate:
        objects = []
        for slot, welded, part_name in meshes:
            obj = model.AddMeshObject()
            obj.SetGeometry(
                [lib3mf.Position(Coordinates=(x, y, z)) for x, y, z in welded.vertices.tolist()],
                [lib3mf.Triangle(Indices=(a, b, c)) for a, b, c in welded.faces.tolist()],
            )
            obj.SetType(lib3mf.ObjectType.Model)
            if slot in palette:
                obj.SetObjectLevelProperty(material_id, palette[slot])
            if part_name:
                obj.SetName(part_name)
            objects.append((slot, obj))
        if len(objects) == 1 and objects[0][0] == 1:
            model.AddBuildItem(objects[0][1], identity)
            continue
        group = model.AddComponentsObject()
        if name:
            group.SetName(name)
        for _, obj in objects:
            group.AddComponent(obj, identity)
        model.AddBuildItem(group, identity)
        config.append(
            f'  <object id="{group.GetResourceID()}">\n    <metadata key="extruder" value="1"/>\n'
            + "".join(
                f'    <part id="{obj.GetResourceID()}" subtype="normal_part">\n'
                f'      <metadata key="name" value={quoteattr(obj.GetName())}/>\n'
                f'      <metadata key="extruder" value="{slot}"/>\n    </part>\n'
                for slot, obj in objects
            )
            + "  </object>\n"
        )
    if config:
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "".join(config) + "</config>\n"
        attachment = model.AddAttachment(
            "/Metadata/model_settings.config", "http://schemas.bambulab.com/package/2021/settings"
        )
        attachment.ReadFromBuffer(list(xml.encode()))
    mesher.write(str(target))


def _welded(shape):
    """The export tessellation with shared vertices, ready for lib3mf."""
    mesh = to_mesh(shape, 0.01)
    # A 3MF indexes shared vertices, while `to_mesh` splits them per face to keep the
    # viewer's edges crisp. Rebuilding welds them, which is both what the format wants
    # and a third off the file size.
    welded = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=True)
    # lib3mf SetGeometry rejects a triangle whose three indices are not unique.
    # Tessellation already dropped exact coincident corners; this is the weld's
    # own rule (it bins round(v*1e8), not Euclidean equality) and the last gate
    # before the C API.
    faces = welded.faces
    if len(faces):
        keep = (
            (faces[:, 0] != faces[:, 1])
            & (faces[:, 1] != faces[:, 2])
            & (faces[:, 2] != faces[:, 0])
        )
        if not keep.all():
            welded.update_faces(keep)
            welded.remove_unreferenced_vertices()
    return welded


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
