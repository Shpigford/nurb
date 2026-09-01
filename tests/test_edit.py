"""Writing slider values back into a part file.

This is the only code in nurb that edits someone's source, so the tests care as much
about what it leaves alone as about what it changes.
"""

import pytest

from nurb import checks, edit

SOURCE = '''from nurb import *

from system import SIDE_CLEARANCE


@part
def thing(
    count=4,          # how many
    height=42,
    chamfer=1.0,
    offset=-3,
    clearance=SIDE_CLEARANCE,
    scale=cell / 2,
    draft=False,
):
    return Box(count, height, chamfer)
'''


@pytest.fixture
def part_file(tmp_path):
    path = tmp_path / "thing.py"
    path.write_text(SOURCE)
    return path


def defaults(path):
    """What the file's signature says now, read back through the parser."""
    tree = edit.ast.parse(path.read_text())
    fn = edit._part_function(tree, path)
    return {k: edit._number(v) for k, v in edit._defaults(fn).items()}


def test_writes_only_the_defaults_it_was_given(part_file):
    written, skipped = edit.apply(part_file, {"count": 6, "height": 50})
    assert written == ["count", "height"]
    assert skipped == []
    assert defaults(part_file) == {
        "count": 6, "height": 50, "chamfer": 1.0, "offset": -3, "draft": None,
        "clearance": None, "scale": None,
    }


def test_everything_around_the_number_survives(part_file):
    edit.apply(part_file, {"count": 6})
    text = part_file.read_text()
    assert "    count=6,          # how many" in text
    assert "from system import SIDE_CLEARANCE" in text
    assert text.splitlines()[-1] == "    return Box(count, height, chamfer)"
    # One line differs, and it is the one that was asked for.
    changed = [
        (a, b)
        for a, b in zip(SOURCE.splitlines(), text.splitlines())
        if a != b
    ]
    assert len(changed) == 1


def test_an_int_stays_an_int_and_a_float_stays_a_float(part_file):
    edit.apply(part_file, {"count": 7.0, "chamfer": 2})
    text = part_file.read_text()
    assert "count=7," in text
    assert "chamfer=2.0," in text


def test_a_slider_lands_on_a_number_someone_would_write(part_file):
    """0.1 + 0.2 is a real slider value and 0.30000000000000004 is not a dimension."""
    edit.apply(part_file, {"chamfer": 0.1 + 0.2})
    assert "chamfer=0.3," in part_file.read_text()


def test_several_defaults_on_one_line(tmp_path):
    """Each splice shifts the rest of its line, so the edits go in last-to-first.
    Written left-to-right, the second one lands at an offset that has moved."""
    path = tmp_path / "row.py"
    path.write_text("from nurb import *\n\n\n@part\ndef row(a=1, b=2, c=3):  # all three\n    return a\n")
    edit.apply(path, {"a": 10, "b": 20, "c": 30})
    assert path.read_text().splitlines()[4] == "def row(a=10, b=20, c=30):  # all three"


def test_negatives_keep_their_sign(part_file):
    edit.apply(part_file, {"offset": -5})
    assert "offset=-5," in part_file.read_text()
    assert defaults(part_file)["offset"] == -5


@pytest.mark.parametrize("name,written_as", [("clearance", "SIDE_CLEARANCE"), ("scale", "cell / 2")])
def test_a_default_that_is_not_a_number_is_left_alone_and_explained(part_file, name, written_as):
    """Replacing a named constant with a literal keeps the number and loses its source."""
    written, skipped = edit.apply(part_file, {name: 0.5, "count": 5})
    assert written == ["count"]
    assert [n for n, _ in skipped] == [name]
    assert written_as in skipped[0][1]
    # The one it could write still landed: one such parameter must not block the rest.
    assert defaults(part_file)["count"] == 5
    assert written_as in part_file.read_text()


def test_values_already_equal_to_the_default_leave_no_diff(part_file):
    written, _ = edit.apply(part_file, {"count": 4, "height": 42})
    assert written == []
    assert part_file.read_text() == SOURCE


def test_an_unknown_parameter_is_an_error_not_a_skip(part_file):
    with pytest.raises(edit.EditError, match="no parameter named nope"):
        edit.apply(part_file, {"nope": 1})


def test_a_file_with_no_part_says_so(tmp_path):
    path = tmp_path / "plain.py"
    path.write_text("def thing(count=4):\n    return count\n")
    with pytest.raises(edit.EditError, match="no @part function"):
        edit.apply(path, {"count": 5})


def test_the_temp_file_does_not_survive(part_file):
    edit.apply(part_file, {"count": 9})
    assert [p.name for p in part_file.parent.iterdir()] == ["thing.py"]


CARD = '''# thing

Ported by hand.

```toml
[part]
min_wall = 0.7

# Why the wide one exists.
[variants.wide.params]
count = 6
chamfer = 2.0

[variants.wide.accepted]
sliver = 4

[variants.bare.accepted]
sliver = 2
```

## Notes

More prose after the block.
'''


@pytest.fixture
def carded(part_file):
    (part_file.parent / "thing.md").write_text(CARD)
    return part_file


def read_variants(card):
    import tomllib

    block = card.read_text(encoding="utf-8").split("```toml", 1)[1].split("```", 1)[0]
    return tomllib.loads(block)["variants"]


def test_updates_only_the_variant_it_was_given(carded):
    written = edit.apply_variant(carded, "wide", {"count": 8, "height": 50})
    assert written == ["count", "height"]
    card = carded.parent / "thing.md"
    variants = read_variants(card)
    # chamfer went back to the default at some point, so it is no longer an override.
    assert variants["wide"]["params"] == {"count": 8, "height": 50}
    assert variants["wide"]["accepted"] == {"sliver": 4}
    text = card.read_text()
    assert "# Why the wide one exists." in text
    assert "min_wall = 0.7" in text
    assert "More prose after the block." in text


def test_variant_values_keep_the_signature_types(carded):
    edit.apply_variant(carded, "wide", {"count": 8.0, "chamfer": 2, "flag": True, "label": "x"})
    text = (carded.parent / "thing.md").read_text()
    assert "count = 8\n" in text
    assert "chamfer = 2.0\n" in text
    assert "flag = true\n" in text
    assert 'label = "x"\n' in text


def test_variant_strings_keep_non_bmp_unicode(carded):
    edit.apply_variant(carded, "wide", {"label": "fixture 😀"})
    variants = read_variants(carded.parent / "thing.md")
    assert variants["wide"]["params"] == {"label": "fixture 😀"}


def test_a_quoted_variant_name_is_updated(carded):
    card = carded.parent / "thing.md"
    card.write_text(CARD.replace("variants.wide", 'variants."wide one"'))
    edit.apply_variant(carded, "wide one", {"count": 8})
    assert read_variants(card)["wide one"]["params"] == {"count": 8}


def test_a_quoted_variant_name_gets_a_params_section(carded):
    card = carded.parent / "thing.md"
    card.write_text(CARD.replace("variants.bare", 'variants."bare one"'))
    edit.apply_variant(carded, "bare one", {"height": 30})
    assert read_variants(card)["bare one"] == {
        "params": {"height": 30}, "accepted": {"sliver": 2}
    }


def test_a_variant_without_a_params_section_gets_one(carded):
    edit.apply_variant(carded, "bare", {"height": 30})
    variants = read_variants(carded.parent / "thing.md")
    assert variants["bare"] == {"params": {"height": 30}, "accepted": {"sliver": 2}}


INLINE_CARD = '''# thing

```toml
[part]
min_wall = 1.6

[variants.30230]
note = "for the 10-7/8 inch bin: 3 fill the floor, 2 stack"
params = { count = 5, chamfer = 2.0 }

[variants.30250]
note = "for the big bin"
params = { count = 7 }
```
'''


def test_an_inline_params_table_is_replaced_in_place(part_file):
    """Agent-written cards hold the overrides as `params = {...}` on one line. Adding
    a [variants.<name>.params] section next to that would define params twice, which
    is exactly the write the validation refused in the field."""
    card = part_file.parent / "thing.md"
    card.write_text(INLINE_CARD)
    written = edit.apply_variant(part_file, "30230", {"count": 6, "height": 50})
    assert written == ["count", "height"]
    variants = read_variants(card)
    assert variants["30230"] == {
        "note": "for the 10-7/8 inch bin: 3 fill the floor, 2 stack",
        "params": {"count": 6, "height": 50},
    }
    # The sibling variant and its inline table survive untouched.
    assert 'params = { count = 7 }' in card.read_text()


def test_an_inline_params_table_can_empty_out(part_file):
    """Dragged back to the part's defaults, the variant keeps its row but no overrides."""
    card = part_file.parent / "thing.md"
    card.write_text(INLINE_CARD)
    edit.apply_variant(part_file, "30230", {})
    assert read_variants(card)["30230"]["params"] == {}


def test_a_variant_the_card_never_mentions_is_an_error(carded):
    with pytest.raises(edit.EditError, match="no variant named tall"):
        edit.apply_variant(carded, "tall", {"count": 8})


def test_a_part_without_a_card_says_so(part_file):
    with pytest.raises(edit.EditError, match="no card"):
        edit.apply_variant(part_file, "wide", {"count": 8})


def test_the_variant_temp_file_does_not_survive(carded):
    edit.apply_variant(carded, "wide", {"count": 8})
    assert sorted(p.name for p in carded.parent.iterdir()) == ["thing.md", "thing.py"]


def test_non_ascii_earlier_on_the_line_does_not_shift_the_offsets(tmp_path):
    """col_offset counts utf-8 bytes, not characters.

    The degree sign has to sit *before* the number for this to test anything: it is two
    bytes, so slicing the line by character index would cut one character short and
    write the new value into the middle of the previous argument.
    """
    path = tmp_path / "wide.py"
    src = 'from nurb import *\n\n\n@part\ndef thing(label="45°", count=4):\n    return count\n'
    path.write_text(src, encoding="utf-8")
    edit.apply(path, {"count": 6})
    assert path.read_text(encoding="utf-8") == src.replace("count=4", "count=6")


# --- supports ----------------------------------------------------------------


def supports_card(tmp_path, body):
    (tmp_path / "thing.py").write_text("")
    (tmp_path / "thing.md").write_text(body, encoding="utf-8")
    return tmp_path / "thing.py"


def test_supports_starts_a_settings_block_on_a_card_that_has_none(tmp_path):
    """Every card `nurb new` writes is this shape, so it is the common case and not
    an error: the control exists so nobody has to learn the file format first."""
    part = supports_card(tmp_path, "# thing\n\n## What it is\n\nA thing.\n")
    edit.set_supports(part, True)
    text = (tmp_path / "thing.md").read_text(encoding="utf-8")
    assert checks.settings(part) == {"part": {"supports": True}}
    assert "A thing.\n\n```toml" in text  # prose and fence stay separate
    assert text.endswith("```\n")


def test_supports_joins_a_settings_block_that_already_exists(tmp_path):
    part = supports_card(
        tmp_path, "# thing\n\n```toml\n[accepted]\nsliver = 6\n```\n\n## Notes\n"
    )
    edit.set_supports(part, True)
    settings = checks.settings(part)
    assert settings["part"] == {"supports": True}
    assert settings["accepted"] == {"sliver": 6}  # untouched
    assert "## Notes" in (tmp_path / "thing.md").read_text(encoding="utf-8")


def test_supports_leaves_the_rest_of_the_part_table_alone(tmp_path):
    part = supports_card(
        tmp_path, "# thing\n\n```toml\n[part]\nmin_wall = 1.0\nsupports = false\n```\n"
    )
    edit.set_supports(part, True)
    assert checks.settings(part)["part"] == {"supports": True, "min_wall": 1.0}


def test_supports_can_be_turned_back_off(tmp_path):
    part = supports_card(tmp_path, "# thing\n\n## What it is\n\nA thing.\n")
    edit.set_supports(part, True)
    edit.set_supports(part, False)
    assert checks.settings(part)["part"] == {"supports": False}


def test_supports_needs_a_card_to_write_to(tmp_path):
    (tmp_path / "thing.py").write_text("")
    with pytest.raises(edit.EditError, match="does not exist"):
        edit.set_supports(tmp_path / "thing.py", True)
