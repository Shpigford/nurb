"""Write parameter values back into a part file's keyword defaults.

The keyword defaults are the parameters, so an exploration that ends up in the file has
to end up in the signature. This is the only module that writes to a part file, and it
rewrites exactly the default it was asked to and nothing else: the source is edited as
text at the offsets the parser reports, so comments, formatting and every other line
survive untouched.
"""

import ast
import os
import pathlib


class EditError(Exception):
    pass


def _is_part(node):
    """@part, @nurb.part, and the call forms."""
    if isinstance(node, ast.Call):
        node = node.func
    name = node.attr if isinstance(node, ast.Attribute) else getattr(node, "id", None)
    return name == "part"


def _part_function(tree, path):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and any(_is_part(d) for d in node.decorator_list):
            return node
    raise EditError(f"no @part function in {path.name}")


def _defaults(fn):
    """Parameter name -> the AST node of its default, for those that have one."""
    out = {}
    positional = fn.args.posonlyargs + fn.args.args
    tail = positional[len(positional) - len(fn.args.defaults) :]
    for arg, node in zip(tail, fn.args.defaults):
        out[arg.arg] = node
    for arg, node in zip(fn.args.kwonlyargs, fn.args.kw_defaults):
        if node is not None:
            out[arg.arg] = node
    return out


def _number(node):
    """The number a default is written as, or None if it is not written as one."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _number(node.operand)
        return None if inner is None else -inner
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    return None


def _format(old, new):
    """Written the way it was written: an int stays an int, a float stays a float."""
    if isinstance(old, int) and float(new).is_integer():
        return str(int(new))
    # A slider lands on 0.30000000000000004, which is not a dimension anyone chose.
    text = f"{float(new):.6g}"
    return text if ("." in text or "e" in text) else text + ".0"


def _splice(src, node, text):
    """Replace the source the node covers. col_offset is a utf-8 byte offset."""
    lines = src.splitlines(keepends=True)
    head = lines[node.lineno - 1].encode()[: node.col_offset].decode()
    tail = lines[node.end_lineno - 1].encode()[node.end_col_offset :].decode()
    lines[node.lineno - 1 : node.end_lineno] = [head + text + tail]
    return "".join(lines)


def apply(path, values):
    """Write `values` into the part's keyword defaults.

    Returns (written, skipped), where `skipped` is a list of (name, why). Values
    already equal to the file's default are skipped silently, so applying an untouched
    exploration writes nothing and leaves no diff.
    """
    path = pathlib.Path(path)
    src = path.read_text(encoding="utf-8")
    fn = _part_function(ast.parse(src, filename=str(path)), path)
    defaults = _defaults(fn)

    edits, skipped = [], []
    for name, new in values.items():
        node = defaults.get(name)
        if node is None:
            raise EditError(f"{path.name} has no parameter named {name}")
        old = _number(node)
        if old is None:
            # A default written as a name or a call is a value with a source. Replacing
            # it with a literal keeps the number and throws away the only record of
            # where the number came from, so this one is left alone and said out loud.
            # Skipped rather than refused, so one such parameter cannot block the rest.
            written = ast.get_source_segment(src, node) or "an expression"
            skipped.append((name, f"defaults to {written}. Change {written} itself."))
            continue
        if old != new:
            edits.append((name, node, _format(old, new)))
    if not edits:
        return [], skipped

    out = src
    # Last edit first, so the offsets of the earlier ones are still the offsets.
    for _, node, text in sorted(edits, key=lambda e: (e[1].lineno, e[1].col_offset), reverse=True):
        out = _splice(out, node, text)

    # This rewrites someone's source, so it checks its own work before saving: the file
    # still parses, and every default it touched reads back as the number it wrote.
    check = _defaults(_part_function(ast.parse(out, filename=str(path)), path))
    for name, _, text in edits:
        if _number(check[name]) != float(text):
            raise EditError(f"rewriting {name} in {path.name} did not come out right")

    # Atomic, because the watcher is looking at this file: a partial write is a syntax
    # error the user did not make. The leading "_" is one of the names the watcher skips.
    tmp = path.with_name(f"_{path.name}.tmp")
    tmp.write_text(out, encoding="utf-8")
    os.replace(tmp, path)
    return sorted(name for name, _, _ in edits), skipped
