"""The hanging interface, asserted rather than read.

Every Notch part carries the same dovetail channels, and a part whose channels are a
tenth of a millimetre off pitch builds, exports, checks clean and does not go on the
wall. The catalog cards recorded a hand-checked `Fit:` line per part for exactly this
reason; this file is that line, run.

The numbers here are deliberately literals and not imports from `examples/notch/system`.
A fit test that reads the same constant the part built from agrees with the part however
wrong the constant is. These three came off a bracket and out of the shipped Fusion
ChannelTool, and they are what the wall actually is.
"""

import pathlib

import pytest

from nurb import builder, checks

PARTS = pathlib.Path(__file__).parents[1] / "examples" / "notch" / "parts"

PITCH = 25.16  # on-center spacing across a run of Wall Control brackets
FLOOR_X = -4.2  # bracket plate thickness 4.0 plus 0.2 depth clearance
SPAN = 21.06  # pocket width 20.56 plus 0.25 side clearance either side
EPS = 1e-3


# What Fusion measured, off the catalog cards, as (width, height, projection). These are
# the closest thing to the STLs themselves: the exports live in the Fusion project and
# not in this repo, so the recorded bounding box is the dimension check. The cards round
# to a tenth, which is why the tolerance is 0.05 and not something tighter.
FUSION = {
    "hook_scissors": (25.16, 30.0, 34.0),
    "hook_utility": (25.16, 30.0, 31.0),
    "hook_utility_long": (25.16, 35.0, 51.0),
    "shelf_gridfinity": (100.6, 42.0, 94.0),
    "shelf_gridfinity_2x1": (100.6, 35.0, 52.0),
    "shelf_gridfinity_3x2": (151.0, 42.0, 94.0),
    "shelf_basic": (100.6, 45.0, 106.0),
    "holder_pliers": (151.0, 30.0, 30.0),
    "holder_tall_tools": (125.8, 55.0, 27.0),
    "holder_calipers": (50.3, 30.0, 20.0),
    "holder_bambu_scraper": (50.0, 32.0, 18.5),
    "holder_needle_files": (50.3, 28.0, 20.5),
    "holder_filament_spool": (50.3, 65.0, 160.0),
    "mount_tape_measure": (50.3, 28.0, 14.0),
    "mount_akrobin_rail": (226.4, 55.0, 8.75),
    "bin_small_parts": (75.5, 60.0, 65.0),
}


def parts():
    return sorted(p for p in PARTS.glob("*.py") if not p.name.startswith("_"))


def ids(paths):
    return [p.stem for p in paths]


def floors(shape):
    """Every face lying in the channel floor plane, as (y center, y span)."""
    out = []
    for face in shape.faces():
        box = face.bounding_box()
        if abs(box.min.X - FLOOR_X) < EPS and abs(box.max.X - FLOOR_X) < EPS:
            out.append((round(face.center().Y, 4), round(box.size.Y, 4)))
    return sorted(out)


def misfits(shape, count, step=1):
    """Everything wrong with a part's hanging interface. Empty means it goes on the wall.

    Four failures, and only the first is the one anyone thinks to check. A part can have
    every floor on exact pitch and still be wrong because it grew a fifth floor where
    four were wanted, or because one floor came out narrow after a boolean clipped it.
    """
    found = floors(shape)
    want = [round(k * step * PITCH, 4) for k in range(count)]
    problems = []
    if len(found) != count:
        problems.append(f"{len(found)} channel floors, expected {count}")
    for (y, span), expected in zip(found, want):
        if abs(y - expected) > EPS:
            problems.append(f"floor at y={y}, expected {expected}")
        if abs(span - SPAN) > EPS:
            problems.append(f"floor at y={y} spans {span}mm, expected {SPAN}mm")
    return problems


def brackets(path, overrides=None):
    """What a configuration ends up with for `bracket_count` and `bracket_step`.

    Read off the signature, since the keyword defaults are the parameters, and there is
    no second place to look.
    """
    declared = {**builder.load(path)._nurb.params, **(overrides or {})}
    return int(declared.get("bracket_count", 1)), int(declared.get("bracket_step", 1))


@pytest.mark.parametrize("path", parts(), ids=ids(parts()))
def test_every_configuration_hangs_on_the_wall(path):
    """One solid, and channels a real bracket run would take, for every shipped config."""
    for name, overrides, _ in checks.configurations(path):
        shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
        assert len(shape.solids()) == 1, f"{name}: {len(shape.solids())} solids"
        assert misfits(shape, *brackets(path, overrides)) == [], name


@pytest.mark.parametrize("path", parts(), ids=ids(parts()))
def test_every_configuration_matches_what_fusion_measured(path):
    """A port that builds is not a port that agrees with the part it came from."""
    for name, overrides, _ in checks.configurations(path):
        if name not in FUSION:
            continue
        shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
        size = shape.bounding_box().size
        width, height, projection = FUSION[name]
        assert (size.Y, size.Z, size.X) == pytest.approx(
            (width, height, projection), abs=0.05
        ), name


def test_the_whole_catalog_is_covered():
    """Sixteen catalog entries, twelve part files, and nothing quietly dropped."""
    shipped = {name for path in parts() for name, _, _ in checks.configurations(path)}
    assert set(FUSION) - shipped == set(), "catalog entries with no configuration"


@pytest.mark.parametrize("path", parts(), ids=ids(parts()))
def test_every_configuration_checks_clean(path):
    """Zero findings is the bar. A rule firing at a part that prints is a rule bug."""
    for name, overrides, ctx in checks.configurations(path):
        shape, _, _ = builder.build(path, overrides=overrides or None, draft=False)
        found = checks.run(shape, ctx)
        assert found == [], f"{name}: " + "; ".join(str(f) for f in found)


KERNEL = ("Failed creating a chamfer", "Failed creating a fillet", "BRep_API")


@pytest.mark.parametrize("path", parts(), ids=ids(parts()))
def test_the_channel_run_grows(path):
    """Growth is what catches a frozen selector; shrinking alone passes a broken part.

    Only upward. Every part has a floor under `bracket_count` somewhere, since a pocket
    row or a grid has to fit between the brackets, and those floors are guarded per part.

    A part is allowed to refuse to grow, because one or two of them have a width tuned
    against a real object rather than derived from the bracket run. What it is not
    allowed to do is refuse in the kernel's words: a guard that names the parameter and
    the fix is a design decision, and `BRep_API: command not done` is a missing guard.
    """
    count, step = brackets(path)
    for grown in (count + 1, count + 2):
        try:
            shape, _, _ = builder.build(path, overrides={"bracket_count": grown}, draft=False)
        except ValueError as exc:
            assert not any(k in str(exc) for k in KERNEL), f"bracket_count={grown}: {exc}"
            continue
        assert len(shape.solids()) == 1, f"bracket_count={grown}"
        assert misfits(shape, grown, step) == [], f"bracket_count={grown}"


def test_the_fit_check_catches_a_pitch_error():
    """The assertion has to be able to fail, or it is decoration.

    A tenth of a millimetre per interval is the size of error that gets past a reading
    of the source and past every printability rule, and it is what stops the fourth
    bracket entering its channel.
    """
    from build123d import Box, Part, Polygon, Pos, extrude

    def slab(pitch):
        body = Pos(-3, 1.5 * PITCH, -15) * Box(6, 4 * PITCH, 30)
        cut = Polygon(
            (0, 6.38), (FLOOR_X, 10.53), (FLOOR_X, -10.53), (0, -6.38), align=None
        )
        one = Pos(0, 0, -3) * extrude(cut, -28)
        return body - (Part() + [Pos(0, k * pitch, 0) * one for k in range(4)])

    assert misfits(slab(PITCH), 4) == []
    wrong = misfits(slab(25.06), 4)
    assert wrong, "a 0.1mm per interval pitch error went unnoticed"
    assert "expected 25.16" in wrong[0]
