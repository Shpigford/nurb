"""Assemblies: placed parts, a joint, and the sweep that catches a jam before a print.

Every rule in checks.py judges one solid being manufactured. Nothing judges two solids
being *used*: a door that cannot open past 45 degrees builds clean, checks clean,
exports watertight and prints beautifully, because no check anywhere holds the door and
its mount in the same hand. The failure is only visible in the motion, and the motion
was in nobody's model. This module puts it in the model.

An assembly is a part file whose function returns placed solids instead of one solid:

    from nurb import *

    @assembly
    def privacy_cover(open_deg=0.0):
        mount = use("prompter_mount")
        door = Pos(0, 30, 24) * Rot(0, 0, 180) * use("prompter_door")
        door = hinge(door, Axis((0, 38, 24), (1, 0, 0)), through=(0, 180), at=open_deg)
        machine = obstacle(Pos(0, -100, -110) * Box(224, 230, 219), "the prompter")
        return mount, door, machine

The joint parameter is an ordinary keyword default, so the viewer's existing slider
already animates it: drag `open_deg` and the door swings in the browser. Nothing in the
viewer knows assemblies exist.

`nurb check` on an assembly runs the sweep instead of the printability rules: each
hinged solid is rotated through its declared range and intersected against everything
else, and the finding reports the angle where it jams and the coordinates of the
contact. The printability rules still run where they belong, on the individual parts.

Collision is measured as intersection volume, so two faces that merely kiss at zero
volume are reported clear; in plastic a zero-clearance pass is already a bind, and the
declared range should carry the same honesty about clearance that a tongue's `fit`
carries about width.
"""

import copy
import functools
import pathlib
import sys
from dataclasses import dataclass, field

from .registry import PartDef, declared, param_docs

# Findings come from checks.py's vocabulary so an assembly's report reads exactly like
# a part's: same severities, same line format, same sorting.
RULE = "motion"


@dataclass
class Hinge:
    solid: object
    axis: object  # build123d Axis
    lo: float
    hi: float
    at: float
    name: str
    step: float
    param: str | None = None  # the keyword that drove `at`, when one did


class _Named(float):
    """A float that remembers which parameter it was.

    The viewer wants to drive a joint without a rebuild, and for that it has to know
    which slider is which hinge. Nothing in `hinge(at=open_deg)` says so -- by the
    time the value arrives it is just 0.0. So the runtime hands the assembly function
    its float arguments wrapped in these, and `hinge` reads the name straight off its
    `at`. Passed through arithmetic the name is lost, which is the right behaviour:
    `at=open_deg / 2` is no longer the slider's own value, and a rebuild is the only
    honest way to pose it.
    """

    __slots__ = ("param",)

    def __new__(cls, value, param):
        self = float.__new__(cls, value)
        self.param = param
        return self


@dataclass
class Scene:
    """What the sweep needs: who moves, about what, and what is in the way."""

    hinges: list = field(default_factory=list)
    statics: list = field(default_factory=list)  # placed parts that do not move
    obstacles: list = field(default_factory=list)  # context geometry, never printed
    uses: tuple = ()  # the part files use() built, so a watcher can rebuild dependents


NODE = "joint{}"  # the GLB node for scene.hinges[i]; the exporter and the payload both speak it


def wire(scene):
    """The joints as the part payload carries them: which GLB node each hinge is,
    about what axis it turns, and which slider drives it.

    This is the viewer's half of the client-side posing contract. With it a joint
    drag is a transform at whatever rate the screen paints, not a rebuild
    round-trip per tick.
    """
    return [
        {
            "node": NODE.format(i),
            "param": h.param,
            "name": h.name,
            "origin": [h.axis.position.X, h.axis.position.Y, h.axis.position.Z],
            "dir": [h.axis.direction.X, h.axis.direction.Y, h.axis.direction.Z],
            "lo": h.lo,
            "hi": h.hi,
            "at": h.at,
        }
        for i, h in enumerate(scene.hinges)
    ]


@dataclass
class _Recorder:
    draft: bool = False
    hinges: dict = field(default_factory=dict)  # id(solid) -> Hinge
    obstacles: dict = field(default_factory=dict)  # id(solid) -> name
    uses: set = field(default_factory=set)  # resolved paths use() has built


_active = []  # the recorder for the @assembly call currently executing, if any


def _recorder(who):
    if not _active:
        raise RuntimeError(f"{who} only means something inside an @assembly function")
    return _active[-1]


# --- the vocabulary an assembly file gets ------------------------------------


def _caller_root():
    """The project of the file that called, found the way the CLI finds it."""
    from .cli import project_root

    frame = sys._getframe(2)
    here = frame.f_globals.get("__file__")
    return project_root(pathlib.Path(here).resolve().parent if here else None)


_built = {}  # (path, stamp, overrides, draft) -> shape

# Geometry can come from outside the part file: measured() reads measurements.toml
# and any part can import from system.py. A cache keyed on the part's mtime alone
# would keep serving the old solid after either of those changed -- silently, which
# is the exact failure measurements.toml exists to prevent.
_SHARED = ("system.py", "measurements.toml")


def _stamp(root, path):
    times = [path.stat().st_mtime_ns]
    for name in _SHARED:
        shared = root / name
        if shared.is_file():
            times.append(shared.stat().st_mtime_ns)
    return max(times)


def use(name, **overrides):
    """Build a sibling part by name and return its solid, placed where it was modelled.

    Cached, so dragging an assembly slider in the viewer does not pay for a rebuild of
    every part it places. The cache stamp covers the part file and the shared files
    that can feed its geometry, so a save to any of them lands on the next build. Each
    call returns a fresh wrapper around the cached geometry, because the caller is
    about to move it and two assemblies sharing one Python object would move each
    other.
    """
    from . import builder

    rec = _recorder("use()")
    root = _caller_root()
    path = root / "parts" / f"{name.replace('-', '_')}.py"
    if not path.is_file():
        raise FileNotFoundError(f"no part named {name!r} ({path} does not exist)")
    rec.uses.add(str(path))
    key = (str(path), _stamp(root, path), tuple(sorted(overrides.items())), rec.draft)
    if key not in _built:
        _built[key] = builder.build(path, overrides=overrides or None, draft=rec.draft)[0]
        # One stamp per file: a save invalidates, history does not accumulate.
        stale = [k for k in _built if k[0] == key[0] and k[1] != key[1]]
        for k in stale:
            del _built[k]
    shape = copy.copy(_built[key])
    shape.label = name
    return shape


def hinge(solid, axis, through, at=0.0, name=None, step=3.0):
    """Declare that this solid rotates about `axis`, and pose it at `at` degrees.

    `through` is the range the assembly claims to reach, and the claim is what the
    sweep tests: motion is checked against the declaration the same way min_wall is
    checked against the card. Positive angles follow the right hand rule about the
    axis direction, so the axis is also how you pick which way is opening.

    `step` is the coarse sweep resolution; the jam angle itself is bisected to a tenth
    of a degree regardless.
    """
    rec = _recorder("hinge()")
    lo, hi = float(through[0]), float(through[1])
    if not lo <= at <= hi:
        raise ValueError(f"hinge posed at {at} degrees, outside its declared ({lo}, {hi})")
    posed = solid.rotate(axis, at) if at else solid
    rec.hinges[id(posed)] = Hinge(
        solid=posed,
        axis=axis,
        lo=lo,
        hi=hi,
        at=float(at),
        name=name or getattr(solid, "label", "") or "the moving part",
        step=float(step),
        param=getattr(at, "param", None),
    )
    return posed


def obstacle(solid, name="an obstacle"):
    """Context geometry: the wall, the machine, the shelf above.

    It collides like anything else and is displayed like anything else. What it is
    not is printed -- an assembly is never exported as one STL anyway, but the name
    keeps the intent readable in the file.
    """
    rec = _recorder("obstacle()")
    rec.obstacles[id(solid)] = name
    solid.label = name
    return solid


def _flatten(result):
    if isinstance(result, (tuple, list)):
        out = []
        for item in result:
            out.extend(_flatten(item))
        return out
    return [result]


def assembly(fn):
    """Mark a function as an assembly. Its keyword defaults are parameters, exactly
    like a part's, so the viewer's sliders drive the pose.

    The function returns its placed solids (a tuple, or one solid); the runtime
    compounds them for display and carries the recorded joints on the compound, which
    is how `nurb check` knows to sweep instead of running the printability rules.
    """
    params, takes_draft = declared(fn)

    @functools.wraps(fn)
    def wrapped(**kwargs):
        from build123d import Compound

        draft = bool(kwargs.pop("draft", False))
        rec = _Recorder(draft=draft)
        _active.append(rec)
        try:
            # Floats go in knowing their own names, so `hinge(at=open_deg)` can tie
            # the joint to the slider that drives it. Bools are ints; leave both.
            call = {
                k: _Named(v, k) if type(v) is float else v for k, v in kwargs.items()
            }
            if takes_draft:
                call["draft"] = draft
            result = fn(**call)
        finally:
            _active.pop()

        solids = _flatten(result)
        returned = {id(s) for s in solids}
        for h in rec.hinges.values():
            if id(h.solid) not in returned:
                raise ValueError(
                    f"hinge({h.name!r}) was declared but the hinged solid was not "
                    f"returned. Return what hinge() returned, not what went in."
                )
        scene = Scene(uses=tuple(sorted(rec.uses)))
        for s in solids:
            if id(s) in rec.hinges:
                scene.hinges.append(rec.hinges[id(s)])
            elif id(s) in rec.obstacles:
                scene.obstacles.append(s)
            else:
                scene.statics.append(s)
        comp = Compound(children=[copy.copy(s) for s in solids])
        comp._nurb_scene = scene
        return comp

    wrapped._nurb = PartDef(
        fn=wrapped,
        name=fn.__name__,
        params=params,
        accepts_draft=True,
        docs=param_docs(fn, params),
    )
    return wrapped


# --- the sweep ---------------------------------------------------------------


_EPS = 1e-4  # mm3; below this an intersection is numerical noise, not a collision


def _inside(bb, outer, slack=0.5):
    return (
        bb.min.X >= outer.min.X - slack
        and bb.min.Y >= outer.min.Y - slack
        and bb.min.Z >= outer.min.Z - slack
        and bb.max.X <= outer.max.X + slack
        and bb.max.Y <= outer.max.Y + slack
        and bb.max.Z <= outer.max.Z + slack
    )


def _hits(moved, others):
    """The overlap volume and where it is, or (0, None)."""
    worst, where = 0.0, None
    for other in others:
        try:
            common = moved & other
            vol = common.volume if common else 0.0
        except Exception:  # an empty boolean, depending on kernel mood
            vol = 0.0
        if vol > max(_EPS, worst):
            bb = common.bounding_box()
            # A real intersection is a subset of both inputs. OCCT handed a
            # degenerate solid can return chunks of the other operand instead,
            # which would read as a huge phantom collision; refusing it loudly
            # names the solid to fix, where a silent zero would hide it and a
            # phantom finding would send someone redesigning a working hinge.
            label = getattr(other, "label", "") or "a fixed part"
            if not _inside(bb, other.bounding_box()):
                raise ValueError(
                    f"intersecting with {label} returned geometry outside it "
                    f"({vol:.0f}mm3) -- that solid is likely degenerate"
                )
            worst = vol
            where = (
                (bb.min.X + bb.max.X) / 2,
                (bb.min.Y + bb.max.Y) / 2,
                (bb.min.Z + bb.max.Z) / 2,
                label,
            )
    return worst, where


def _limit(h, others, direction):
    """The last clear angle sweeping from the pose toward one end of the range.

    Coarse steps find the first collision, bisection then pins the boundary to under
    a tenth of a degree. Angles are absolute joint angles, not offsets from the pose.
    """
    end = h.hi if direction > 0 else h.lo
    span = abs(end - h.at)
    if span < 1e-9:
        return end, None
    clear, hit, contact = h.at, None, None
    steps = int(span // h.step) + 1
    for i in range(1, steps + 1):
        t = h.at + direction * min(i * h.step, span)
        moved = h.solid.rotate(h.axis, t - h.at)
        vol, where = _hits(moved, others)
        if vol:
            hit, contact = t, where
            break
        clear = t
    if hit is None:
        return end, None
    while abs(hit - clear) > 0.1:
        mid = (hit + clear) / 2
        moved = h.solid.rotate(h.axis, mid - h.at)
        vol, where = _hits(moved, others)
        if vol:
            hit, contact = mid, where
        else:
            clear = mid
    return clear, contact


def sweep(scene):
    """Findings for every declared joint, in checks.py's own vocabulary.

    Each hinge sweeps alone; other hinged solids stand frozen at their pose, which is
    the conservative reading of a mechanism you can only move one hand at a time.
    """
    from .checks import FAIL, Finding

    found = []
    for h in scene.hinges:
        others = (
            scene.statics
            + scene.obstacles
            + [o.solid for o in scene.hinges if o is not h]
        )
        if not others:
            continue
        vol, where = _hits(h.solid, others)
        if vol:
            found.append(
                Finding(
                    RULE,
                    FAIL,
                    f"{h.name} collides before it moves, posed at {h.at:.0f} deg "
                    f"against {where[3]}",
                    value=h.at,
                    where=where[:3],
                )
            )
            continue
        for direction, end in ((+1, h.hi), (-1, h.lo)):
            reached, contact = _limit(h, others, direction)
            if contact is None:
                continue
            found.append(
                Finding(
                    RULE,
                    FAIL,
                    f"{h.name} jams at {reached:.1f} deg of the "
                    f"({h.lo:.0f}, {h.hi:.0f}) declared, striking {contact[3]}",
                    value=reached,
                    where=contact[:3],
                )
            )
    return found
