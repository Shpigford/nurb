import io
import zipfile
from xml.etree import ElementTree

import pytest
import trimesh
from build123d import Box, Cylinder, Pos

from nurb import add_color, add_text, builder, edit, engine_run, raster
from nurb.color import bodies, coloring, moved, slots


def shell():
    return Box(60, 40, 20)


def screen():
    return Pos(0, 0, 9.5) * Box(40, 25, 1)


def knob():
    return Pos(25, 0, 12) * Cylinder(4, 4)


def tv():
    part = add_color(shell(), "#E8704A")
    part = add_color(part, "#1a1a1a", screen())
    return add_color(part, "#f2e8d5", knob())


def test_an_inlay_is_cut_from_the_part_and_a_knob_is_added_to_it():
    part = tv()
    split = bodies(part)
    assert [c for c, _ in split] == ["#e8704a", "#1a1a1a", "#f2e8d5"]
    # The inlay replaces material, the knob adds it, and the bodies are the part.
    assert split[0][1].volume == pytest.approx(60 * 40 * 20 - 40 * 25 * 1, rel=1e-6)
    assert part.volume == pytest.approx(sum(b.volume for _, b in split), rel=1e-6)
    assert len(part.solids()) == 1


def test_a_later_region_wins_where_two_overlap():
    part = add_color(shell(), "#111111", Pos(0, 0, 9) * Box(10, 10, 2))
    part = add_color(part, "#222222", Pos(5, 0, 9) * Box(10, 10, 2))
    (_, base), (_, first), (_, second) = bodies(part)
    assert first.volume == pytest.approx(5 * 10 * 2, rel=1e-6)
    assert second.volume == pytest.approx(10 * 10 * 2, rel=1e-6)


def test_a_bad_color_is_refused_with_the_shape_of_a_good_one():
    with pytest.raises(ValueError, match="#rrggbb"):
        add_color(shell(), "red")


def test_color_goes_on_before_text():
    with pytest.raises(ValueError, match="before add_text"):
        add_color(add_text(shell(), "AB"), "#123456")


def test_text_on_a_colored_part_keeps_the_colors_and_cuts_the_body_it_lands_on():
    part = add_text(tv(), "AB", Pos(0, 0, 10) * Box(30, 15, 0.001).faces().sort_by().last, style="flush", size=8)
    split = bodies(part)
    assert [c for c, _ in split] == ["#e8704a", "#1a1a1a", "#f2e8d5", "text"]
    # The letters landed on the screen, so the screen lost what they filled.
    assert split[1][1].volume < 40 * 25 * 1 - 1
    assert part.volume == pytest.approx(sum(b.volume for _, b in split), rel=1e-6)


def test_text_in_a_color_and_mixed_text_colors_are_refused():
    part = add_text(shell(), "AB", color="#ff0000")
    assert bodies(part)[-1][0] == "#ff0000"
    with pytest.raises(ValueError, match="one color"):
        add_text(part, "C", Pos(0, 0, 10) * Box(10, 10, 0.001).faces().sort_by().last, color="#00ff00")


def test_anything_done_after_add_color_drops_the_colors():
    part = tv()
    assert coloring(part) is not None
    assert coloring(part + Pos(40, 0, 0) * Box(5, 5, 5)) is None


def test_the_viewer_gets_one_node_per_body_named_by_its_color():
    scene = trimesh.load(io.BytesIO(builder.to_glb(tv())), file_type="glb")
    assert sorted(scene.geometry) == ["color-1a1a1a-1", "color-e8704a-0", "color-f2e8d5-2"]


def test_the_3mf_puts_each_color_on_its_own_filament_and_shares_a_repeated_one(tmp_path):
    part = add_color(tv(), "#1a1a1a", Pos(-25, 0, 12) * Cylinder(4, 4))
    entries, colors = builder.by_filament([part])
    assert colors == ["#e8704a", "#1a1a1a", "#f2e8d5"]
    assert [slot for slot, _, _ in entries[0]] == [1, 2, 3, 2]
    target = tmp_path / "tv.3mf"
    builder.write_3mf(entries, target)
    config = zipfile.ZipFile(target).read("Metadata/model_settings.config").decode()
    assert config.count("<part ") == 4
    assert '<metadata key="extruder" value="3"/>' in config


def test_slots_put_the_parts_own_filament_first():
    assert slots(["text", None]) == [None, "#ffffff"]
    assert slots(["#aaaaaa", "#bbbbbb", "#aaaaaa"]) == ["#aaaaaa", "#bbbbbb"]


def test_a_plate_keeps_each_parts_colors_where_it_was_laid():
    part = tv()
    a = moved(part, Pos(-80, 0, 0))
    split = bodies(a)
    assert split[1][1].bounding_box().center().X == pytest.approx(-80, abs=1e-6)


def test_the_picture_paints_a_region_in_its_color():
    import numpy as np

    from PIL import Image

    png = raster.render(builder.to_glb(tv()))
    pixels = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).reshape(-1, 3)
    # The screen is near black, which the part's own orange tones never are.
    assert ((pixels < 40).all(axis=1)).sum() > 500


def test_applying_a_hex_label_keeps_the_text_control(tmp_path):
    path = tmp_path / "tag.py"
    source = 'from nurb import *\n@part\ndef tag(text: str = "Hi"):\n    return add_text(Box(50, 20, 4), text, size=5)\n'
    applied, written, _ = edit.apply_to_source(source, {"text": "#123456"})
    path.write_text(applied)
    _, params, _ = builder.build(path)
    assert written == ["text"]
    assert (params[0]["kind"], params[0]["value"]) == ("str", "#123456")


def test_an_annotated_color_stays_adjustable_after_apply(tmp_path):
    path = tmp_path / "tile.py"
    source = (
        'from __future__ import annotations\nfrom nurb import *\n'
        '@part\ndef tile(body_color: FilamentColor = "#e8704a"):\n'
        '    return add_color(Box(20, 10, 4), body_color)\n'
    )
    applied, written, _ = edit.apply_to_source(source, {"body_color": "#123456"})
    path.write_text(applied)
    shape, params, _ = builder.build(path)
    assert written == ["body_color"]
    assert (params[0]["kind"], params[0]["value"]) == ("color", "#123456")
    assert bodies(shape)[0][0] == "#123456"


def test_a_one_color_part_on_a_plate_keeps_the_slicers_first_filament():
    colored = add_color(shell(), "#1a1a1a")
    entries, colors = builder.by_filament([colored, shell()])
    assert colors == [None, "#1a1a1a"]


def test_a_region_covered_whole_by_a_later_one_costs_no_filament():
    part = add_color(shell(), "#ff0000", Pos(0, 0, 9.5) * Box(10, 10, 1))
    part = add_color(part, "#00ff00", Pos(0, 0, 9.5) * Box(20, 20, 1))
    assert [c for c, _ in bodies(part)] == [None, "#00ff00"]


def test_a_region_that_consumes_the_base_only_allocates_real_filaments():
    part = add_color(shell(), "#123456", shell())
    assert builder.by_filament([part])[1] == ["#123456"]
    part = add_color(part, "#fedcba", screen())
    part = add_text(part, "AB", style="engraved", size=8)
    assert builder.by_filament([part])[1] == ["#123456", "#fedcba"]
    assert sum(body.volume for _, body in bodies(part)) == pytest.approx(part.volume)


def test_engraving_preserves_the_color_of_existing_letters():
    part = add_text(shell(), "AB", color="#ff0000", size=6)
    face = (Pos(20, 0, 9.9995) * Box(10, 10, 0.001)).faces().sort_by().last
    engraved = add_text(part, "C", face, style="engraved", size=4)
    assert engraved.volume < part.volume
    assert builder.by_filament([engraved])[1] == [None, "#ff0000"]


def test_the_bare_3mf_keeps_the_palette_and_summarizes_the_plate(tmp_path):
    parts = tmp_path / "parts"
    parts.mkdir()
    for name, color in (("blue", "#123456"), ("cream", "#fedcba")):
        (parts / f"{name}.py").write_text(
            f'from nurb import *\n@part\ndef {name}():\n    return add_color(Box(20, 10, 4), "{color}")\n'
        )
    (parts / "both.py").write_text(
        'from nurb import *\n@assembly\ndef both():\n    return use("blue"), Pos(30, 0, 0) * use("cream")\n'
    )
    result = engine_run._export_in_process(tmp_path, "both", "3mf")
    assert "2 colors, one filament each" in result["note"]
    with zipfile.ZipFile(io.BytesIO(result["bytes"])) as bundle:
        model = ElementTree.fromstring(bundle.read("3D/3dmodel.model"))
    palette = model.find(".//{*}basematerials")
    assert palette is not None
    assigned = {
        obj.get("name"): palette[int(obj.attrib["pindex"])].attrib["displaycolor"][:7].lower()
        for obj in model.findall(".//{*}object[@pindex]")
        if obj.get("pid") == palette.get("id")
    }
    assert assigned == {"blue": "#123456", "cream": "#fedcba"}
