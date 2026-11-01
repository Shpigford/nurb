"""The one document a model reads before it writes a part: doctrine, vocabulary, kernel.

Assembled at call time rather than cached, because the doctrine and the vocabulary are
the tool's own files and a stale copy would teach the wrong rules after an upgrade.
"""

import pathlib

from . import __version__

DOCTRINE = pathlib.Path(__file__).with_name("doctrine.md")

# Both sections describe work this contract has no tool for, so they would read as
# instructions the model cannot follow.
DROPPED = ("Cards", "Assemblies")

PREAMBLE = (
    "The doctrine below is binding, not advice; call get_project before you write part "
    "source so you edit what is there rather than what you remember."
)

# Every line was measured against build123d 0.11.1, which is what nurb pins. A part
# file has no shell to read site-packages with, so the reference rides in the guide.
BUILD123D_SHEET = """# build123d reference

`from nurb import *` gives a part file the vocabulary above plus all of build123d in
algebra mode. Use only names listed here or above. Never assume a signature: a wrong
guess costs a build. Everything is millimetres, +Z is up, the bed is Z=0.

Solids (centred on the origin unless align says otherwise):
  Box(length, width, height, align=Align.CENTER)    length is X, width is Y, height is Z
  Cylinder(radius, height, align=Align.CENTER)      axis along Z
  Cone(bottom_radius, top_radius, height)           Sphere(radius)
  align=Align.MIN puts the shape's minimum corner at the origin. Per axis:
  Box(10, 20, 5, align=(Align.CENTER, Align.MIN, Align.MIN))

Sketches are 2D on Plane.XY and become solids by extruding:
  Rectangle(width, height)   Circle(radius)   Polygon(*pts, align=None)   pts are (x, y)
  make_face(Polyline((0, 0), (10, 0), (10, 5), (0, 0)))   a closed polyline as a face
  extrude(sketch, amount)          along the sketch plane's normal, +Z for Plane.XY
  extrude(sketch, amount, both=True)   revolve(sketch, axis=Axis.Y)   loft([a, b])
  Draw a side profile on another plane, then extrude across:
    Plane.YZ * Polygon(...)   local (x, y) land on world (Y, Z); extrude runs along +X
    Plane.XZ * Polygon(...)   local (x, y) land on world (X, Z); extrude runs along -Y
  Plane.XY.offset(d) shifts a plane along its normal by d.

Placing (transforms compose right to left: the one nearest the shape applies first):
  Pos(x, y, z) * shape                   translate
  Rot(x_deg, y_deg, z_deg) * shape       rotate about the world axes through the origin
  Pos(0, 0, 10) * Rot(0, 0, 45) * shape  rotate, then lift
  Rot(Axis.Y, 90) is WRONG: build123d accepts it and silently rotates about X. Write
  Rot(0, 90, 0). Never pass an Axis to Rot.
  Box(10, 2, 1, rotation=(0, 0, 90)) rotates a primitive as it is made.

Booleans: a + b union, a - b cut, a & b intersect. A part must end as one solid:
  len(body.solids()) == 1. Overlap unions; touching at an edge is not joined.

Measuring and selecting (these are all methods with parentheses):
  bb = shape.bounding_box(); bb.min.Z, bb.max.X, bb.size.Y, bb.center().Z
  face.center(), face.area, face.normal_at(), edge.length, shape.volume
  shape.faces().filter_by(Axis.Z)    faces whose normal is parallel to Z
  shape.edges().filter_by(Axis.Z)    edges parallel to Z
  shape.faces().sort_by(Axis.Z)[-1]  the top face; [0] the bottom
  shape.edges().group_by(Axis.Z)[-1] the edges at the top
  .filter_by(lambda e: e.length > 5) any callable works
  new_edges(a, b, combined=a + b)    the edges a boolean created
  concave_edges(shape) returns a plain list: wrap it, ShapeList(concave_edges(shape)),
  before calling filter_by or sort_by on it.

Edges: fillet(edges, radius), chamfer(edges, size), polish(shape, edges, size).
Also available: split(shape, bisect_by=Plane.XY, keep=Keep.TOP), mirror(shape,
about=Plane.YZ), offset(shape, amount), Location, Vector, Axis.X/Y/Z, Hole,
CounterBoreHole, SlotCenterToCenter, RegularPolygon, Text.
"""


def condensed_doctrine():
    text = DOCTRINE.read_text(encoding="utf-8").strip()
    sections = []
    for section in _split_sections(text):
        if any(section.startswith(f"## {title}\n") for title in DROPPED):
            continue
        sections.append(section)
    return "".join(sections).strip()


def _split_sections(text):
    """The doctrine split before each `## ` heading, preamble first."""
    sections, current = [], []
    for line in text.splitlines(keepends=True):
        if line.startswith("## ") and current:
            sections.append("".join(current))
            current = []
        current.append(line)
    if current:
        sections.append("".join(current))
    return sections


def text():
    from . import api

    return "\n\n".join(
        [
            f"# nurb {__version__} guide",
            PREAMBLE,
            condensed_doctrine(),
            "# nurb vocabulary\n" + "\n".join(api.report()),
            BUILD123D_SHEET.strip(),
        ]
    )
