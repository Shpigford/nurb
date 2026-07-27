"""Duplication across sibling parts, which is where a system comes from.

A system is extracted, never scaffolded. Guessing what a family shares before the
family exists propagates the wrong abstraction into every part at once, and the cost of
that only shows up later, when the guess turns out to have been about the wrong thing.
So this runs after a port, over parts that already work, and it answers one question:
what did these files end up saying twice?

It reports and does not rewrite. Lifting a run of statements into a shared function
means choosing which of its free names become parameters and what the function is
called, and both are judgement calls about what the thing *is*. The expensive part is
noticing, and noticing is mechanical. Naming is not.

Matching is alpha-equivalence over the AST: names bound inside a part function are
canonicalized so two parts that wrote the same construction with different local names
still match, while imported and module-level names keep their identity, because
`Box(a, b, c)` and `Pos(a, b, c)` are not the same statement.
"""

import ast
import pathlib

# Two statements is the shortest run worth a name. One is a line, and every part in a
# family opens with the same kind of line without that meaning anything.
MIN_RUN = 2
MIN_TEXT = 60  # characters of normalized shape, so two short assignments do not qualify


def _bound(node):
    """Names a function binds: its parameters and anything it assigns."""
    names = {a.arg for a in node.args.args + node.args.kwonlyargs}
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            names.add(child.id)
        elif isinstance(child, ast.arg):
            names.add(child.arg)
    return names


def _shape(node, local, seen):
    """A structural dump with local names canonicalized.

    Only locals. An imported name is part of what the statement means, so `Box` and
    `Pos` stay themselves and two calls with the same arity do not collide.
    """
    if isinstance(node, ast.Name):
        if node.id in local:
            return f"L{seen.setdefault(node.id, len(seen))}"
        return f"G{node.id}"
    if isinstance(node, ast.arg):
        return f"L{seen.setdefault(node.arg, len(seen))}"
    if isinstance(node, ast.Constant):
        return f"C{node.value!r}"
    if isinstance(node, ast.AST):
        fields = ",".join(
            f"{name}={_shape(value, local, seen)}"
            for name, value in ast.iter_fields(node)
            if name != "ctx"
        )
        return f"{type(node).__name__}({fields})"
    if isinstance(node, list):
        return "[" + ",".join(_shape(item, local, seen) for item in node) + "]"
    return repr(node)


def _regions(path):
    """The statement runs worth comparing in one part file.

    A part file has two: what the module does at the top, which is where a copied
    helper lands, and what the part function does, which is where a copied construction
    lands. Both are flat lists of statements, so both are searched the same way.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = [(tree.body, set())]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append((node.body, _bound(node)))
    return out


def _windows(path):
    """Every run of consecutive statements in a file, keyed by its normalized shape."""
    found = {}
    for body, local in _regions(path):
        # Imports are not a system. Two parts in a family import the same names by
        # definition, and reporting that as duplication buries the geometry underneath.
        body = [s for s in body if not isinstance(s, (ast.Import, ast.ImportFrom))]
        shapes = [_shape(stmt, local, {}) for stmt in body]
        for start in range(len(body)):
            for end in range(start + MIN_RUN, len(body) + 1):
                text = "|".join(shapes[start:end])
                if len(text) < MIN_TEXT:
                    continue
                found.setdefault(text, (body[start].lineno, body[end - 1].end_lineno, end - start))
    return found


def duplication(paths):
    """Runs of statements that more than one part file says.

    Returns the maximal ones, longest first. A five-statement match contains four
    four-statement matches and reporting all of them buries the one that matters, so a
    run that sits inside a longer run already reported for the same files is dropped.
    """
    seen = {}
    for path in paths:
        for text, where in _windows(path).items():
            seen.setdefault(text, []).append((path, *where))

    shared = [
        {"shape": text, "sites": sites, "statements": sites[0][3]}
        for text, sites in seen.items()
        if len({site[0] for site in sites}) > 1
    ]
    shared.sort(key=lambda d: (-d["statements"], -len(d["sites"])))

    out, covered = [], set()
    for run in shared:
        span = {(path, line) for path, line, _, _ in run["sites"]}
        if span & covered:
            continue  # already inside a longer run reported for the same files
        for path, start, end, _ in run["sites"]:
            covered.update((path, line) for line in range(start, end + 1))
        out.append(run)
    return out


def source(path, start, end):
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1 : end])
