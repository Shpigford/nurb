"""`nurb api` is derived, so it cannot drift from what a part file can call.

The point of the command is that an agent stops reading site-packages to find out what
`concave_edges` returns. That only holds if the output is generated from the functions
themselves; a hand-written list would be a second copy of the vocabulary and would go
stale exactly when someone adds to the first one.
"""

import inspect

import build123d
import pytest

import nurb
from nurb import api


@pytest.fixture
def box_stl(tmp_path):
    """A box, because the shadowed `import_stl` takes flat-faced meshes and only those."""
    target = tmp_path / "box.stl"
    build123d.export_stl(build123d.Box(10, 10, 10), str(target))
    return str(target)


def test_own_names_are_whatever_init_adds_to_build123d():
    """Subtraction, not a list. Adding an export to `__init__` shows up here for free."""
    borrowed = set(getattr(build123d, "__all__", ()) or dir(build123d))
    assert set(api.own_names()) == set(nurb.__all__) - borrowed


def test_the_documented_vocabulary_is_the_exported_one():
    """What the doctrine names in prose: part, polish, the convexity pair, measured,
    and the assembly four."""
    assert set(api.own_names()) == {
        "part",
        "reject",
        "polish",
        "crown",
        "is_convex",
        "concave_edges",
        "measured",
        "stand",
        "counterbore",
        "supported",
        "assembly",
        "use",
        "hinge",
        "obstacle",
    }


def test_shadowed_names_are_found_by_identity_not_by_a_list():
    """A part file calls this believing it is build123d's, and it is not."""
    import build123d

    assert set(api.shadowed_names()) == {"chamfer", "import_stl"}
    for name in api.shadowed_names():
        assert getattr(nurb, name) is not getattr(build123d, name)


def test_shadowed_api_preserves_the_build123d_signature():
    """The command exists to give argument order, including optional named arguments."""
    import inspect

    assert inspect.signature(nurb.chamfer) == inspect.signature(build123d.chamfer)


def test_import_stl_is_the_shadow_that_deliberately_differs(box_stl):
    """`chamfer` shadows for the error text; this one shadows to change the answer.

    build123d's returns a `Face`, a sheet of triangles with no volume, and subtracting
    from one segfaults. Preserving that signature would mean preserving the trap, so
    the summary `nurb api` prints has to carry the difference instead.
    """
    assert build123d.import_stl(box_stl).volume == 0.0
    assert nurb.import_stl(box_stl).volume > 0.0
    signature = f"import_stl{inspect.signature(nurb.import_stl)}"
    summary = dict(api.entries()[1])[signature]
    assert "solid" in summary and "nurb scan" in summary


def test_every_entry_carries_a_signature_and_a_sentence():
    """A name with no argument order is the thing that sent the agent to the source."""
    own, shadowed, borrowed = api.entries()
    assert own and shadowed and borrowed
    for sig, summary in own + shadowed + borrowed:
        assert "(" in sig, sig
        assert summary, sig


def test_a_docstring_that_opens_with_its_own_name_is_skipped():
    """build123d's convention. Otherwise `new_edges` is documented by the word 'new_edges'."""
    *_, borrowed = api.entries()
    sig, summary = borrowed[0]
    assert sig.startswith("new_edges(")
    assert summary != "new_edges"
    assert "newly added edges" in summary


def test_report_points_at_the_two_commands_that_answer_the_next_question():
    text = "\n".join(api.report())
    assert "nurb rules" in text  # when to reach for these
    assert "nurb inspect" in text  # what the built part actually looks like


@pytest.mark.parametrize("name", ["polish", "concave_edges", "measured"])
def test_signatures_are_read_off_the_live_function(name):
    """Renaming a parameter changes this output, which is the whole idea."""
    import inspect

    sig, _ = next(s for s in api.entries()[0] if s[0].startswith(name + "("))
    assert sig == f"{name}{inspect.signature(getattr(nurb, name))}"
