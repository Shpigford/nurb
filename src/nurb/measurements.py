"""Named real-world values, with provenance.

The bottleneck on a one-off part is not geometry, it is dimensions. An agent cannot
measure a freezer shelf, and a guessed number produces a perfect model of the wrong
object: it builds, it checks clean, and it prints. Nothing downstream catches it.

So a measurement is a named value on disk with a note saying how it was obtained, and
asking for one that is not on file raises. That failure is the feature. It is the moment
to ask rather than to pick something plausible.
"""

import pathlib
import sys
import tomllib

FILENAME = "measurements.toml"


class MeasurementError(LookupError):
    """A measurement is missing or unusable.

    Not `KeyError`, which reprs its argument: a message with a worked example in it comes
    out as one quoted string full of backslash-n, and the example is the useful part.
    """


def _caller_dir(depth):
    """Where the code that called us lives, so the lookup needs no configuration."""
    frame = sys._getframe(depth)
    here = frame.f_globals.get("__file__")
    return pathlib.Path(here).resolve().parent if here else pathlib.Path.cwd()


def _find(start):
    """The nearest measurements file, without leaving the project.

    The walk stops at the project root, meaning the directory holding `parts/`. Without
    that stop it would keep going to the filesystem root and could silently answer with
    some unrelated file from an ancestor directory, which is the exact failure this whole
    module exists to prevent: a dimension that is wrong and looks fine.
    """
    for d in [start, *start.parents]:
        if (d / FILENAME).is_file():
            return d / FILENAME
        if (d / "parts").is_dir():
            return None
    return None


def _read(path):
    """Parse it, and say which file when it will not parse. The same courtesy cards get."""
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise MeasurementError(f"{path.name}: not valid TOML ({exc})") from exc


def load(start=None):
    """Every measurement on file, as name -> record. Empty when there is no file."""
    path = _find(pathlib.Path(start).resolve() if start else _caller_dir(2))
    return _read(path) if path else {}


def provisional(start=None):
    """Every value on file that admits it was not actually measured.

    The doctrine says to ask rather than improvise, and sometimes there is nobody to
    ask: the caliper is in a drawer, the object is at the office, the print has to go
    on tonight. The failure mode is not putting a number in, it is that the number then
    looks exactly like one somebody measured. Six months later nothing distinguishes
    them and the part is wrong for a reason no one can find.

    So a guess is allowed to be written down and required to say so, and `nurb check`
    reports the ones that still are. `how` stays mandatory either way: a provisional
    value still has to say where it came from, because "eyeballed against a broom"
    tells the next person how much to trust it.
    """
    return sorted(
        (name, entry.get("how", ""))
        for name, entry in load(start).items()
        if entry.get("provisional")
    )


def measured(name, start=None):
    """A measured value, in mm.

    Raises when it is not on file, when it has no provenance, or when it is recorded in
    units this does not work in. All three are cases where continuing would produce
    geometry that looks right and is wrong.

    A value marked `provisional = true` is returned like any other. It is a real number
    that builds a real part; what it is not is measured, and `nurb check` says so until
    somebody picks up a caliper.
    """
    start = pathlib.Path(start).resolve() if start else _caller_dir(2)
    path = _find(start)
    if path is None:
        raise MeasurementError(
            f"no {FILENAME} above {start}, so there is nothing measured to ask for. "
            f"Measure {name!r}, then record it:\n\n"
            f'  [{name}]\n  value = 0\n  unit = "mm"\n  how = "how you measured it"\n\n'
            f"If there is nobody to ask right now, add `provisional = true` and put "
            f"your best guess in. `nurb check` will keep reminding you."
        )
    book = _read(path)
    if name not in book:
        have = ", ".join(sorted(book)) or "nothing yet"
        raise MeasurementError(
            f"nothing measured called {name!r} in {path.name}. have: {have}. "
            f"Ask for the measurement rather than guessing one: a wrong number here "
            f"builds, checks clean, and prints."
        )
    entry = book[name]
    if "value" not in entry:
        raise MeasurementError(f"{path.name}: {name} has no value")
    if "how" not in entry:
        raise MeasurementError(
            f"{path.name}: {name} does not say how it was measured. A value without "
            f"provenance is a guess with a filename on it."
        )
    unit = entry.get("unit", "mm")
    if unit != "mm":
        raise MeasurementError(f"{path.name}: {name} is in {unit!r}, and nurb works in mm")
    return entry["value"]
