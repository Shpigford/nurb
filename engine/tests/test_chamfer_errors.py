"""The kernel's chamfer message is wrong about the cause, so nurb says the rest.

"Failed creating a chamfer, try a smaller length value(s)" points at the length, and the
doctrine is explicit that following it would never have found the real rule: a chamfer
fails for room. Shrinking it is the response that makes a part quietly worse, because a
0.4mm chamfer lands and then prints as a defect. This is the most common way a part
stops building, which is what makes the message worth owning.
"""

from build123d import Box, Pos
import pytest

import sys

import nurb
from nurb.polish import KERNEL

# `from nurb import polish` hands back the function: `__init__` binds that name over its
# own submodule. The module object is what the monkeypatch below needs.
polish_mod = sys.modules["nurb.polish"]


def tight_solid():
    """A step 1.6mm tall: less than the 2mm two 1mm chamfers need between them."""
    return Box(40, 30, 10) + Pos(0, 0, 5 + 0.8) * Box(36, 26, 1.6)


def test_the_wrapper_is_what_a_part_file_gets():
    """Only chamfer gets doctrine; fillet keeps build123d's own recovery advice."""
    import build123d

    assert nurb.chamfer is not build123d.chamfer
    assert nurb.fillet is build123d.fillet
    assert nurb.chamfer is polish_mod.chamfer


def test_a_fillet_failure_keeps_its_native_guidance():
    """A fillet radius can be too large, where shrinking it is exactly the right fix."""
    with pytest.raises(ValueError) as exc:
        nurb.fillet(Box(20, 20, 20).edges(), 30.0)
    text = str(exc.value)
    assert "max_fillet()" in text
    assert "polish(shape" not in text


def test_a_successful_chamfer_is_untouched():
    """Same behaviour is the whole promise; only the failure path differs."""
    import build123d

    box = Box(20, 20, 20)
    theirs = build123d.chamfer(box.edges(), 1.0)
    ours = nurb.chamfer(box.edges(), 1.0)
    assert ours.volume == pytest.approx(theirs.volume)


def test_the_failure_keeps_its_type_and_opening_line():
    """`nurb verify` classifies kernel refusals by matching this string.

    Enriching the message must not break that, or a part that fails in the kernel starts
    reading as a part that failed in its own words.
    """
    with pytest.raises(ValueError) as exc:
        nurb.chamfer(tight_solid().edges(), 1.0)
    text = str(exc.value)
    assert text.startswith("Failed creating a chamfer")
    assert any(k in text for k in KERNEL)


def test_a_batch_failure_names_the_room_rule_and_the_batch():
    with pytest.raises(ValueError) as exc:
        nurb.chamfer(tight_solid().edges(), 1.0)
    text = str(exc.value)
    assert "fails for room, not for length" in text
    assert "more than 2mm of face" in text  # 2 * the 1mm asked for
    assert "all or nothing" in text
    assert "polish(shape, edges, 1.0)" in text  # a size is a float, never a bare 1


def test_a_single_edge_gets_the_other_case_instead():
    """Bisecting cannot help one edge, so the advice has to be the vertex case."""
    box = Box(20, 20, 20)
    with pytest.raises(ValueError) as exc:
        nurb.chamfer(min(box.edges(), key=lambda e: e.length), 30.0)
    text = str(exc.value)
    assert "all or nothing" not in text
    assert "four faces and only three edges" in text


def test_a_generator_still_reports_how_many_edges_it_held():
    """The failing call exhausts it, so the count has to be taken before that."""
    solid = tight_solid()
    with pytest.raises(ValueError) as exc:
        nurb.chamfer((e for e in solid.edges()), 1.0)
    assert f"passed {len(solid.edges())} edges" in str(exc.value)


def test_an_unrelated_error_is_not_dressed_up():
    """Only the kernel's refusal gets the doctrine attached."""
    with pytest.raises(Exception) as exc:
        nurb.chamfer(Box(20, 20, 20).edges(), "not a length")
    assert "fails for room" not in str(exc.value)


def test_polish_does_not_pay_for_advice_it_throws_away(monkeypatch):
    """Bisection expects failures, so the guidance must not be built once per attempt."""
    built = []
    real = polish_mod._advice
    monkeypatch.setattr(polish_mod, "_advice", lambda *a: built.append(a) or real(*a))
    out = polish_mod.polish(tight_solid(), tight_solid().edges(), 1.0)
    assert out is not None
    assert built == []
