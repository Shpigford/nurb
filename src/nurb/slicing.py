"""The handoff to a slicer, and the two numbers that come back.

nurb owns the geometry and the stance it prints in. Everything after that, layer
heights and flow rates and how this filament behaves at 220 degrees, belongs to the
slicer the user already has configured, and re-deriving any of it here would be a
second opinion nobody asked for that goes stale every firmware release.

So this module is deliberately thin. It finds the slicer, picks the profile that
matches the machine the project already named in `printer.toml`, and hands over the
STL. What it wants back is the pair of numbers that change a design decision while
there is still time to change it: how long the print takes, and how much filament it
weighs. A wall that goes from 2 to 3mm is a shrug in the viewer and forty minutes on
the plate, and finding that out after the part is on the bed is finding out too late.

Local only. No account, no network call, no printer credentials: this runs the
slicer that is already on the machine and reads the files it wrote.
"""

import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys

# Keep slicer subprocesses from opening console windows when nurb itself runs
# without one (the desktop app); a plain 0 is ignored off Windows.
_QUIET = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

# Slicers that share the one CLI grammar this module speaks: `--load-settings`,
# `--load-filaments`, `--slice`, `--outputdir`, and a bundled tree of vendor profiles
# under Resources/profiles. They are a fork and its parent, which is why one adapter
# covers both. Orca leads because it carries profiles for more machines.
SLICERS = ("OrcaSlicer", "BambuStudio")
COMMANDS = {
    "OrcaSlicer": ("OrcaSlicer", "orcaslicer", "orca-slicer"),
    "BambuStudio": ("BambuStudio", "bambustudio", "bambu-studio"),
}
FLATPAKS = {
    "OrcaSlicer": "com.orcaslicer.OrcaSlicer",
    "BambuStudio": "com.bambulab.BambuStudio",
}

# What each shipped profile is called in a slicer's own vendor bundle. It lives beside
# the machine rather than in this module's head, so `printers.toml` stays the one place
# a machine is described; see `checks.printer`, which drops this key before the rest of
# a profile becomes check settings.
NOZZLE = "0.4"
PLATE = "Textured PEI Plate"


class Unavailable(Exception):
    """No slicer, or no profile in it for this machine. The message says what to do."""


# What every exported part gets over the stock process profile. Values are strings
# because that is how a slicer's own config files carry them. Gyroid instead of grid
# because it is isotropic and printable without crossings, which is why it holds the
# same strength at 10% that grid needs 15% for; three walls instead of two because
# these are functional parts, and walls carry load that infill never sees.
TUNED = {
    "sparse_infill_pattern": "gyroid",
    "sparse_infill_density": "10%",
    "wall_loops": "3",
}

# The findings that mean this part needs help holding the bed. Both are the checks'
# own judgement: a first layer big enough to peel its corners, or a part standing
# taller than first-layer adhesion holds. The brim is the slicer-side share of both
# fixes.
BRIM_RULES = ("warp_risk", "stability")

# Supports are the other setting a part can earn, and they arrive by a different route,
# which is worth naming because the two sit side by side below. A brim is *derived*: the
# rules look at the geometry and decide. Supports are *declared*, by `supported()` in the
# part file or by the card, and no amount of looking at a solid can tell you whether its
# owner is willing to cut support material off it. So this reads the declaration and
# does not second-guess it.
#
# Only the on switch. The slicer's own support threshold is measured from the horizontal
# while `overhang_limit` is measured from the build direction, so they are complements
# and driving one from the other inverts at every value but the default. Past that, an
# angle is tuning, and tuning belongs to the profile the user already configured.
SUPPORT_SETTINGS = {"enable_support": "1"}


def tuned(shape, ctx=None):
    """The process settings this part's geometry justifies, and the words for them.

    Returns (settings, notes): the overrides to lay over a stock process profile, and
    a short phrase per decision for whoever is reading an export line. This is the
    module's one exception to leaving settings to the slicer, drawn on a line: what
    follows from the geometry nurb built is nurb's knowledge, while flow, temperature
    and layer height stay the slicer's.
    """
    from . import checks, supports

    # `checks.run` defaults this for itself, but the declaration below is read here.
    ctx = ctx or checks.Context()
    settings = dict(TUNED)
    notes = [f"gyroid {settings['sparse_infill_density']}", f"{settings['wall_loops']} walls"]
    found = checks.run(shape, ctx, only=set(BRIM_RULES))
    if found:
        settings["brim_type"] = "outer_only"
        settings["brim_width"] = "5"
        notes.append(f"brim ({checks.LABELS[found[0].rule]})")
    if ctx.supports or supports.regions(shape):
        settings.update(SUPPORT_SETTINGS)
        notes.append("supports")
    return settings, notes


def app(search=None):
    """The installed slicer's executable, or None.

    macOS keeps it in a bundle. Windows installs into Program Files (or the
    per-user Programs folder). Linux uses a command, an AppImage on PATH, or one
    of the two official Flatpaks. A Flatpak is returned as its command prefix;
    `run` appends the slicing arguments in exactly the same way it does for an
    executable.
    """
    for name in search or SLICERS:
        bundle = pathlib.Path(f"/Applications/{name}.app/Contents/MacOS/{name}")
        if bundle.is_file():
            return bundle
        for folder in _windows_install_dirs(name):
            for command in COMMANDS.get(name, (name, name.lower())):
                found = folder / f"{command}.exe"
                if found.is_file():
                    return found
        for command in COMMANDS.get(name, (name, name.lower())):
            found = shutil.which(command)
            if found:
                return pathlib.Path(found)
        if sys.platform != "win32":
            # AppImage filenames carry a version, so `which` cannot name one
            # exactly. Looking only on PATH keeps discovery explicit and bounded.
            patterns = (f"{name}*.AppImage", f"{name.replace('Studio', '_Studio')}*.AppImage")
            for folder in os.get_exec_path():
                for pattern in patterns:
                    for found in sorted(pathlib.Path(folder).glob(pattern)):
                        if found.is_file() and os.access(found, os.X_OK):
                            return found
        app_id = FLATPAKS.get(name)
        flatpak = shutil.which("flatpak")
        if app_id and flatpak and any(root.is_dir() for root in _flatpak_roots(app_id)):
            return (flatpak, "run", app_id)
    return None


def _windows_install_dirs(name):
    """Where the Windows installers put a slicer, machine-wide and per-user.

    Both installer titles space out the camel case ("Bambu Studio"), but the
    Orca folder keeps it joined, so both spellings are tried.
    """
    if sys.platform != "win32":
        return []
    folders = dict.fromkeys((name, re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)))
    dirs = []
    for env in ("ProgramFiles", "ProgramFiles(x86)"):
        if base := os.environ.get(env):
            dirs += [pathlib.Path(base) / folder for folder in folders]
    if local := os.environ.get("LOCALAPPDATA"):
        dirs += [pathlib.Path(local) / "Programs" / folder for folder in folders]
    return dirs


def vendors(exe):
    """The slicer's bundled profile tree."""
    paths = [] if isinstance(exe, tuple) else [pathlib.Path(exe), pathlib.Path(exe).resolve()]
    flavor = _flavor(exe)
    candidates = []
    for path in dict.fromkeys(paths):
        candidates += [
            path.parent.parent / "Resources" / "profiles",  # macOS bundle
            path.parent / "resources" / "profiles",  # unpacked AppImage
            path.parent.parent / "resources" / "profiles",
        ]
        prefix = path.parent.parent
        for name in _resource_names(flavor):
            candidates += [
                prefix / "share" / name / "profiles",
                prefix / "share" / name / "resources" / "profiles",
                prefix / "share" / name / "system",
            ]
    candidates += _user_profile_roots(flavor)
    app_id = next((a for a in FLATPAKS.values() if isinstance(exe, tuple) and a in exe), None)
    for root in _flatpak_roots(app_id) if app_id else ():
        files = root / "files" / "share"
        candidates.append(root / "files" / "resources" / "profiles")
        for name in _resource_names(flavor):
            candidates += [
                files / name / "profiles",
                files / name / "resources" / "profiles",
                files / name / "system",
            ]
    return next((root for root in candidates if root.is_dir()), None)


def label(exe):
    """A slicer name suitable for an error, whether it is a path or Flatpak command."""
    return _flavor(exe)


def _flavor(exe):
    """The application family, from a path or Flatpak command."""
    said = " ".join(str(v) for v in exe) if isinstance(exe, tuple) else str(exe)
    return "OrcaSlicer" if "orca" in said.lower() else "BambuStudio"


def _resource_names(flavor):
    return (flavor, flavor.lower(), flavor.replace("Slicer", "-slicer").replace("Studio", "-studio").lower())


def _flatpak_roots(app_id):
    if not app_id:
        return ()
    home = pathlib.Path.home()
    return (
        home / ".local" / "share" / "flatpak" / "app" / app_id / "current" / "active",
        pathlib.Path("/var/lib/flatpak/app") / app_id / "current" / "active",
    )


def _user_profile_roots(flavor):
    """Profile caches written after the slicer has run once."""
    home = pathlib.Path.home()
    config = pathlib.Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    app_id = FLATPAKS[flavor]
    roots = [
        config / flavor / "system",
        home / ".var" / "app" / app_id / "config" / flavor / "system",
    ]
    if appdata := os.environ.get("APPDATA"):
        roots.insert(0, pathlib.Path(appdata) / flavor / "system")
    return roots


def _readable(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}  # a template fragment or a file this version writes differently


def machine(profiles, name, nozzle=NOZZLE):
    """The vendor profile for a machine, by the name a slicer knows it under."""
    want = f"{name} {nozzle} nozzle"
    for candidate in sorted(profiles.glob(f"*/machine/{want}.json")):
        return candidate
    all_machines = sorted(profiles.glob("*/machine/* nozzle.json"))
    prefix, suffix = f"{name} ", " nozzle"
    nozzles = sorted(
        {
            path.stem[len(prefix) : -len(suffix)]
            for path in all_machines
            if path.stem.startswith(prefix) and path.stem.endswith(suffix)
        }
    )
    if nozzles:
        raise Unavailable(
            f"this slicer has no {nozzle}mm profile for {name!r}.\n"
            f"  For this machine it has: {', '.join(f'{size}mm' for size in nozzles)} nozzle."
        )
    have = sorted({p.stem.rsplit(" ", 2)[0] for p in all_machines})
    # Its neighbours, not the first six alphabetically: someone whose MK4S is missing
    # needs to know which Prusas are here, and a list starting at Anker tells them
    # nothing except that the list is long.
    family = name.split()[0]
    near = [m for m in have if m.startswith(family)]
    raise Unavailable(
        f"this slicer has no profile for {name!r} with a {nozzle}mm nozzle.\n"
        + (
            f"  From the same maker it has: {', '.join(near)}.\n"
            if near
            else f"  It has nothing from {family} at all, out of {len(have)} machines.\n"
        )
        + "  OrcaSlicer carries the widest set if yours is missing here."
    )


def _compatible(folder, printer, prefer, fallback=True, whole=False):
    """The best profile in `folder` that this printer can actually use.

    `compatible_printers` is the vendor bundle's own answer to which process goes with
    which machine, so it is the thing to ask rather than matching on the name suffixes,
    which differ per vendor and change between releases.
    """
    usable = []
    for path in sorted(folder.glob("*.json")):
        data = _readable(path)
        if data.get("instantiation") != "true":
            continue
        if printer in data.get("compatible_printers", []):
            usable.append(path)
    if not usable:
        return None
    for want in prefer:
        for path in usable:
            matches = (
                re.search(rf"(?<![\w-]){re.escape(want)}(?![\w-])", path.stem, re.IGNORECASE)
                if whole
                else want.lower() in path.stem.lower()
            )
            if matches:
                return path
    return usable[0] if fallback else None


def profiles_for(machine_path, layer="0.20", filament="PLA"):
    """The process and filament this machine should slice with.

    Both are picked rather than configured, and the picks get printed, because a
    prediction is only worth reading next to the settings that produced it.
    """
    printer = machine_path.stem
    vendor = machine_path.parent.parent
    process = _compatible(vendor / "process", printer, [f"{layer}mm Standard", f"{layer}mm", "Standard"])
    stock = _compatible(
        vendor / "filament",
        printer,
        [f"{filament} Basic", filament],
        fallback=False,
        whole=True,
    )
    if not process or not stock:
        missing = "process" if not process else "filament"
        asked = f" matching {filament!r}" if missing == "filament" else ""
        raise Unavailable(
            f"this slicer ships no {missing} profile{asked} compatible with {printer!r}"
        )
    return process, stock


def _preset_args(out_dir, machine_path, process, filament, settings=None):
    """The `--load-*` arguments, with the presets flattened into `out_dir` first.

    `settings` lays over the flattened process profile, which is how `tuned` reaches
    both the G-code and the project 3MF through one seam: the slicer only ever sees a
    complete profile that already says gyroid.
    """
    flattened = []
    for kind, source in (("machine", machine_path), ("process", process), ("filament", filament)):
        data = _flatten(source)
        if kind == "process" and settings:
            # A key the stock profile has never heard of is a typo, and it is otherwise
            # the quietest bug in this module: the slicer ignores what it cannot parse,
            # so the export line still promises supports and the 3MF opens without
            # them. Said rather than raised, because a vendor is free to rename a key
            # and losing the slice over it would be worse than losing the setting.
            unknown = sorted(k for k in settings if k not in data)
            if unknown:
                print(
                    f"  this slicer's process profile has no {', '.join(unknown)}; "
                    "those settings will not reach it",
                    flush=True,
                )
            data.update(settings)
        full = out_dir / f"{kind}.json"
        full.write_text(json.dumps(data), encoding="utf-8")
        flattened.append(full)
    machine_full, process_full, filament_full = flattened
    return [
        "--load-settings", f"{machine_full};{process_full}",
        "--load-filaments", str(filament_full),
    ]


def run(model, target, machine_path, process, filament, exe=None, plate=PLATE, settings=None):
    """Slice one model to `target`, and return what the slicer predicted.

    Returns ((seconds, grams), path). Either number can be None: a slicer that changes
    how it reports is a reason to say less, never a reason to make one up.

    The slicer names its own output after the plate, so it gets a scratch directory and
    the gcode is moved to the name the rest of build/ uses. A part is `thing.stl` and
    `thing.gcode`, not `thing.stl` and `gcode/thing/plate_1.gcode`.
    """
    exe = exe or app()
    target = pathlib.Path(target)
    out_dir = target.parent / f".{target.stem}.slicing"
    target.parent.mkdir(parents=True, exist_ok=True)
    # A failed attempt must not leave yesterday's printable file looking current.
    target.unlink(missing_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in ("plate_1.gcode", "result.json"):
        (out_dir / stale).unlink(missing_ok=True)
    try:
        command = list(exe) if isinstance(exe, tuple) else [str(exe)]
        done = subprocess.run(
            [
                *command,
                "--curr-bed-type", plate,
                *_preset_args(out_dir, machine_path, process, filament, settings),
                "--slice", "0",
                "--outputdir", str(out_dir),
                str(model),
            ],
            capture_output=True,
            text=True,
            creationflags=_QUIET,
        )
        gcode = out_dir / "plate_1.gcode"
        if done.returncode != 0 or not gcode.is_file():
            raise Unavailable(f"the slicer refused this model: {_why(done, out_dir)}")
        predicted = _predicted(out_dir)  # read while both files are still together
        gcode.rename(target)
    finally:
        # In `finally` because the refusal path is the one that leaves debris, and a
        # hidden directory nobody looks in is one that never gets cleaned up by hand.
        shutil.rmtree(out_dir, ignore_errors=True)
    return predicted, target


def kit(root):
    """What upgrading a 3MF to carry print settings needs, or why it cannot.

    Returns ((machine, process, filament, exe), None) when everything is in place,
    and (None, reason) when it is not. The reason is one line because a bare 3MF is
    the export working as it always has, not a failure to explain at length.
    """
    from . import checks

    exe = app()
    if exe is None:
        return None, "no slicer installed to write print settings"
    try:
        wanted, _ = checks.slicer_name(root)
        if not wanted:
            return None, "no printer named in printer.toml to tune settings for"
        bundle = vendors(exe)
        if bundle is None:
            return None, f"found {label(exe)} but not its profile bundle"
        machine_path = machine(bundle, wanted)
        material = (checks.printer(root).material or "PLA").upper()
        process, filament = profiles_for(machine_path, filament=material)
    except (ValueError, Unavailable) as exc:
        return None, str(exc)
    return (machine_path, process, filament, exe), None


def write_project(model, target, machine_path, process, filament, exe=None, settings=None, plate=PLATE):
    """Rewrite a bare 3MF as a project 3MF that carries its print settings.

    A bare 3MF is geometry and a unit; the settings a slicer honors on open live in
    `Metadata/project_settings.config`, a full dump of every process key in the
    slicer's own format. The slicer writes that file itself here, via `--export-3mf`
    with our overrides loaded, rather than nurb composing it: a hand-built config
    with keys missing crashes Bambu Studio's own loader outright (verified, exit
    -11), and the full key set changes with slicer releases, so the one program
    guaranteed to know this version's complete schema is the slicer being asked to
    read it back. `--arrange` because a bare 3MF carries no plate, and a project
    file whose part sits half off the bed opens as an error.

    `model` and `target` may be the same path: the export lands in a scratch
    directory and only replaces `target` once the slicer has succeeded.
    """
    exe = exe or app()
    target = pathlib.Path(target)
    out_dir = target.parent / f".{target.stem}.slicing"
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    try:
        command = list(exe) if isinstance(exe, tuple) else [str(exe)]
        done = subprocess.run(
            [
                *command,
                "--curr-bed-type", plate,
                *_preset_args(out_dir, machine_path, process, filament, settings),
                "--arrange", "1",
                "--export-3mf", "project.3mf",
                "--outputdir", str(out_dir),
                str(model),
            ],
            capture_output=True,
            text=True,
            creationflags=_QUIET,
        )
        written = out_dir / "project.3mf"
        if done.returncode != 0 or not written.is_file():
            raise Unavailable(f"the slicer refused this model: {_why(done, out_dir)}")
        os.replace(written, target)
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
    return target


def _flatten(path, seen=None):
    """One complete preset: inherited values, then its split-out template fields."""
    path = pathlib.Path(path)
    seen = set() if seen is None else seen
    if path in seen:
        raise Unavailable(f"profile inheritance loops at {path.name}")
    seen.add(path)
    data = _read_profile(path)
    parent = data.pop("inherits", None)
    full = {}
    if parent:
        parent_path = _parent_profile(path, parent)
        if parent_path is None:
            raise Unavailable(f"{path.name} inherits missing profile {parent!r}")
        full = _flatten(parent_path, seen)
    full.update(data)
    # Bambu keeps large G-code fields in sibling fragments named after the preset.
    # They are part of the full profile the CLI requires, but their own bookkeeping
    # must not turn the selected leaf back into an uninstantiable template.
    prefix = f"{path.stem} template "
    for template in sorted(p for p in path.parent.glob("*.json") if p.stem.startswith(prefix)):
        patch = _read_profile(template)
        for key in ("name", "inherits", "instantiation", "from", "type"):
            patch.pop(key, None)
        full.update(patch)
    return full


def _read_profile(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Unavailable(f"cannot read slicer profile {path.name}: {exc}") from exc


def _parent_profile(path, name):
    """Find a named parent in this vendor first, then elsewhere in the bundle."""
    direct = path.parent / f"{name}.json"
    if direct.is_file():
        return direct
    profiles = path.parents[2]
    kind = path.parent.name
    matches = sorted(
        candidate
        for candidate in profiles.glob(f"*/{kind}/**/*.json")
        if candidate.stem == name
    )
    return matches[0] if len(matches) == 1 else None


def _why(done, out_dir):
    """The slicer's own reason, which it puts in result.json before it puts it on stderr."""
    said = _readable(out_dir / "result.json").get("error_string")
    if said and said != "Success.":
        return said
    tail = [line for line in (done.stderr or done.stdout or "").splitlines() if "error" in line.lower()]
    return tail[-1] if tail else f"exit code {done.returncode}"


TIME = re.compile(r"total estimated time: ([^;\n]+)")
LENGTH = re.compile(r"total filament length \[mm\] ?: ?([\d.]+)")
WEIGHT = re.compile(r"total filament weight \[g\] ?: ?([\d.]+)")
DENSITY = re.compile(r"filament_density[ =:]+([\d.]+)")
DIAMETER = re.compile(r"filament_diameter[ =:]+([\d.]+)")


def _predicted(out_dir):
    """Time in seconds and filament in grams, from whichever of the two files carries it.

    Grams because that is the unit a spool is sold in and the only one anyone thinks in;
    nobody has ever decided anything from a length of filament.

    The structured file is authoritative on time and silent on filament, and the gcode
    header carries both, so they are read in that order rather than one being trusted
    for everything. The weight line reads 0 on a stock profile whose density never
    resolved, and a wrong gram figure is worse than none because only one of them gets
    checked, so a zero falls through to the arithmetic: length, diameter and density are
    three separate header keys, and a cylinder of filament is the whole calculation.
    """
    seconds = None
    plates = _readable(out_dir / "result.json").get("sliced_plates") or []
    if plates and isinstance(plates[0], dict):
        predicted = plates[0].get("total_predication")
        seconds = float(predicted) if predicted else None
    head = ""
    gcode = out_dir / "plate_1.gcode"
    if gcode.is_file():
        with gcode.open("r", encoding="utf-8", errors="replace") as fh:
            head = fh.read(4096) + _tail(gcode)
    if seconds is None:
        said = TIME.search(head)
        seconds = _clock(said[1]) if said else None
    return seconds, _grams(head)


def _grams(head):
    """What the plate weighs, from the header's own figure or from its parts."""
    said = WEIGHT.search(head)
    if said and float(said[1]) > 0:
        return float(said[1])
    length, density, diameter = (r.search(head) for r in (LENGTH, DENSITY, DIAMETER))
    if not (length and density and diameter):
        return None
    radius = float(diameter[1]) / 2
    volume = float(length[1]) * math.pi * radius * radius  # mm3
    return volume / 1000 * float(density[1])


def _tail(gcode, size=8192):
    """These slicers write their totals as a footer, so the head alone would miss them."""
    with gcode.open("rb") as fh:
        fh.seek(max(0, gcode.stat().st_size - size))
        return fh.read().decode("utf-8", errors="replace")


def _clock(said):
    """`1d 4h 20m 12s` as seconds.

    Days are in here because a long print reaches them and dropping the unit would not
    fail, it would quietly report a 28 hour print as four. Anything this does not
    recognise makes the whole reading None, on the module's own rule that a slicer
    reporting differently is a reason to say less rather than to answer confidently.
    """
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = 0
    for value, unit in re.findall(r"(\d+)\s*([a-z])", said.lower()):
        if unit not in units:
            return None
        total += int(value) * units[unit]
    return total or None


def weighed(grams):
    """A weight against a 1kg spool, which is the only filament measure anyone holds.

    Whole grams past 10, because a tenth of a gram is noise next to a slicer's own
    error, and one decimal below it so a fit coupon does not round to nothing.
    """
    if not grams:
        return "unknown"
    return f"{grams:.0f}g" if grams >= 10 else f"{grams:.1f}g"


def spoken(seconds):
    """A duration a human reads at a glance rather than divides."""
    if not seconds:
        return "unknown"
    days, rest = divmod(int(seconds), 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days}d {hours}h {minutes:02d}m"
    return f"{hours}h {minutes:02d}m" if hours else f"{minutes}m"
