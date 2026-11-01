"""A project's shared files, read the way a person tunes them.

A setting is an UPPER_CASE name bound once, at the top of a shared file, to a plain
number: `CLEARANCE = 0.2  # slide fit, depth`. That is how Notch's system.py was
already written, so the convention costs an agent nothing to follow and needs no
declaration beside it. A name bound to an expression (`CHANNEL_WIDTH = POCKET_WIDTH +
2 * SIDE_CLEARANCE`) is derived, so it is not a setting: moving it would only fight the
numbers it comes from. A leading underscore keeps a number private, the way Python
already reads it: `_EPS = 1e-4` is the file's business, not a slider. A piece is a
public function the parts call.
"""

import ast
import math
import re

SETTING = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _number(node):
    """The plain number a node spells, or None."""
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _number(node.operand)
        return None if inner is None else -inner
    return None


def _bindings(tree):
    """Top-level single-name assignments by name, counting rebinds."""
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    found.setdefault(target.id, []).append(node)
    return found


def settings(source):
    """[{name, value, kind, note}] for every setting in one shared file's source."""
    try:
        tree = ast.parse(source or "")
    except SyntaxError:
        return []
    lines = (source or "").splitlines()
    out = []
    for name, nodes in _bindings(tree).items():
        # Bound twice means the file decides between them; not a knob to turn.
        if len(nodes) != 1 or not SETTING.match(name) or nodes[0].value is None:
            continue
        node = nodes[0]
        value = _number(node.value)
        if value is None:
            continue
        tail = lines[node.end_lineno - 1][node.value.end_col_offset :]
        note = tail.split("#", 1)[1].strip() if "#" in tail else ""
        out.append({"name": name, "value": value, "kind": "int" if isinstance(value, int) else "float", "note": note})
    return out


def set_setting(source, name, value):
    """The source with one setting's number replaced, or ValueError saying why not."""
    tree = ast.parse(source)
    nodes = _bindings(tree).get(name, [])
    if len(nodes) != 1 or _number(nodes[0].value) is None:
        raise ValueError(f"{name} is not a setting in this file")
    old = _number(nodes[0].value)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"{name} needs a number")
    if isinstance(old, int):
        if float(value) != int(value):
            raise ValueError(f"{name} counts whole things, so it takes a whole number")
        text = str(int(value))
    else:
        text = repr(float(value))
    node = nodes[0].value
    lines = source.splitlines(keepends=True)
    if node.lineno != node.end_lineno:
        raise ValueError(f"{name} spans lines; change it in the source")
    line = lines[node.lineno - 1]
    lines[node.lineno - 1] = line[: node.col_offset] + text + line[node.end_col_offset :]
    return "".join(lines)


def pieces(source):
    """The public functions a shared file offers its parts, in file order."""
    try:
        tree = ast.parse(source or "")
    except SyntaxError:
        return []
    return [node.name for node in tree.body if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")]


def uses(source, module, piece):
    """Whether a part's source calls on `piece` from `module`: imported by name, by
    star, or reached as `module.piece`."""
    try:
        tree = ast.parse(source or "")
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module and not node.level:
            if any(alias.name in (piece, "*") for alias in node.names):
                return True
        if isinstance(node, ast.Attribute) and node.attr == piece:
            if isinstance(node.value, ast.Name) and node.value.id == module:
                return True
    return False
