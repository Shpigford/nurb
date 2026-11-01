"""The printers standing in the workshop.

A printer is a fact about the workshop, not about one project, so the list lives in
`~/.config/nurb/config.toml` beside the `profile` line that names the default. A
project with no printer.toml of its own already falls back to that line, so adding a
machine here is the only step most people ever take.
"""

import pathlib

from . import checks


def _config():
    return checks.global_file()


def _block():
    file = _config()
    return checks._read_toml(file, str(file))


def _known(key):
    have = checks.profiles()
    if key not in have:
        raise ValueError(
            f"no printer profile called {key!r}. Pick one of: {', '.join(have)}"
        )
    return have


def default_printer():
    """The key the workshop prints on when a project does not say, or None."""
    return _block().get("profile") or None


def workshop_printers():
    """The machines in the workshop, the default first.

    The `profile` line is the default and counts as a member even when an older
    config never listed it, so upgrading does not lose the one printer a person has.
    """
    block = _block()
    listed = [str(k) for k in block.get("printers") or [] if isinstance(k, str)]
    default = block.get("profile")
    if default and default not in listed:
        listed.insert(0, default)
    seen, out = set(), []
    for key in listed:
        if key not in seen:
            seen.add(key)
            out.append(key)
    if default in out:
        out.remove(default)
        out.insert(0, default)
    return out


def _write(keys, default):
    file = _config()
    line = "printers = [" + ", ".join(f'"{k}"' for k in keys) + "]" if keys else None
    checks.write_top_line(file, "printers", line)
    checks.write_top_line(file, "profile", f'profile = "{default}"' if default else None)
    return workshop_printers()


def add_workshop_printer(key):
    """Put a machine in the workshop. The first one added becomes the default."""
    _known(key)
    keys = workshop_printers()
    if key not in keys:
        keys.append(key)
    return _write(keys, default_printer() or key)


def remove_workshop_printer(key):
    """Take a machine out. The next one standing inherits the default."""
    keys = workshop_printers()
    if key not in keys:
        raise ValueError(f"{key!r} is not in the workshop. Add it before removing it.")
    keys.remove(key)
    default = default_printer()
    if default == key or default not in keys:
        default = keys[0] if keys else None
    return _write(keys, default)


def set_default_printer(key):
    """Name the machine every project uses unless it says otherwise."""
    keys = workshop_printers()
    if key not in keys:
        raise ValueError(
            f"{key!r} is not in the workshop. Add it first, then make it the default."
        )
    return _write(keys, key)
