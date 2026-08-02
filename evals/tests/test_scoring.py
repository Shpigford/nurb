"""The scorer's fairness, proven with reference solutions.

Every flawed solution here is a negative control: the assertion has to be able to
fail, or it is decoration. Each flaw must be caught in the stage built to catch it,
and the totals must order the way a user would rank the parts.
"""

import json
import pathlib
import shutil
import subprocess
import sys
import time

import pytest

from nurb_evals import grade, scoring

EVALS = pathlib.Path(__file__).parents[1]
TASK = EVALS / "tasks" / "cable_clip"
SOLUTIONS = pathlib.Path(__file__).parent / "solutions" / "cable_clip"

task = scoring.load_task(TASK)

# The reference solutions are written for an 8.0mm bundle, so the tests pin the seed
# that produces one rather than hardcoding a magic number that could drift.
SEED = next(s for s in range(1000) if task.instance(s).dims["bundle"] == 8.0)


def score(name, seed=None):
    return scoring.grade(SOLUTIONS / f"{name}.py", TASK, SEED if seed is None else seed)


def test_the_reference_solution_scores_full_marks():
    result = score("good")
    assert result["score"] == 1.0, result
    assert result["stages"] == {"lint": 1.0, "dims": 1.0, "flex": 1.0}
    assert result["misfits"] == [] and result["findings"] == []


def test_a_doctrine_polished_part_also_scores_full_marks():
    """Fable's first real trial: chamfered outside edges, square fit geometry, exactly
    what the shipped skill teaches. The first matrix run scored it 0.633 because three
    checks measured top-face spans, which re-measure the chamfer instead of the part.
    Every stated dimension must survive the doctrine's polish pass."""
    result = score("polished")
    assert result["score"] == 1.0, result
    assert result["stages"] == {"lint": 1.0, "dims": 1.0, "flex": 1.0}


def test_a_narrow_channel_is_caught_by_the_dimension_stage():
    result = score("wrong_dim")
    assert result["stages"]["dims"] < 1.0
    assert any("channel floor" in m for m in result["misfits"])
    assert result["score"] < score("good")["score"]


def test_a_solid_block_with_the_right_bbox_still_fails():
    """The bounding box alone must never be enough to pass."""
    result = score("no_channel")
    assert result["stages"]["dims"] < 1.0
    assert any("channel floor" in m for m in result["misfits"])
    assert any("volume" in m for m in result["misfits"])


def test_a_closed_tunnel_is_caught_by_the_open_top_check():
    """The cheat an adversarial pass actually found: roof the channel 1mm shy of the
    top and every other assertion stays green."""
    result = score("roofed")
    assert result["stages"]["dims"] < 1.0
    assert any("roofed over" in m for m in result["misfits"])
    assert result["score"] < score("good")["score"]


def test_a_channel_blocked_at_one_end_is_caught():
    result = score("blocked_channel")
    assert result["stages"]["dims"] < 1.0
    assert any("channel floor" in m for m in result["misfits"])


def test_asymmetric_wall_thicknesses_are_caught():
    result = score("wrong_walls")
    assert result["stages"]["dims"] < 1.0
    assert any("walls" in m for m in result["misfits"])


def test_a_half_height_wall_is_caught():
    """The verifier's cheat: lop the top 45% off the non-tab wall and the other wall
    still satisfies the bounding box while the deficit hides in the volume band."""
    result = score("short_wall")
    assert result["stages"]["dims"] < 1.0
    assert any("tall" in m for m in result["misfits"])


def test_an_off_center_mounting_hole_is_caught():
    result = score("offset_hole")
    assert result["stages"]["dims"] < 1.0
    assert any("centered" in m and "through-hole" in m for m in result["misfits"])


def test_a_decorative_parameter_is_caught_by_the_flex_stage():
    result = score("hardcoded")
    assert result["stages"]["dims"] == 1.0, "correct at defaults by construction"
    assert result["stages"]["flex"] < 1.0
    assert any("does not track" in p for p in result["flex_problems"])


def test_a_flex_rebuild_with_multiple_solids_is_caught():
    result = score("flex_two_solids")
    assert result["stages"]["dims"] == 1.0, "the default build is valid"
    assert result["stages"]["flex"] < 1.0
    assert any("2 solids" in p for p in result["flex_problems"])


def test_a_later_flex_crash_keeps_the_completed_default_build():
    result = score("crashes_on_flex")
    assert result["built"] is True and result["error"] is None
    assert result["stages"] == {"lint": 1.0, "dims": 1.0, "flex": 0.0}
    assert all("builder crashed" in p for p in result["flex_problems"])


def test_a_later_flex_timeout_keeps_the_completed_default_build():
    started = time.monotonic()
    result = grade.run(SOLUTIONS / "hangs_on_flex.py", TASK, SEED, timeout=16.0)
    assert time.monotonic() - started < 22.0
    assert result["built"] is True and result["error"] is None
    assert result["stages"] == {"lint": 1.0, "dims": 1.0, "flex": 0.0}
    assert all("timeout" in p for p in result["flex_problems"])


def test_counterbored_rims_do_not_fake_a_full_diameter_through_hole():
    result = score("undersized_hole")
    assert result["stages"]["dims"] < 1.0
    assert any("through-hole" in p for p in result["misfits"])


def test_an_unprintable_ledge_is_caught_by_the_lint_stage():
    result = score("overhang")
    assert result["stages"]["lint"] < 1.0
    assert any(f["severity"] == "fail" for f in result["findings"])


def test_the_gate_zeroes_what_does_not_build():
    for name, fragment in (("two_solids", "2 solids"), ("raises", "refusing to build")):
        result = score(name)
        assert result["score"] == 0.0, name
        assert fragment in result["error"], name


def test_scores_order_the_way_a_user_would_rank_the_parts():
    names = ("good", "hardcoded", "wrong_dim", "no_channel", "overhang", "raises")
    totals = [score(n)["score"] for n in names]
    assert totals == sorted(totals, reverse=True), dict(zip(names, totals))


def test_a_hanging_part_times_out_at_zero():
    started = time.monotonic()
    result = grade.run(SOLUTIONS / "hangs.py", TASK, SEED, timeout=10.0)
    assert time.monotonic() - started < 30.0
    assert result["score"] == 0.0
    assert "timeout" in result["error"]


def test_candidate_stdout_cannot_forge_the_grader_verdict():
    result = grade.run(SOLUTIONS / "spoofed.py", TASK, SEED, timeout=10.0)
    assert result["score"] == 0.0
    assert result["built"] is False


def test_candidate_cannot_mutate_the_scorers_check_registry():
    result = score("muted_checks")
    assert result["stages"]["lint"] < 1.0
    assert any(f["severity"] == "fail" for f in result["findings"])


def test_the_grade_cli_prints_parseable_json():
    done = subprocess.run(
        [sys.executable, "-m", "nurb_evals.grade", str(SOLUTIONS / "good.py"), str(TASK), str(SEED)],
        capture_output=True,
        text=True,
        cwd=EVALS,
    )
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    assert result["score"] == 1.0
    assert set(result["stages"]) == {"lint", "dims", "flex"}


def test_a_muting_card_changes_nothing(tmp_path):
    """A model that writes its own card must not be able to grade itself. The card
    below would silence every rule if the scorer read it the way `nurb check` does."""
    part = tmp_path / "cable_clip.py"
    shutil.copy(SOLUTIONS / "overhang.py", part)
    part.with_suffix(".md").write_text(
        "# cable_clip\n\n```toml\n[part]\nmin_wall = 0.0\nsliver_area = 0.0\n"
        '[accepted]\noverhang = 9\nfloating = 9\n```\n',
        encoding="utf-8",
    )
    with_card = scoring.grade(part, TASK, SEED)
    without = score("overhang")
    assert with_card["score"] == without["score"]
    assert with_card["stages"]["lint"] < 1.0


def test_the_seed_drives_instruction_and_assertions_together():
    a, b = task.instance(SEED), task.instance(SEED)
    assert a == b, "same seed, same instance"
    other = next(s for s in range(1000) if task.instance(s).dims["bundle"] != 8.0)
    changed = task.instance(other)
    assert changed.dims["bundle"] != 8.0
    for inst in (a, changed):
        assert f"{inst.dims['bundle']} mm across" in inst.instruction
        assert str(inst.dims["channel"]) in inst.instruction
        assert f"value = {inst.dims['bundle']}" in inst.measurements


def test_materialize_writes_a_startable_project(tmp_path):
    root = task.materialize(SEED, tmp_path / "project")
    assert (root / "parts").is_dir()
    assert "bambu_p1s" in (root / "printer.toml").read_text()
    text = (root / "measurements.toml").read_text()
    assert "value = 8.0" in text and "how =" in text, "a measurement without provenance is a guess"


def test_an_orphaned_candidate_exits_instead_of_spinning(tmp_path):
    """The candidate runs in its own session so the scorer can kill it selectively,
    which also means nothing kills it when the scorer dies first. It has to notice
    the orphaning itself, or a hanging part leaves a process spinning forever."""
    import os
    import signal

    request = tmp_path / "request.json"
    request.write_text("[{}]", encoding="utf-8")
    wrapper = (
        "import subprocess, sys\n"
        f"p = subprocess.Popen([sys.executable, '-m', 'nurb_evals.candidate',"
        f" {str(SOLUTIONS / 'hangs.py')!r}, {str(request)!r}, {str(tmp_path / 'out')!r}],"
        " start_new_session=True)\n"
        "print(p.pid)\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", wrapper], capture_output=True, text=True, timeout=30
    )
    pid = int(done.stdout)

    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.5)
    os.kill(pid, signal.SIGKILL)
    pytest.fail("the orphaned candidate was still running 20s after its parent died")
