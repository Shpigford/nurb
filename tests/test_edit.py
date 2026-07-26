"""Writing slider values back into a part file.

This is the only code in nurb that edits someone's source, so the tests care as much
about what it leaves alone as about what it changes.
"""

import pytest

from nurb import edit

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
