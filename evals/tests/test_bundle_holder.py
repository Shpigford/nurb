"""Fairness of the first function task.

bundle_holder states a problem, not a geometry, so its negative controls are broken
functions rather than wrong dimensions: a holder that drops the bundle, one that
cannot be screwed to the wall, one whose screw head has no room, one deaf to its
parameter, and one that works by sheer bulk. Each must be caught in the stage built
to catch it, and the totals must order the way a user would rank the parts: working
beats wasteful beats fixed-size beats broken.
"""

import pathlib
import time

from nurb_evals import scoring

EVALS = pathlib.Path(__file__).parents[1]
TASK = EVALS / "tasks" / "bundle_holder"
SOLUTIONS = pathlib.Path(__file__).parent / "solutions" / "bundle_holder"

task = scoring.load_task(TASK)

# Solutions are written for an 8.0mm bundle; pin the seed that produces one.
SEED = next(s for s in range(1000) if task.instance(s).dims["bundle"] == 8.0)


def score(name):
    return scoring.grade(SOLUTIONS / f"{name}.py", TASK, SEED)


def test_the_reference_holder_scores_full_marks():
    result = score("good")
    assert result["score"] == 1.0, result
    assert result["stages"] == {"lint": 1.0, "dims": 1.0, "flex": 1.0}
    assert result["misfits"] == [] and result["findings"] == []


def test_a_shelf_without_a_lip_is_not_retention():
    """Blocked down is not held: the bundle rolls off the open front."""
    result = score("shelf_only")
    assert result["stages"]["dims"] < 1.0
    assert any("not retained" in m for m in result["misfits"])
    assert all("nowhere to sit" not in m for m in result["misfits"]), "it does fit, it just escapes"


def test_a_holder_with_no_screw_hole_cannot_mount():
    result = score("no_hole")
    assert result["stages"]["dims"] < 1.0
    assert any("screw bore" in m for m in result["misfits"])


def test_a_shallow_counterbore_does_not_fake_the_required_bore_diameter():
    result = score("undersized_bore")
    assert result["stages"]["dims"] < 1.0
    assert any("screw bore" in m for m in result["misfits"])


def test_a_bore_behind_the_lip_has_no_head_room():
    """The bore is real and seated; the screw can still never be driven."""
    result = score("blocked_head")
    assert result["stages"]["dims"] < 1.0
    assert result["misfits"] and all("head-and-driver" in m for m in result["misfits"])


def test_a_snug_hardcoded_tunnel_is_caught_by_the_flex_stage():
    result = score("hardcoded")
    assert result["stages"]["dims"] == 1.0, "correct at the measured size by construction"
    assert result["stages"]["flex"] < 1.0
    assert any("does not track" in p for p in result["flex_problems"])


def test_bulk_is_charged_once_by_the_volume_ladder():
    """Every function check passes; only the material gradient separates the brick
    from the reference, and the flex probes must not charge the bulk again."""
    result = score("bloated")
    assert result["stages"]["flex"] == 1.0
    assert result["stages"]["dims"] < 1.0
    assert result["misfits"] and all("volume" in m for m in result["misfits"])


import pytest


@pytest.mark.parametrize(
    ("cheat", "caught_by"),
    [
        ("septum_tunnel", "retained"),  # hidden septum between fixed sampling stations
        ("single_finger", "retained"),  # 1.4mm finger straddling one lucky station
        ("sealed_membranes", "retained"),  # 0.09mm films sealing the tunnel ends
        ("knife_lip", "retained"),  # 0.15mm foil lip as the only retention
        ("skin_bore", "screw bore"),  # bore skinned over, slots at the old probe points
        ("head_blocker", "head-and-driver"),  # wall between the old 1.0mm head steps
        ("mega_fake", "retained"),  # single finger and skinned bore combined
        ("screw_in_seat", "installed screw"),  # bore dead-center in the bundle's seat
    ],
)
def test_the_adversarial_cheats_stay_dead(cheat, caught_by):
    """Every one of these scored 0.925 or a perfect 1.0 before the scorer was
    hardened: feature-aware stations, blocking along a third of the length on opened
    sections, and the continuous virtual-screw boolean. A user would laugh at a
    photo of any of them, so a score near the pass bar is a scorer bug."""
    result = score(cheat)
    assert result["score"] <= 0.75, result
    assert any(caught_by in m for m in result["misfits"]), result["misfits"]


def test_scores_order_the_way_a_user_would_rank_the_holders():
    names = ("good", "bloated", "hardcoded", "blocked_head", "shelf_only", "no_hole")
    totals = [score(n)["score"] for n in names]
    assert totals == sorted(totals, reverse=True), dict(zip(names, totals))


def test_a_working_but_wasteful_holder_beats_any_broken_one():
    """The function-task ordering promise: bulk costs less than broken function."""
    bloated = score("bloated")["score"]
    for broken in ("blocked_head", "shelf_only", "no_hole"):
        assert bloated > score(broken)["score"], broken


def test_grading_stays_fast_enough_for_the_runner():
    """The retention search runs on mesh cross-sections precisely so grading three
    builds stays a footnote next to a trial's minutes of model time."""
    started = time.monotonic()
    score("good")
    assert time.monotonic() - started < 30.0


def test_the_seed_drives_instruction_and_assertions_together():
    other = next(s for s in range(1000) if task.instance(s).dims["bundle"] != 8.0)
    for inst in (task.instance(SEED), task.instance(other)):
        assert f"{inst.dims['bundle']} mm across" in inst.instruction
        assert str(inst.dims["channel"]) in inst.instruction
        assert str(inst.dims["v1"]) in inst.instruction
        assert f"value = {inst.dims['bundle']}" in inst.measurements


def test_materialize_writes_a_startable_project(tmp_path):
    root = task.materialize(SEED, tmp_path / "project")
    assert (root / "parts").is_dir()
    assert "bambu_p1s" in (root / "printer.toml").read_text()
    assert "value = 8.0" in (root / "measurements.toml").read_text()
    assert (root / "AGENTS.md").read_text().startswith("#")
