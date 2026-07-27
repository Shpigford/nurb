"""`nurb extract` finds what a family ended up saying twice.

The two things it has to get right pull against each other: a construction written out
with different local names in two parts is the same construction, and two calls with the
same arity to different functions are not. So names a part binds are canonicalized and
names it imports are not.
"""

import pathlib

from nurb import extract


def write(tmp_path, name, body):
    path = tmp_path / f"{name}.py"
    path.write_text(body)
    return path


SLAB = """from nurb import *

from system import BLOCK_WIDTH, channels


@part
def one(bracket_count=2, item_height=30.0, item_depth=6.0):
    y0, y1 = -BLOCK_WIDTH / 2, (bracket_count - 0.5) * BLOCK_WIDTH
    slab = Pos(-item_depth / 2, (y0 + y1) / 2, -item_height / 2) * Box(
        item_depth, y1 - y0, item_height
    )
    back = slab - channels(bracket_count, item_height)
    return back
"""

# The same three statements, every local renamed and the part given other parameters.
RENAMED = """from nurb import *

from system import BLOCK_WIDTH, channels


@part
def two(brackets=4, height=42.0, depth=6.0):
    lo, hi = -BLOCK_WIDTH / 2, (brackets - 0.5) * BLOCK_WIDTH
    plate = Pos(-depth / 2, (lo + hi) / 2, -height / 2) * Box(depth, hi - lo, height)
    body = plate - channels(brackets, height)
    return body
"""


def test_the_same_construction_under_other_names_is_one_candidate(tmp_path):
    paths = [write(tmp_path, "one", SLAB), write(tmp_path, "two", RENAMED)]
    found = extract.duplication(paths)
    assert len(found) == 1
    assert {p.stem for p, *_ in found[0]["sites"]} == {"one", "two"}
    # Four, not three: `return back` and `return body` are the same statement too.
    assert found[0]["statements"] == 4


def test_imports_are_not_a_system(tmp_path):
    """Two parts in a family import the same names by definition."""
    paths = [write(tmp_path, "one", SLAB), write(tmp_path, "two", RENAMED)]
    for run in extract.duplication(paths):
        path, start, end, _ = run["sites"][0]
        assert "import" not in extract.source(path, start, end)


def test_different_functions_with_the_same_arity_do_not_match(tmp_path):
    """`Box(a, b, c)` and `Pos(a, b, c)` are not the same statement."""
    boxes = "@part\ndef one(a=1.0, b=2.0, c=3.0):\n    x = Box(a, b, c)\n    y = Box(a, b, c)\n    return x + y\n"
    poses = "@part\ndef two(a=1.0, b=2.0, c=3.0):\n    x = Pos(a, b, c)\n    y = Pos(a, b, c)\n    return x + y\n"
    paths = [write(tmp_path, "one", boxes), write(tmp_path, "two", poses)]
    assert extract.duplication(paths) == []


def test_nothing_shared_reports_nothing(tmp_path):
    one = "@part\ndef one(w=10.0):\n    body = Box(w, w, w)\n    return chamfer(body.edges(), 1)\n"
    two = "@part\ndef two(r=4.0):\n    disc = Circle(r)\n    return extrude(disc, 10)\n"
    paths = [write(tmp_path, "one", one), write(tmp_path, "two", two)]
    assert extract.duplication(paths) == []


def test_a_run_inside_a_longer_run_is_not_reported_twice(tmp_path):
    """A five-statement match contains four four-statement matches."""
    paths = [write(tmp_path, "one", SLAB), write(tmp_path, "two", RENAMED)]
    found = extract.duplication(paths)
    starts = [(p.stem, line) for run in found for p, line, _, _ in run["sites"]]
    assert len(starts) == len(set(starts))


def test_alpha_equivalence_preserves_data_flow_across_statements(tmp_path):
    """Swapping two established locals is behavior, not another spelling of the same code."""
    one = (
        "def one(seed):\n"
        "    left = make(seed)\n"
        "    right = transform(left)\n"
        "    return combine(left, right)\n"
    )
    swapped = (
        "def swapped(source):\n"
        "    first = make(source)\n"
        "    second = transform(first)\n"
        "    return combine(second, first)\n"
    )
    found = extract.duplication(
        [write(tmp_path, "one", one), write(tmp_path, "swapped", swapped)]
    )
    assert max(run["statements"] for run in found) == 2


def test_overlap_in_another_file_is_still_reported(tmp_path):
    """A long A/B match does not account for the overlapping suffix also present in C."""
    one = (
        "def one(seed):\n"
        "    a = first(seed)\n"
        "    b = second(a)\n"
        "    c = third(b)\n"
        "    return fourth(c)\n"
    )
    two = (
        "def two(source):\n"
        "    x = first(source)\n"
        "    y = second(x)\n"
        "    z = third(y)\n"
        "    return fourth(z)\n"
    )
    three = "def three(seed):\n    result = third(seed)\n    return fourth(result)\n"
    found = extract.duplication(
        [
            write(tmp_path, "one", one),
            write(tmp_path, "two", two),
            write(tmp_path, "three", three),
        ]
    )
    assert any(
        run["statements"] == 2
        and {path.stem for path, *_ in run["sites"]} == {"one", "two", "three"}
        for run in found
    )


def test_it_runs_over_the_real_library():
    """Whatever it reports, it must not fall over on real parts."""
    parts = pathlib.Path(__file__).parents[1] / "examples" / "notch" / "parts"
    found = extract.duplication(sorted(parts.glob("*.py")))
    for run in found:
        assert run["statements"] >= extract.MIN_RUN
        assert len({p for p, *_ in run["sites"]}) > 1
