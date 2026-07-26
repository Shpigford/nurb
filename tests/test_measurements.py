"""A measurement that is missing has to fail loudly.

The whole point of the file is that an invented dimension produces a part that builds,
checks clean and prints, so nothing downstream catches it. Every test here is about a
refusal to guess.
"""

import pathlib

import pytest

from nurb.measurements import MeasurementError, load, measured

REAL = pathlib.Path(__file__).parents[1] / "examples" / "notch"


def write(tmp_path, body):
    (tmp_path / "measurements.toml").write_text(body)
    return tmp_path


def test_a_value_is_read(tmp_path):
    root = write(tmp_path, '[shelf_depth]\nvalue = 340\nunit = "mm"\nhow = "tape measure"\n')
    assert measured("shelf_depth", start=root) == 340


def test_found_from_a_subdirectory(tmp_path):
    root = write(tmp_path, '[pitch]\nvalue = 25.16\nhow = "calipers"\n')
    deep = root / "parts"
    deep.mkdir()
    assert measured("pitch", start=deep) == 25.16


def test_an_unknown_name_says_what_is_on_file(tmp_path):
    root = write(tmp_path, '[pitch]\nvalue = 25.16\nhow = "calipers"\n')
    with pytest.raises(MeasurementError, match="pitch"):
        measured("burrito_width", start=root)


def test_no_file_at_all_says_how_to_start_one(tmp_path):
    with pytest.raises(MeasurementError, match="measurements.toml"):
        measured("anything", start=tmp_path)


def test_a_value_without_provenance_is_a_guess(tmp_path):
    root = write(tmp_path, "[pitch]\nvalue = 25.16\n")
    with pytest.raises(MeasurementError, match="how it was measured"):
        measured("pitch", start=root)


def test_the_wrong_unit_is_an_error_not_a_conversion(tmp_path):
    root = write(tmp_path, '[pitch]\nvalue = 1.0\nunit = "in"\nhow = "ruler"\n')
    with pytest.raises(MeasurementError, match="mm"):
        measured("pitch", start=root)


def test_no_file_means_nothing_measured_rather_than_an_error(tmp_path):
    assert load(start=tmp_path) == {}


def test_the_search_does_not_leave_the_project(tmp_path):
    """An ancestor's measurements are not this project's.

    Without the stop at the project root the walk runs to the filesystem root and can
    answer with a file from somewhere else entirely, which is a wrong dimension that looks
    right: exactly what this module exists to prevent.
    """
    write(tmp_path, '[pitch]\nvalue = 99.0\nhow = "somebody else\'s wall"\n')
    project = tmp_path / "project"
    (project / "parts").mkdir(parents=True)
    with pytest.raises(MeasurementError, match="no measurements.toml"):
        measured("pitch", start=project / "parts")


def test_broken_toml_says_which_file(tmp_path):
    root = write(tmp_path, "[pitch\nvalue = 1\n")
    with pytest.raises(MeasurementError, match="measurements.toml"):
        measured("pitch", start=root)


def test_the_real_measurements_carry_provenance():
    """Every value in the worked example says where it came from."""
    book = load(start=REAL)
    assert book, "examples/notch should have measurements"
    for name, entry in book.items():
        assert entry.get("how"), f"{name} has no provenance"
        assert entry.get("unit", "mm") == "mm", name


def test_the_bracket_pitch_is_what_the_library_was_built_on():
    assert measured("bracket_pitch", start=REAL) == 25.16
