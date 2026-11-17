"""Text on a part: words a person types, drawn in a font nurb ships.

A system font builds different geometry on different machines, which is why the
doctrine kept text off parts. A font file shipped in the package does not: OCCT reads
its outlines with hinting off, so the same file and kernel give the same faces anywhere.
So `add_text` only ever draws with the fonts in `fonts/`, and refuses a name it does
not ship rather than letting build123d fall back to Arial without a word.

Raised and flush text keep the letters as their own body, so the viewer can show them
in a second colour and the 3MF can hand them to a second filament. The part itself is
still one solid, the base and letters fused: that is what prints, so it is what every
check judges.
"""

import dataclasses
import functools
import math
import pathlib
from dataclasses import dataclass

FONTS_DIR = pathlib.Path(__file__).parent / "fonts"

# The names a person picks from. Each is a bold weight, because a regular stroke is
# too thin to print at the sizes labels come in. Each was swept over every pair of
# letters for a mesh that closes. Standard is Liberation Sans, the Arial-metric face
# OpenSCAD's text() defaults to, so it is the lettering most customizer prints already
# use. Roboto, Inter, Montserrat and Lexend build invalid solids from overlapping
# outlines, and Open Sans cracked its mesh on pairs like "ee".
FONTS = {
    "Standard": "LiberationSans-Bold.ttf",
    "Heavy": "ArchivoBlack-Regular.ttf",
    "Stencil": "StardosStencil-Bold.ttf",
}

# Narrowest stroke as a fraction of the font size, measured off each file's lowercase
# "l" at mid-height (tests/test_text.py measures it again). A stroke is what fails
# first on a small letter, so this is what turns a size into a printability answer.
STROKE = {"Standard": 0.137, "Heavy": 0.199, "Stencil": 0.145}

STYLES = ("raised", "engraved", "flush")

# How far two touching glyphs grow before they are merged. Kerned pairs like "vy" or
# "AV" touch at a single point, and a solid that meets itself at a point tessellates
# with a crack the slicer has to repair. Grown this much they overlap by an area and
# fuse clean: every pair of letters in all three fonts, where 3 to 26 pairs per font
# cracked before.
GROW = 0.05
# The fitted text's clear space, as a share of the face's shorter side, and its floor in
# mm. A fixed 2mm put "PLA Silk" within a hair of the ring hole on a 20mm tag.
MARGIN = 0.2
MARGIN_MIN = 1.5
# The shortest run a flattened outline keeps, in mm.
SHORTEST = 0.01


@dataclass
class Lettering:
    """What `add_text` leaves on the part it returns, for colour and for the checks.

    `base` and `letters` together are the part: the base is everything that is not
    text, the letters are the text bodies. `blank` is the part before text, for cosmetic
    checks and wall probe origins. `structure` also keeps engraving cuts, so structural
    checks see the material left behind without treating added glyphs as walls.
    `smallest` is the size of the smallest text on the part, and
    `stroke` the narrowest stroke that size draws. `swap_mm` is the height above the bed
    where every letter starts, when there is one: raised text on the part's top face,
    printed as modelled. That is where a printer with one filament pauses for a swap.
    """

    blank: object
    structure: object
    base: object
    letters: object | None
    smallest: float
    stroke: float
    font: str
    swap_mm: float | None = None
    # The exact shape this describes. build123d copies attributes onto a moved or
    # rotated shape, so without this a part stood up after `add_text` would carry the
    # letters, the blank and the checks of the part lying down.
    owner: object = None
    # move() and locate() mutate owner itself, so its placement needs a separate copy.
    location: object = None


def font_file(font):
    """The bundled file for a font name, or a refusal that lists the ones nurb has."""
    if font not in FONTS:
        raise ValueError(f"no font named {font!r}. nurb ships {', '.join(repr(f) for f in FONTS)}")
    return FONTS_DIR / FONTS[font]


@functools.cache
def _characters(font):
    from fontTools.ttLib import TTFont

    return frozenset(TTFont(font_file(font)).getBestCmap())


def _check_characters(text, font):
    """Refuse a character the font cannot draw.

    OCCT draws a missing Latin glyph as an empty box and may borrow a missing CJK one
    from whatever system font it finds, which is the machine-dependent geometry this
    whole module exists to avoid. Better to say so than to print a box.
    """
    have = _characters(font)
    missing = sorted({c for c in text if c not in "\n" and ord(c) not in have})
    if missing:
        wider = [f for f in FONTS if f != font and all(ord(c) in _characters(f) for c in missing)]
        hint = f" {wider[0]} has them." if wider else " None of nurb's fonts do."
        raise ValueError(f"{font} has no {' '.join(missing)} to draw.{hint}")


def _flattened(face, step):
    """A glyph with its curves drawn as straight runs of about `step` mm.

    A glyph's curved outline extrudes to curved side faces, and OCCT meshes a curved
    side and the flat top along their shared edge a hair differently at some sizes:
    "SS" at 14mm and a third of Stencil's letter pairs left the STL with open edges for
    the slicer to patch. Straight runs make every face flat, which meshes closed every
    time and builds faster. At a fiftieth of the font size the runs sit within a few
    thousandths of a millimetre of the curve, far under what a nozzle can draw.
    """
    from build123d import Face, GeomType, Wire

    def wire(w):
        points = []
        for edge in w.order_edges():
            count = 2 if edge.geom_type == GeomType.LINE else max(3, math.ceil(edge.length / step) + 1)
            for i in range(count - 1):
                point = edge.position_at(i / (count - 1))
                # Two touching glyphs, grown and fused, meet in edges a few nanometres
                # long, which the mesher cannot close. Nothing that short is printable.
                if not points or (point - points[-1]).length > SHORTEST:
                    points.append(point)
        if len(points) > 1 and (points[0] - points[-1]).length <= SHORTEST:
            points.pop()
        return Wire.make_polygon(points, close=True)

    return Face(wire(face.outer_wire()), [wire(w) for w in face.inner_wires()])


def _merged(sketch):
    """The glyphs, with any two that touch grown by GROW and fused into one face.

    Only the touching ones: growing every glyph rounds its corners into arcs, and the
    extra faces made a 22-letter name take 1.4s instead of 0.6s to build.
    """
    from build123d import Compound, offset

    faces = list(sketch.faces())
    boxes = [f.bounding_box() for f in faces]
    near = 2 * GROW
    touching = set()
    for i in range(len(faces)):
        for j in range(i + 1, len(faces)):
            a, b = boxes[i], boxes[j]
            apart = (
                a.min.X > b.max.X + near or b.min.X > a.max.X + near
                or a.min.Y > b.max.Y + near or b.min.Y > a.max.Y + near
            )
            if not apart and faces[i].distance_to(faces[j]) < near:
                touching |= {i, j}
    if not touching:
        return sketch
    grown = [offset(faces[i], amount=GROW).faces()[0] for i in sorted(touching)]
    fused = grown[0].fuse(*grown[1:]).clean() if len(grown) > 1 else grown[0]
    step = max(0.2, max(b.size.Y for b in boxes) / 50)
    kept = [f for i, f in enumerate(faces) if i not in touching]
    return Compound(kept + [_flattened(f, step) for f in fused.faces()])


def _top_face(body):
    """The highest face that looks up, the largest if several tie."""
    from build123d import GeomType

    up = [f for f in body.faces() if f.geom_type == GeomType.PLANE and f.normal_at(f.center()).Z > 0.99]
    if not up:
        raise ValueError("this part has no flat face that faces up; pass the face to put the text on")
    top = max(f.center().Z for f in up)
    return max((f for f in up if f.center().Z > top - 1e-3), key=lambda f: f.area)


def _plane(face):
    """A plane on the face whose x runs the way a person reads it.

    Looking at the face from outside, text reads left to right with its tops toward
    +Z, or toward +Y on a face that looks straight up or down.
    """
    from build123d import GeomType, Plane, Vector

    if face.geom_type != GeomType.PLANE:
        raise ValueError("text goes on a flat face, and this one is curved")
    normal = face.normal_at(face.center())
    up = Vector(0, 0, 1) if abs(normal.Z) < 0.9 else Vector(0, 1, 0) * (1 if normal.Z > 0 else -1)
    x_dir = up.cross(normal)
    return Plane(origin=face.center(), x_dir=x_dir, z_dir=normal)


def add_text(body, text, face=None, *, size=None, depth=0.6, style="raised", font="Standard", margin=None, rotation=0.0):
    """Put text on a flat face of a part, and return the part with it.

    text: what to write. A line break starts a second line.
    face: the flat face to write on. Defaults to the highest face that looks up. Any
        flat face lying on the part works, so to write in only part of a face, pass a
        `Rectangle` placed on it: `(Plane.XY.offset(top) * Pos(x, 0) * Rectangle(w, h)).face()`.
    size: font size in mm. Leave it out and the text grows to fill the face, inside
        `margin`, so a longer name gets smaller letters instead of running off the edge.
    margin: clear space in mm between the text and the face's edges when fitting.
        Defaults to 20% of the face's shorter side, at least 1.5mm, so the letters have
        room to breathe on a 20mm tag and on a 200mm sign alike.
    depth: how far the letters stand up, or sink in. 0.6 is three 0.2mm layers, which is
        where a filament swap lands cleanly for two-colour raised text.
    style: "raised" letters stand on the face, "engraved" letters are cut into it, and
        "flush" letters are cut in and filled, level with the face, as a second body for a
        second filament.
    font: one of nurb's bundled fonts: "Standard" (default), a plain Arial-style sans;
        "Heavy", in the Arial Black spirit, whose thick strokes print best small; or
        "Stencil".
        Stencil is the one for text cut all the way through, because its "O" and "A"
        keep their middles.
    rotation: degrees, counter-clockwise as you look at the face.

    Call it last. Raised and flush text are carried on the returned part so they show,
    and export, in their own colour; a later boolean or move builds a new shape and the
    text becomes the part's colour. Empty text returns the part unchanged.
    """
    from build123d import Pos, Text, extrude

    if style not in STYLES:
        raise ValueError(f"style is one of {', '.join(STYLES)}, not {style!r}")
    if depth <= 0:
        raise ValueError(f"depth must be more than 0mm, not {depth}")
    path = font_file(font)
    if not text.strip():
        return body
    _check_characters(text, font)

    face = face if face is not None else _top_face(body)
    plane = _plane(face)
    room = plane.to_local_coords(face).bounding_box()

    def drawn(at):
        return Text(text, at, font=font, font_path=str(path), rotation=rotation)

    def flat(at):
        from build123d import Compound

        return Compound([_flattened(f, max(0.2, at / 50)) for f in drawn(at).faces()])

    if margin is None:
        margin = max(MARGIN_MIN, MARGIN * min(room.size.X, room.size.Y))
    if size is None:
        # Outlines scale exactly with size, so one measurement at 10mm sizes the rest.
        probe = drawn(10.0).bounding_box()
        fit = min((room.size.X - 2 * margin) / probe.size.X, (room.size.Y - 2 * margin) / probe.size.Y)
        if fit <= 0:
            raise ValueError(f"no room for text on a {room.size.X:.1f} x {room.size.Y:.1f}mm face inside a {margin:.1f}mm margin")
        size = 10.0 * fit
    elif size <= 0:
        raise ValueError(f"size must be more than 0mm, not {size}")

    sketch = _merged(flat(size))
    middle = sketch.bounding_box().center()
    sketch = plane.location * (Pos(room.center().X - middle.X, room.center().Y - middle.Y) * sketch)
    normal = plane.z_dir

    before = lettering(body)
    structure = before.structure if before else body
    base = before.base if before else body
    letters = before.letters if before else None
    if style == "raised":
        new = extrude(sketch, amount=depth, dir=normal)
        whole = body + new
        letters = new if letters is None else letters + new
    else:
        cut = extrude(sketch, amount=depth, dir=-normal) & body
        base = base - cut
        if style == "engraved":
            whole = body - cut
            structure = structure - cut
            letters = None if letters is None else letters - cut
        else:
            whole = body
            letters = cut if letters is None else (letters - cut) + cut

    swap = None
    if style == "raised" and normal.Z > 0.99:
        box = body.bounding_box()
        if face.center().Z > box.max.Z - 1e-3:
            swap = round(face.center().Z - box.min.Z, 3)
    if before:
        swap = swap if swap is not None and before.swap_mm == swap else None
    stroke = STROKE[font] * size
    smallest = min(size, before.smallest) if before else size
    whole._nurb_text = Lettering(
        blank=before.blank if before else body,
        structure=structure,
        base=base,
        letters=letters,
        smallest=smallest,
        stroke=min(stroke, before.stroke) if before else stroke,
        font=font,
        swap_mm=swap,
        owner=whole.wrapped,
        location=whole.location,
    )
    return whole


def lettering(shape):
    """The text a part carries, or None once anything has changed the shape since."""
    found = getattr(shape, "_nurb_text", None)
    wrapped = getattr(shape, "wrapped", None)
    if found is None or wrapped is None or not wrapped.IsEqual(found.owner) or shape.location != found.location:
        return None
    return found


def moved(shape, location):
    """`location * shape`, with its text moved along with it.

    For laying parts out on a plate, where the move is nurb's own and the letters
    should keep their colour through it.
    """
    out = location * shape
    found = lettering(shape)
    if found is not None:
        def at(body):
            return None if body is None else location * body

        out._nurb_text = dataclasses.replace(
            found, blank=at(found.blank), structure=at(found.structure), base=at(found.base), letters=at(found.letters),
            swap_mm=None, owner=out.wrapped, location=out.location
        )
    return out
