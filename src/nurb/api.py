"""The vocabulary a part file gets, printed with signatures.

`from nurb import *` hands a part file the whole build123d namespace plus a handful of
names of nurb's own. The doctrine names those in prose and gives no signatures, so an
agent that wants to know what `concave_edges` returns goes and reads the installed
source to find out. In one recorded session that was ten of thirty-eight shell commands,
and reading source is the most expensive way for a model to answer a question it could
have been told in thirty lines.

Nurb's own names are derived, never listed: they are whatever `__init__` adds on top of
build123d, so this cannot drift from what a part file can actually call. The signatures
and the summaries come off the functions themselves for the same reason.
"""

import inspect

# Named by the doctrine rather than by nurb. `new_edges` is the one build123d selector
# the doctrine mandates ("prefer new_edges over geometric selectors"), and a part file
# that follows that rule needs its argument order. The rest of build123d is its own
# documentation and does not belong here.
BORROWED = ("new_edges",)


def _summary(obj):
    """The first line of a docstring that says something.

    Skipping a first line that is only the function's own name, which is build123d's
    convention and would otherwise render `new_edges` as documented by the word
    "new_edges".
    """
    name = getattr(obj, "__name__", "")
    for line in (inspect.getdoc(obj) or "").splitlines():
        line = line.strip()
        if line and line != name:
            return line
    return ""


def _signature(obj):
    try:
        return f"{obj.__name__}{inspect.signature(obj)}"
    except (TypeError, ValueError):  # a C function, or anything without one
        return getattr(obj, "__name__", str(obj))


def _b3d_names(build123d):
    return set(getattr(build123d, "__all__", ()) or dir(build123d))


def own_names():
    """What `nurb` adds to build123d, in the order `__init__` declares it."""
    import build123d

    import nurb

    return [n for n in nurb.__all__ if n not in _b3d_names(build123d)]


def shadowed_names():
    """build123d names that `nurb` replaces with its own.

    Found by identity, not by a list, for the same reason `own_names` uses subtraction:
    wrapping one more of them should show up here without anyone remembering to say so.
    A part file calls these believing they are build123d's, so an agent reading `nurb
    api` is entitled to know which ones are not.
    """
    import build123d

    import nurb

    return sorted(
        n
        for n in _b3d_names(build123d)
        if hasattr(nurb, n) and getattr(nurb, n) is not getattr(build123d, n)
    )


def entries():
    """(signature, summary) rows for each of the three groups a part file should know."""
    import build123d

    import nurb

    own = [(_signature(o), _summary(o)) for o in (getattr(nurb, n) for n in own_names())]
    shadowed = [
        (_signature(o), _summary(o)) for o in (getattr(nurb, n) for n in shadowed_names())
    ]
    borrowed = [
        (_signature(o), _summary(o))
        for o in (getattr(build123d, n, None) for n in BORROWED)
        if o is not None
    ]
    return own, shadowed, borrowed


def _section(title, rows):
    lines = ["", title, ""]
    for sig, summary in rows:
        lines.append(f"  {sig}")
        if summary:
            lines.append(f"      {summary}")
    return lines


def report():
    own, shadowed, borrowed = entries()
    lines = ["  from nurb import *  gives a part file all of build123d, plus:", ""]
    for sig, summary in own:
        lines.append(f"  {sig}")
        if summary:
            lines.append(f"      {summary}")
    if shadowed:
        lines += _section(
            "  And it replaces these build123d names with its own. Read the summary:", shadowed
        )
    if borrowed:
        lines += _section("  From build123d, because the doctrine mandates it:", borrowed)
    lines += [
        "",
        "  `nurb rules` is when to reach for these. `nurb inspect <part>` measures a",
        "  built one in the same units the rules report.",
    ]
    return lines
