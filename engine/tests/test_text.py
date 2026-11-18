"""Text on parts: the bundled fonts, the three styles, and what carries the letters
through to the viewer, the checks and the 3MF."""

import io
import pathlib
import zipfile

import pytest
from build123d import Axis, Box, Edge, Pos, Rectangle, Rot, Text

from nurb import builder, checks, edit
from nurb.registry import part
from nurb.text import FONTS, STROKE, add_text, font_file, lettering

TAG = pathlib.Path(__file__).parents[1] / "examples" / "tags" / "parts" / "name_tag.py"


def plate():
    return Box(93, 34, 2)


@pytest.mark.parametrize("font", list(FONTS))
def test_stroke_table_is_what_each_font_draws(font):
    """The text rule's sizes come from this table, so it is measured, not remembered."""
    drawn = Text("l", 100, font=font, font_path=str(font_file(font)))
    box = drawn.bounding_box()
    across = Edge.make_line((box.min.X - 5, box.center().Y, 0), (box.max.X + 5, box.center().Y, 0))
    width = sum(e.length for e in drawn.faces()[0].intersect(across).edges())
    assert width / 100 == pytest.approx(STROKE[font], abs=0.002)


def test_a_font_nurb_does_not_ship_is_refused_not_swapped_for_arial():
    with pytest.raises(ValueError, match="no font named 'Arial'. nurb ships 'Standard'"):
        add_text(plate(), "hi", font="Arial")


def test_a_character_the_font_cannot_draw_is_refused():
    with pytest.raises(ValueError, match="Standard has no ✓ to draw"):
        add_text(plate(), "ok ✓")


@pytest.mark.parametrize("style", ["raised", "engraved", "flush"])
def test_every_style_is_one_valid_solid_that_fits_the_face(style):
    shape = add_text(plate(), "PLA Silk", style=style)
    assert shape.is_valid and len(shape.solids()) == 1
    lettered = lettering(shape)
    # Fit to the face inside the 2mm margin: the 34mm side is what limits "PLA Silk".
    assert 20 < lettered.smallest < 30
    if style == "engraved":
        assert lettered.letters is None
        assert shape.volume < plate().volume
    else:
        # The dot on the i is a solid of its own and stays with the letters.
        assert len(lettered.letters.solids()) == 8
        assert lettered.base.volume + lettered.letters.volume == pytest.approx(shape.volume, rel=1e-6)


def test_text_builds_the_same_shape_every_time():
    """The doctrine kept text off parts because a system font differs by machine. A
    bundled font is the same file everywhere, so two builds must agree exactly."""
    a = add_text(plate(), "nurb 2026")
    b = add_text(plate(), "nurb 2026")
    assert (round(a.volume, 6), len(a.faces())) == (round(b.volume, 6), len(b.faces()))


def test_empty_text_leaves_the_part_alone():
    body = plate()
    assert add_text(body, "  ") is body


def test_text_on_a_side_face_reads_left_to_right():
    body = Box(60, 20, 30)
    front = body.faces().sort_by(Axis.Y)[0]
    shape = add_text(body, "FRONT", front)
    letters = lettering(shape).letters.bounding_box()
    assert letters.max.Y <= -10 + 1e-6 and letters.min.Y == pytest.approx(-10.6, abs=1e-3)
    assert letters.size.X > letters.size.Z  # laid along the face, not up it


def test_raised_text_on_top_knows_where_a_filament_swap_goes():
    assert lettering(add_text(plate(), "AB")).swap_mm == 2.0
    assert lettering(add_text(plate(), "AB", style="flush")).swap_mm is None


def test_the_checks_judge_the_part_without_its_text_and_the_text_on_its_own():
    """Glyph flanks are hundreds of small faces and a 0.6mm relief is not a wall."""
    assert checks.run(add_text(plate(), "PLA Silk")) == []
    small = checks.run(add_text(plate(), "PLA Silk", size=4.0))
    assert [f.rule for f in small] == ["text"]
    assert "size 7.3mm or more" in small[0].message


def test_raised_text_on_the_bed_face_fails_and_flush_there_does_not():
    bottom = plate().faces().sort_by(Axis.Z)[0]
    found = checks.run(add_text(plate(), "PLA Silk", bottom), only=["text"])
    assert [(f.rule, f.severity) for f in found] == [("text", checks.FAIL)]
    assert "turned over" in found[0].said
    assert checks.run(add_text(plate(), "PLA Silk", bottom, style="flush"), only=["text"]) == []
    assert checks.run(add_text(plate(), "PLA Silk"), only=["text"]) == []


@pytest.mark.parametrize("later", [None, "raised", "flush"])
def test_engraving_keeps_the_thin_floor_visible_to_structural_checks(later):
    shape, _, _ = builder.build(
        TAG, overrides={"thickness": 1.5, "letter_depth": 1.2, "style": "engraved"}
    )
    if later:
        face = (Pos(-26, 0, 1.5) * Rectangle(6, 10)).face()
        shape = add_text(shape, "I", face, size=8, style=later)
    findings = checks.run(shape, only=["min_wall"])
    assert len(findings) == 1 and findings[0].rule == "min_wall"
    assert findings[0].value == pytest.approx(0.3, abs=0.01)


def test_printer_fit_includes_raised_lettering():
    shape = add_text(Box(256, 256, 255.8), "AB", size=10)
    findings = checks.run(shape, only=["build_volume"])
    assert len(findings) == 1 and findings[0].rule == "build_volume"


def test_the_viewer_gets_the_letters_as_their_own_node():
    import trimesh

    glb = builder.to_glb(add_text(plate(), "AB", style="flush"))
    scene = trimesh.load(io.BytesIO(glb), file_type="glb")
    assert sorted(scene.geometry) == ["part", "text"]


def test_the_3mf_puts_the_letters_on_filament_two_in_one_object(tmp_path):
    shape = add_text(plate(), "AB")
    target = tmp_path / "tag.3mf"
    builder.write_3mf(builder.by_filament([shape])[0], target)
    config = zipfile.ZipFile(target).read("Metadata/model_settings.config").decode()
    assert config.count("<part ") == 2
    assert '<metadata key="name" value="text"/>\n      <metadata key="extruder" value="2"/>' in config
    # A part without text is written exactly as before, with no settings file.
    builder.write_3mf(builder.by_filament([plate()])[0], target)
    assert "Metadata/model_settings.config" not in zipfile.ZipFile(target).namelist()


def test_a_literal_annotation_is_a_choice_and_a_plain_string_is_text():
    from typing import Literal

    @part
    def tag(text="Hi", style: Literal["raised", "flush"] = "raised", bad: Literal["a"] = "b", n=2):
        return Box(1, 1, 1)

    rows = {r["name"]: r for r in builder.describe(tag._nurb, tag._nurb.params)}
    assert rows["text"]["kind"] == "str"
    assert rows["style"] == {**rows["style"], "kind": "choice", "options": ["raised", "flush"]}
    # A default outside its own options would be a picker with nothing picked.
    assert rows["bad"]["kind"] == "str"
    assert rows["n"]["kind"] == "int"


@pytest.mark.parametrize(
    "overrides,said",
    [
        ({}, []),
        ({"style": "flush", "text": "PLA Silk"}, []),
        ({"style": "engraved", "font": "Stencil"}, []),
        ({"text": ""}, []),
        # A long name on a 60mm tag fits at 6mm, under what prints cleanly: the panel says so.
        ({"style": "flush", "text": "Sir Reginald"}, ["text"]),
    ],
)
def test_the_name_tag_example_builds_in_every_style(overrides, said):
    shape, params, _ = builder.build(TAG, overrides=overrides or None)
    assert len(shape.solids()) == 1 and shape.is_valid
    assert [f.rule for f in checks.run(shape)] == said
    assert [p["kind"] for p in params][:3] == ["str", "choice", "choice"]


def test_typing_a_name_and_saving_it_rewrites_the_source():
    source = TAG.read_text(encoding="utf-8")
    out, written, skipped = edit.apply_to_source(source, {"text": "Mochi", "style": "flush"})
    assert written == ["style", "text"] and skipped == []
    assert 'text="Mochi"' in out and 'style: Literal["raised", "engraved", "flush"] = "flush"' in out


def test_moving_a_part_after_its_text_drops_the_text_rather_than_lying():
    """build123d copies attributes onto a moved shape. A part stood up after add_text
    must be judged, drawn and exported standing up, so the stale letters go."""
    from build123d import Pos, Rot

    body = Box(60, 20, 3) + Pos(25, 0, 8) * Box(10, 20, 14)
    flipped = Rot(180, 0, 0) * add_text(body, "Hi", size=6)
    assert lettering(flipped) is None
    assert checks.judged(flipped) is flipped
    assert {f.rule for f in checks.run(flipped)} >= {"floating"}


@pytest.mark.parametrize("placement", ["move", "locate", "position"])
def test_in_place_placement_drops_stale_viewer_and_filament_geometry(placement):
    import trimesh

    shape = add_text(Box(40, 20, 3), "AB", size=10)
    if placement == "position":
        shape.position = (100, 0, 0)
    else:
        getattr(shape, placement)(Pos(100, 0, 0) * Rot(90, 0, 0))
    assert lettering(shape) is None
    scene = trimesh.load(io.BytesIO(builder.to_glb(shape)), file_type="glb")
    box = shape.bounding_box()
    assert scene.bounds[0] == pytest.approx(tuple(box.min), abs=1e-5)
    assert scene.bounds[1] == pytest.approx(tuple(box.max), abs=1e-5)
    assert builder.by_filament([shape]) == ([shape], None)


def test_copying_or_leaving_placement_unchanged_preserves_lettering():
    import copy
    import trimesh

    shape = add_text(plate(), "AB", style="flush")
    for kept in (shape, copy.copy(shape)):
        kept.move(Pos(0, 0, 0))
        assert lettering(kept) is not None
        scene = trimesh.load(io.BytesIO(builder.to_glb(kept)), file_type="glb")
        assert set(scene.geometry) == {"part", "text"}


def test_a_plate_of_lettered_parts_keeps_each_ones_letters_where_it_was_laid():
    from build123d import Pos

    from nurb.text import moved

    tag = add_text(plate(), "AB")
    tag.label = "tag"
    a, b = moved(tag, Pos(-60, 0, 0)), moved(tag, Pos(60, 0, 0))
    entries, colors = builder.by_filament([a, b])
    assert colors == [None, "#ffffff"]
    assert [e[0][2] for e in entries] == ["tag", "tag"]
    for entry, x in zip(entries, (-60, 60)):
        (_, base, _), (_, letters, _) = entry
        assert base.bounding_box().center().X == pytest.approx(x, abs=1e-6)
        assert letters.bounding_box().center().X == pytest.approx(x, abs=2)


def test_the_mesh_rule_still_reads_the_letters():
    """The export is the whole part, so the rule that guards it sees the glyphs."""
    assert "mesh" in checks.WHOLE


@pytest.mark.parametrize("font,pair", [("Standard", "VY"), ("Standard", "SS"), ("Heavy", "vy"), ("Stencil", "VV"), ("Stencil", "HH")])
def test_kerned_letters_that_touch_still_export_closed(font, pair):
    """Glyphs that touch at a point crack the mesh the slicer gets; they are merged first."""
    shape = add_text(Box(40, 20, 3), pair, font=font, size=14)
    assert shape.is_valid and builder._welded(shape).is_watertight
