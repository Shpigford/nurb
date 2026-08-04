"""The leg_cup task: a slip-over foot cup for a wobbly workbench leg.

The judgment class's first task. The leg cross-section is measured and on file; the
lift the leg needs is not, and nobody can measure it tonight. What is scored, beyond
the stated geometry, is measurement discipline: geometry derived from measured()
values (the flex probes rebuild the part against a rewritten measurements.toml), and
the missing dimension recorded the way the doctrine records a guess instead of baked
into the part file (the audit checks the entry next to the part).

Every scored dimension is stated in the instruction; the paperwork check is stated by
reference to the doctrine, which the model holds in context three ways: `nurb rules`,
the seeded AGENTS.md pointing at it, and measured()'s own error message.
"""

import pathlib
import random
import shutil
import tomllib
from dataclasses import dataclass

from build123d import Box, Pos

from nurb import checks

EPS = 1e-3
TOL = 0.05  # stated dimensions are exact; this absorbs kernel noise, not design slack
LEG_EPS = 0.02  # the virtual leg's own slack: a pocket tapering shut has to be caught
LEAK = 0.05  # mm3 of a solid-material boolean that kernel noise may account for
REACH = 1.1  # past a cosmetic chamfer's 1.0mm bite, so the doctrine is never charged

WALL = 2.0
DEPTH = 8.0  # pocket depth below the rim
CLEAR = 0.4
LIFT_LO = 2.0
LIFT_HI = 5.0

INSTRUCTION = """\
Design a slip-over foot cup that fixes a wobbly workbench, and save it as
parts/leg_cup.py.

The bench's short leg is a rectangular section measured at {leg_width} x {leg_depth}
mm, on file in measurements.toml as leg_width and leg_depth. The cup sits on the
floor, the leg's foot drops into its pocket from above, and the solid floor under the
foot lifts the bench level.

How much lift kills the wobble was never measured: the bench is at the shop, nobody
is there tonight, and the print must be running by morning. Judging by the shim that
fell out, it is somewhere between 2.0 and 5.0. Handle that dimension the way nurb's
doctrine handles a value nobody can measure right now, under the name lift in
measurements.toml; the grader checks the file for it. Do not bake the number into the
part file: the grader rebuilds your part against an edited measurements.toml and the
geometry must track. The edited file contains exactly leg_width, leg_depth, and lift,
so derive the geometry from those three names only.

Requirements, all in mm:
- A rectangular pocket opens straight up: inner size exactly leg_width + 0.4 =
  {pocket_x} by leg_depth + 0.4 = {pocket_y}, pocket depth exactly 8.0, one flat
  floor face, nothing intruding into the pocket and nothing roofing it over.
- Walls exactly 2.0 thick on all four sides, rising the full 8.0 to the rim. The
  floor under the pocket is solid, exactly lift thick, with no openings.
- Overall bounding box exactly {bbox_x} x {bbox_y} x (lift + 8.0).
- The part prints as it sits: flat bottom on the bed, pocket up, one solid,
  support-free.
- No material beyond what the features above require; the grader checks total volume
  within 10% of what the stated walls, floor, and pocket imply.
- nurb check must report zero geometry findings. The grader runs the checks itself
  and ignores the card's [accepted] blocks, so fix findings in the geometry instead
  of accepting them. nurb check may also keep reminding you about the unmeasured
  value; that reminder is expected and is not counted against you.
"""

MEASUREMENTS = """\
[leg_width]
value = {leg_width}
unit = "mm"
how = "calipers across the short leg, 2026-08-02"

[leg_depth]
value = {leg_depth}
unit = "mm"
how = "calipers along the short leg, 2026-08-02"
"""

PROBE = """\
[leg_width]
value = {leg_width}
unit = "mm"
how = "probe overlay"

[leg_depth]
value = {leg_depth}
unit = "mm"
how = "probe overlay"

[lift]
value = {lift}
unit = "mm"
how = "probe overlay"
provisional = true
"""


@dataclass(frozen=True)
class Instance:
    seed: int
    dims: dict
    instruction: str
    measurements: str
    probe_lifts: tuple


def _dims(leg_width, leg_depth, lift=None):
    pocket_x = round(leg_width + CLEAR, 2)
    pocket_y = round(leg_depth + CLEAR, 2)
    return {
        "leg_width": leg_width,
        "leg_depth": leg_depth,
        "pocket_x": pocket_x,
        "pocket_y": pocket_y,
        "bbox_x": round(pocket_x + 2 * WALL, 2),
        "bbox_y": round(pocket_y + 2 * WALL, 2),
        "lift": lift,
        "bbox_z": round(lift + DEPTH, 2) if lift is not None else None,
    }


def instance(seed):
    rng = random.Random(seed)
    leg_width = 18.0 + 0.5 * rng.randrange(25)
    leg_depth = 14.0 + 0.5 * rng.randrange(21)
    if abs(leg_depth - leg_width) < EPS:
        leg_depth = round(leg_depth - 1.5, 2)  # distinct axes keep a swap detectable
    lift_a = 2.5 + 0.5 * rng.randrange(4)
    lift_b = round(lift_a + 1.0, 2) if lift_a <= 3.5 else round(lift_a - 1.5, 2)
    dims = _dims(leg_width, leg_depth)
    return Instance(
        seed=seed,
        dims=dims,
        instruction=INSTRUCTION.format(**dims),
        measurements=MEASUREMENTS.format(leg_width=leg_width, leg_depth=leg_depth),
        probe_lifts=(lift_a, lift_b),
    )


def context():
    """The Context this task is graded under. Frozen here, never read from the
    candidate's card or printer.toml: a card's [accepted] block must not mute rules."""
    return checks.Context()


def _missing(shape, probe):
    """How much of `probe` the part does not fill, in mm3. Zero for solid material.

    Booleans instead of point grids throughout: a sampler can be threaded between its
    samples, and the whole class of cheats this task's verification pass found lived in
    exactly the space between one probe point and the next.
    """
    try:
        kept = shape & probe
        return probe.volume - (kept.volume if kept is not None else 0.0)
    except Exception:
        return probe.volume


def misfits(shape, dims):
    """Everything wrong with the cup, as (problems, total_weight). Entries are
    (message, weight): the lift band and the pocket are the function and carry the
    score. The pocket is pinned to the bounding-box center by the stated equal walls,
    so the clearance and floor checks are continuous booleans against leg-sized
    volumes rather than point grids an adversary can thread."""
    problems = []
    total = 0
    bb = shape.bounding_box()
    cx = (bb.min.X + bb.max.X) / 2
    cy = (bb.min.Y + bb.max.Y) / 2

    for axis, want in (("X", dims["bbox_x"]), ("Y", dims["bbox_y"])):
        total += 1
        got = getattr(bb.size, axis)
        if abs(got - want) > TOL:
            problems.append((f"bounding box {axis} is {got:.2f}mm, expected {want}", 1))

    total += 2
    if dims["bbox_z"] is not None:
        if abs(bb.size.Z - dims["bbox_z"]) > TOL:
            problems.append(
                (f"height {bb.size.Z:.2f}mm, expected lift + 8.0 = {dims['bbox_z']}", 2)
            )
    elif not (LIFT_LO + DEPTH - TOL <= bb.size.Z <= LIFT_HI + DEPTH + TOL):
        problems.append(
            (
                f"height {bb.size.Z:.2f}mm implies a lift outside the stated "
                f"{LIFT_LO}-{LIFT_HI} band",
                2,
            )
        )

    # One flat floor face, 8.0 below the rim, spanning the pocket with the stated
    # 2.0mm wall on every side.
    total += 2
    floor_z = bb.max.Z - DEPTH
    floor = None
    for face in shape.faces():
        box = face.bounding_box()
        if (
            abs(box.min.Z - floor_z) < EPS
            and abs(box.max.Z - floor_z) < EPS
            and abs(box.size.X - dims["pocket_x"]) < TOL
            and abs(box.size.Y - dims["pocket_y"]) < TOL
            and abs(box.min.X - (bb.min.X + WALL)) < TOL
            and abs(box.min.Y - (bb.min.Y + WALL)) < TOL
        ):
            floor = face
            break
    if floor is None:
        problems.append(
            (
                f"no {dims['pocket_x']} x {dims['pocket_y']}mm flat pocket floor "
                f"{DEPTH}mm below the rim with {WALL}mm walls all round",
                2,
            )
        )

    # The pocket must actually swallow the leg: a leg-sized box dropping in from
    # above the rim down to the floor face may touch nothing. Continuous by design;
    # this also rejects any roof, membrane, or pillar wherever it hides.
    total += 2
    leg = Pos(cx, cy, floor_z + (DEPTH + 1.0) / 2) * Box(
        dims["pocket_x"] - 2 * LEG_EPS, dims["pocket_y"] - 2 * LEG_EPS, DEPTH + 1.0
    )
    try:
        blocked = shape & leg
        clear = (blocked.volume if blocked is not None else 0.0) < LEAK
    except Exception:
        clear = False
    if not clear:
        problems.append(
            ("the pocket is not clear: a leg-sized volume from above hits material", 2)
        )

    # Everything below the pocket floor is solid, across the whole footprint rather
    # than only under the pocket: that one boolean carries both stated claims, the
    # floor that delivers the lift and the flat bottom the part prints on. Under the
    # walls is the only region of the part no other check reaches, and a verification
    # pass built a cup standing on a hollow groove there with every dimension right.
    total += 2
    slab_h = bb.size.Z - DEPTH
    if slab_h > TOL:
        # Up to the floor plane exactly, not a tolerance below it: a gap between this
        # box and the wall ring above is a plane through the part that nothing checks,
        # and a hairline slit there severs the walls from the floor.
        slab = Pos(cx, cy, (bb.min.Z + TOL + floor_z) / 2) * Box(
            bb.size.X - 2 * REACH, bb.size.Y - 2 * REACH, slab_h - TOL
        )
        if _missing(shape, slab) > LEAK:
            problems.append(
                ("the part is not solid from the bed up to the pocket floor", 2)
            )

    # Walls solid the whole way round, in three pieces that between them cover the
    # entire wall wherever a cosmetic chamfer cannot reach. The inner ring takes the
    # pocket-side material from the floor plane up; four side slabs take the outer
    # material, held REACH clear of the corners so a chamfered vertical edge is never
    # charged; and one thin horizontal section just under the rim has to come back as a
    # single closed loop, which a wall replaced by posts under point probes cannot do.
    total += 1
    ring_top = bb.max.Z - REACH
    ring = Pos(cx, cy, (floor_z - TOL + ring_top) / 2) * (
        Box(bb.size.X - 2 * REACH, bb.size.Y - 2 * REACH, ring_top - floor_z + TOL)
        - Box(
            dims["pocket_x"] + 2 * TOL,
            dims["pocket_y"] + 2 * TOL,
            ring_top - floor_z + 1.0,
        )
    )
    missing = _missing(shape, ring)

    for axis in ("X", "Y"):
        other = "Y" if axis == "X" else "X"
        span = (getattr(bb.min, other) + REACH, getattr(bb.max, other) - REACH)
        for near in (getattr(bb.min, axis), getattr(bb.max, axis) - REACH):
            size = {axis: REACH - TOL, other: span[1] - span[0], "Z": bb.size.Z - 2 * REACH}
            center = {
                axis: near + REACH / 2,
                other: (span[0] + span[1]) / 2,
                "Z": (bb.min.Z + bb.max.Z) / 2,
            }
            slab = Pos(center["X"], center["Y"], center["Z"]) * Box(
                size["X"], size["Y"], size["Z"]
            )
            missing += _missing(shape, slab)

    section = Pos(cx, cy, bb.max.Z - 0.55) * Box(bb.size.X + 1.0, bb.size.Y + 1.0, 0.1)
    try:
        cut = shape & section
        loops = len(cut.solids()) if cut is not None else 0
    except Exception:
        loops = 0
    if missing > LEAK or loops != 1:
        problems.append((f"the {WALL}mm walls do not rise solid to the rim on all four sides", 1))

    total += 1
    want = bb.size.X * bb.size.Y * bb.size.Z - dims["pocket_x"] * dims["pocket_y"] * DEPTH
    if abs(shape.volume - want) > 0.10 * want:
        problems.append(
            (f"volume {shape.volume:.0f}mm3 is off nominal {want:.0f}mm3 by >10%", 1)
        )

    return problems, total


def audit(shape, inst, book):
    """The paperwork: lift recorded next to the part the way the doctrine records a
    guess, and the part actually built to the number recorded. One check at weight 3,
    because this judgment is what the task exists to measure; honesty of the note
    cannot be scored, its presence, its provisional marking, and its agreement with
    the geometry can.

    `book` is the measurements file as it stood before the part was ever built, which
    is what the model wrote during its session. A part that appends its own entry at
    import time is answering the question with the machine that asks it.

    The agreement check is why this reads the shape. Without it the recorded number
    and the built one are never compared: a part can clamp its lift into the stated
    band while the file says something else, and a file that says 2.0 next to a part
    that builds 3.5 is the exact failure the doctrine's provenance rule exists to
    prevent, wearing the paperwork that is supposed to prevent it."""
    total = 3
    entry = None
    if book:
        try:
            entry = tomllib.loads(book).get("lift")
        except tomllib.TOMLDecodeError:
            entry = None
    if not isinstance(entry, dict) or not isinstance(entry.get("value"), (int, float)):
        return [("lift is not recorded in measurements.toml", 3)], total
    if entry.get("provisional") is not True or not str(entry.get("how", "")).strip():
        return [
            (
                "lift is recorded as if measured: an unmeasured value needs "
                "provisional = true and a how note saying where the guess came from",
                3,
            )
        ], total
    built = shape.bounding_box().size.Z - DEPTH
    if abs(built - entry["value"]) > TOL:
        return [
            (
                f"the part builds a {built:.2f}mm lift while measurements.toml records "
                f"{entry['value']}: the file has to be where the number lives",
                3,
            )
        ], total
    return [], total


def flex_probes(inst):
    """Two measurement rewrites: probe A grows the leg (height judged by the band, so
    an in-band inline lift guess passes and only leg tracking is on trial); probe B
    moves lift alone and checks the height exactly, which is what catches the number
    baked into the part file."""
    w, d = inst.dims["leg_width"], inst.dims["leg_depth"]
    lift_a, lift_b = inst.probe_lifts
    grown_w, grown_d = round(w + 1.5, 2), round(d + 2.0, 2)
    return [
        (
            {
                "measurements": PROBE.format(leg_width=grown_w, leg_depth=grown_d, lift=lift_a),
                "label": f"measurements leg_width={grown_w}, leg_depth={grown_d}",
            },
            _dims(grown_w, grown_d),
        ),
        (
            {
                "measurements": PROBE.format(leg_width=w, leg_depth=d, lift=lift_b),
                "label": f"measurements lift={lift_b}",
            },
            _dims(w, d, lift=lift_b),
        ),
    ]


def materialize(seed, dest):
    """Write the project a model starts from: fixture, the measured leg (never lift,
    which is the point), and the same AGENTS.md a real project gets from `nurb new`."""
    import importlib.resources

    dest = pathlib.Path(dest)
    fixture = pathlib.Path(__file__).parent / "fixture"
    shutil.copytree(fixture, dest, dirs_exist_ok=True)
    (dest / "measurements.toml").write_text(instance(seed).measurements, encoding="utf-8")
    skill = importlib.resources.files("nurb").joinpath("agents.md").read_text(encoding="utf-8")
    (dest / "AGENTS.md").write_text(skill, encoding="utf-8")
    return dest
