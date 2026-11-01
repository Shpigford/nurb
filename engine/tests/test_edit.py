"""Writing slider values back into a part's source.

This is the only code in nurb that rewrites someone's source, so the tests care as much
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


def defaults(source):
    """What the signature says now, read back through the parser."""
    fn = edit._part_function(edit.ast.parse(source), "the part")
    return {k: edit._number(v) for k, v in edit._defaults(fn).items()}


def test_writes_only_the_defaults_it_was_given():
    out, written, skipped = edit.apply_to_source(SOURCE, {"count": 6, "height": 50})
    assert written == ["count", "height"]
    assert skipped == []
    assert defaults(out) == {
        "count": 6, "height": 50, "chamfer": 1.0, "offset": -3, "draft": None,
        "clearance": None, "scale": None,
    }


def test_everything_around_the_number_survives():
    out, _, _ = edit.apply_to_source(SOURCE, {"count": 6})
    assert "    count=6,          # how many" in out
    assert "from system import SIDE_CLEARANCE" in out
    assert out.splitlines()[-1] == "    return Box(count, height, chamfer)"
    # One line differs, and it is the one that was asked for.
    changed = [(a, b) for a, b in zip(SOURCE.splitlines(), out.splitlines()) if a != b]
    assert len(changed) == 1


def test_an_int_stays_an_int_and_a_float_stays_a_float():
    out, _, _ = edit.apply_to_source(SOURCE, {"count": 7.0, "chamfer": 2})
    assert "count=7," in out
    assert "chamfer=2.0," in out


def test_a_slider_lands_on_a_number_someone_would_write():
    """0.1 + 0.2 is a real slider value and 0.30000000000000004 is not a dimension."""
    out, _, _ = edit.apply_to_source(SOURCE, {"chamfer": 0.1 + 0.2})
    assert "chamfer=0.3," in out


def test_several_defaults_on_one_line():
    """Each splice shifts the rest of its line, so the edits go in last-to-first.
    Written left-to-right, the second one lands at an offset that has moved."""
    source = "from nurb import *\n\n\n@part\ndef row(a=1, b=2, c=3):  # all three\n    return a\n"
    out, _, _ = edit.apply_to_source(source, {"a": 10, "b": 20, "c": 30})
    assert out.splitlines()[4] == "def row(a=10, b=20, c=30):  # all three"


def test_negatives_keep_their_sign():
    out, _, _ = edit.apply_to_source(SOURCE, {"offset": -5})
    assert "offset=-5," in out
    assert defaults(out)["offset"] == -5


@pytest.mark.parametrize("name,written_as", [("clearance", "SIDE_CLEARANCE"), ("scale", "cell / 2")])
def test_a_default_that_is_not_a_number_is_left_alone_and_explained(name, written_as):
    """Replacing a named constant with a literal keeps the number and loses its source."""
    out, written, skipped = edit.apply_to_source(SOURCE, {name: 0.5, "count": 5})
    assert written == ["count"]
    assert [n for n, _ in skipped] == [name]
    assert written_as in skipped[0][1]
    # The one it could write still landed: one such parameter must not block the rest.
    assert defaults(out)["count"] == 5
    assert written_as in out


def test_values_already_equal_to_the_default_leave_no_diff():
    out, written, _ = edit.apply_to_source(SOURCE, {"count": 4, "height": 42})
    assert written == []
    assert out == SOURCE


def test_an_unknown_parameter_is_an_error_not_a_skip():
    with pytest.raises(edit.EditError, match="no parameter named nope"):
        edit.apply_to_source(SOURCE, {"nope": 1})


def test_a_source_with_no_part_says_so():
    with pytest.raises(edit.EditError, match="no @part function"):
        edit.apply_to_source("def thing(count=4):\n    return count\n", {"count": 5})


def test_non_ascii_earlier_on_the_line_does_not_shift_the_offsets():
    """col_offset counts utf-8 bytes, not characters.

    The degree sign has to sit *before* the number for this to test anything: it is two
    bytes, so slicing the line by character index would cut one character short and
    write the new value into the middle of the previous argument.
    """
    source = 'from nurb import *\n\n\n@part\ndef thing(label="45°", count=4):\n    return count\n'
    out, _, _ = edit.apply_to_source(source, {"count": 6})
    assert out == source.replace("count=4", "count=6")


def test_a_default_that_is_a_literal_but_not_a_number_says_what_it_is():
    """"Change False itself" is advice about nothing: a literal has no source to edit."""
    out, written, skipped = edit.apply_to_source(SOURCE, {"draft": True})
    assert out == SOURCE and written == []
    assert skipped == [("draft", "defaults to False, which is not a number.")]
