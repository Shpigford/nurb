"""A 3MF read into triangles, with the standard library.

3MF is what slicers save and what most model sites offer next to STL, and trimesh
reads it only with networkx installed. A dependency is not worth one format whose
geometry is a zip of XML: a build lists items, an item names an object, and an object
is either a mesh or components pointing at other objects, each with a transform.
Bambu Studio and Orca keep the meshes in `3D/Objects/*.model` and point at them from
the root model through the production extension's `path`, so a component's object is
looked up in whichever file it names.

Colours, materials, slice settings and thumbnails are all ignored. What comes back is
the shape, in millimetres, one mesh per build item.
"""

import pathlib
import posixpath
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

# Millimetres per unit, for the units the core spec allows. Millimetre is its default.
UNITS = {
    "micron": 0.001,
    "millimeter": 1.0,
    "centimeter": 10.0,
    "inch": 25.4,
    "foot": 304.8,
    "meter": 1000.0,
}

ROOT = "3D/3dmodel.model"
MODEL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
# Deep enough for any real assembly, shallow enough that a file whose components
# name each other in a loop stops instead of recursing until Python does.
DEPTH = 32


def items(path):
    """(name, trimesh) for each build item, placed where the build puts it, in mm."""
    import trimesh

    path = pathlib.Path(path)
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ValueError(f"{path.name} is not a 3MF: it does not open as a zip") from None
    with archive:
        reader = _Reader(archive)
        root = reader.root()
        _, scale, _ = reader.model(root)
        names = reader.names()
        out = []
        for item in _children(reader.model(root)[0], "build", "item"):
            transform = _transform(item.get("transform"))
            transform[3] *= scale
            parts = reader.triangles(_path(item, root), item.get("objectid"), transform, 0)
            if not parts:
                continue
            verts = np.concatenate([v for v, _ in parts])
            offsets = np.cumsum([0] + [len(v) for v, _ in parts[:-1]])
            faces = np.concatenate([f + o for (_, f), o in zip(parts, offsets)])
            name = names.get(item.get("objectid")) or f"object {item.get('objectid')}"
            out.append((name, trimesh.Trimesh(vertices=verts, faces=faces, process=False)))
    if not out:
        raise ValueError(f"{path.name} has no triangles to measure: its build is empty")
    return out


class _Reader:
    def __init__(self, archive):
        self.archive = archive
        self.files = {}

    def root(self):
        """The model the package's relationships name, which is nearly always ROOT."""
        try:
            rels = ET.fromstring(self.archive.read("_rels/.rels"))
        except (KeyError, ET.ParseError):
            return ROOT
        for rel in rels:
            if rel.get("Type") == MODEL:
                return rel.get("Target", ROOT).lstrip("/")
        return ROOT

    def model(self, name):
        """(the parsed model, mm per unit, its objects by id), parsed once per file."""
        if name not in self.files:
            try:
                tree = ET.fromstring(self.archive.read(name))
            except KeyError:
                raise ValueError(f"the 3MF names {name}, which is not in it") from None
            except ET.ParseError as exc:
                raise ValueError(f"{name} inside the 3MF is not readable XML: {exc}") from None
            unit = tree.get("unit", "millimeter")
            if unit not in UNITS:
                raise ValueError(f"the 3MF is in {unit!r}, which is not a 3MF unit")
            objects = {o.get("id"): o for o in _children(tree, "resources", "object")}
            self.files[name] = (tree, UNITS[unit], objects)
        return self.files[name]

    def names(self):
        """Object names, from the core `name` attribute or the slicer's own settings."""
        tree, _, objects = self.model(self.root())
        names = {id: o.get("name") for id, o in objects.items() if o.get("name")}
        try:
            settings = ET.fromstring(self.archive.read("Metadata/model_settings.config"))
        except (KeyError, ET.ParseError):
            return names
        for obj in settings.iter("object"):
            for meta in obj.iter("metadata"):
                if meta.get("key") == "name" and meta.get("value"):
                    names.setdefault(obj.get("id"), meta.get("value"))
                    break
        return names

    def triangles(self, file, object_id, transform, depth):
        """(vertices, faces) pairs for one object, with every transform above it applied."""
        if depth > DEPTH:
            raise ValueError("the 3MF's components refer to each other in a loop")
        _, scale, objects = self.model(file)
        obj = objects.get(object_id)
        if obj is None:
            raise ValueError(f"the 3MF refers to object {object_id}, which {file} does not define")
        mesh = _child(obj, "mesh")
        if mesh is not None:
            verts = np.array(
                [(v.get("x"), v.get("y"), v.get("z")) for v in _children(mesh, "vertices", "vertex")],
                dtype=np.float64,
            ).reshape(-1, 3)
            faces = np.array(
                [(t.get("v1"), t.get("v2"), t.get("v3")) for t in _children(mesh, "triangles", "triangle")],
                dtype=np.int64,
            ).reshape(-1, 3)
            if not len(faces):
                return []
            # The unit is the file's own, so it scales the mesh before any transform:
            # a transform's translation is in the units of the file that holds it.
            verts = verts * scale
            return [(verts @ transform[:3] + transform[3], faces)]
        out = []
        for component in _children(obj, "components", "component"):
            child = _transform(component.get("transform"))
            # A component's translation is in its parent's file units.
            child[3] *= scale
            combined = np.vstack([child[:3] @ transform[:3], child[3] @ transform[:3] + transform[3]])
            out += self.triangles(_path(component, file), component.get("objectid"), combined, depth + 1)
        return out


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _child(node, name):
    return next((c for c in node if _local(c.tag) == name), None)


def _children(node, group, name):
    holder = _child(node, group)
    return [] if holder is None else [c for c in holder if _local(c.tag) == name]


def _path(node, default):
    """The production extension's `path`, or the file the node sits in."""
    for key, value in node.attrib.items():
        if _local(key) == "path":
            return posixpath.normpath(value).lstrip("/")
    return default


def _transform(text):
    """A 3MF transform as a 4x3 matrix that a row of points multiplies from the left."""
    if not text:
        return np.vstack([np.eye(3), np.zeros(3)])
    values = [float(v) for v in text.split()]
    if len(values) != 12:
        raise ValueError(f"a 3MF transform has 12 numbers, not {len(values)}")
    return np.array(values, dtype=np.float64).reshape(4, 3)
