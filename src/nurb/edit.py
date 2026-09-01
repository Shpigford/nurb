"""Write parameter values back into a part file's keyword defaults.

The keyword defaults are the parameters, so an exploration that ends up in the file has
to end up in the signature. This is the only module that writes to a part file, and it
rewrites exactly the default it was asked to and nothing else: the source is edited as
text at the offsets the parser reports, so comments, formatting and every other line
survive untouched. The same care extends to the card: a variant lives in its
`[variants.<name>.params]` block, and updating one replaces that block alone.
"""

import ast
import json
import os
import pathlib
import tomllib


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


def _header(line):
    """The key path a TOML section header line declares, or None."""
    s = line.strip()
    if not s.startswith("["):
        return None

    # Let TOML itself split dotted and quoted keys. Appending a marker makes the
    # otherwise-empty table discoverable without reimplementing TOML's key grammar.
    marker = "__nurb_header_marker__"
    try:
        parsed = tomllib.loads(f"{s}\n{marker} = true")
    except tomllib.TOMLDecodeError:
        return None

    def marked_path(value, path=()):
        if isinstance(value, dict):
            if value.get(marker) is True:
                return path
            for key, child in value.items():
                found = marked_path(child, path + (key,))
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = marked_path(child, path)
                if found is not None:
                    return found
        return None

    return marked_path(parsed)


def _toml_key(value):
    """One TOML key, bare when possible and quoted otherwise."""
    bare = value and all(c.isascii() and (c.isalnum() or c in "_-") for c in value)
    return value if bare else json.dumps(value, ensure_ascii=False)


def _key(line):
    """The top-level key a single-line `key = value` assignment declares, or None."""
    s = line.strip()
    if not s or s.startswith(("#", "[")):
        return None
    try:
        parsed = tomllib.loads(s)
    except tomllib.TOMLDecodeError:
        return None
    return next(iter(parsed), None)


def apply_variant(path, variant, values):
    """Write `values` into one variant's params block in the part's card.

    A variant is its overrides, so the whole `[variants.<name>.params]` section is
    replaced with what is on screen: a value dragged back to the part's default is no
    longer an override and drops out. Everything else in the card survives untouched.
    Returns the sorted parameter names written.
    """
    from .checks import CARD_SETTINGS

    path = pathlib.Path(path)
    card = path.with_suffix(".md")
    if not card.is_file():
        raise EditError(f"{path.stem} has no card to hold the variant")

    src = path.read_text(encoding="utf-8")
    defaults = _defaults(_part_function(ast.parse(src, filename=str(path)), path))

    def formatted(name, new):
        if isinstance(new, bool):
            return "true" if new else "false"
        if isinstance(new, str):
            # JSON and TOML share the escapes used here, but JSON's default surrogate
            # pairs are not valid TOML Unicode escapes. Write scalar values directly.
            return json.dumps(new, ensure_ascii=False)
        node = defaults.get(name)
        if node is None:
            raise EditError(f"{path.name} has no parameter named {name}")
        # The default says whether this dimension is an int or a float, exactly as
        # `apply` keeps for the signature itself. A default written as an expression
        # says nothing, so the value's own type decides.
        old = _number(node)
        return _format(old if old is not None else new, new)

    text = card.read_text(encoding="utf-8")
    opening = f"```{CARD_SETTINGS}"
    if opening not in text:
        raise EditError(f"{card.name} has no settings block declaring variants")
    head, _, rest = text.partition(opening)
    block, closing, tail = rest.partition("```")
    if not closing:
        raise EditError(f"{card.name}: the settings block never closes")

    lines = block.split("\n")
    target = ("variants", variant, "params")
    target_text = f"variants.{_toml_key(variant)}.params"
    body = [f"{k} = {formatted(k, v)}" for k, v in sorted(values.items())]
    start = next((i for i, l in enumerate(lines) if _header(l) == target), None)
    if start is None:
        # Cards also write the overrides as an inline table, `params = {...}` on one
        # line under [variants.<name>]. That line is the params, so it is what gets
        # replaced; adding a [variants.<name>.params] section next to it would define
        # params twice and no longer parse.
        head_i = next((i for i, l in enumerate(lines) if _header(l) == ("variants", variant)), None)
        inline = None
        if head_i is not None:
            end_i = next((j for j in range(head_i + 1, len(lines)) if _header(lines[j])), len(lines))
            inline = next((j for j in range(head_i + 1, end_i) if _key(lines[j]) == "params"), None)
        if inline is not None:
            lines[inline] = ("params = { " + ", ".join(body) + " }") if body else "params = {}"
        else:
            # The variant exists in some other form, [variants.<name>] alone or a
            # dotted sibling like [variants.<name>.accepted]; a fresh params section
            # goes in front of the first of them. A name the card never mentions is
            # not a variant.
            anchor = next(
                (i for i, l in enumerate(lines)
                 if (h := _header(l)) and len(h) >= 2 and h[:2] == ("variants", variant)),
                None,
            )
            if anchor is None:
                raise EditError(f"{card.name} has no variant named {variant}")
            lines[anchor:anchor] = [f"[{target_text}]", *body, ""]
    else:
        end = next((j for j in range(start + 1, len(lines)) if _header(lines[j])), len(lines))
        # Blank lines before the next header are the gap between sections, not ours.
        while end - 1 > start and not lines[end - 1].strip():
            end -= 1
        lines[start + 1 : end] = body
    new_block = "\n".join(lines)

    # This rewrites someone's card, so it checks its own work before saving: the block
    # still parses, and the variant reads back as exactly the values it was given.
    try:
        parsed = tomllib.loads(new_block)
    except tomllib.TOMLDecodeError as exc:
        raise EditError(f"updating {variant} in {card.name} did not come out right ({exc})") from exc
    if parsed.get("variants", {}).get(variant, {}).get("params") != values:
        raise EditError(f"updating {variant} in {card.name} did not come out right")

    # Atomic for the same reason `apply` is: the watcher rebuilds on this write.
    tmp = card.with_name(f"_{card.name}.tmp")
    tmp.write_text(head + opening + new_block + "```" + tail, encoding="utf-8")
    os.replace(tmp, card)
    return sorted(values)


def set_supports(path, on):
    """Turn `[part] supports` on or off in the part's card, and say what it reads now.

    The one thing `apply_variant` never has to handle, and the common case here: a card
    with no settings fence at all, which is what `nurb new` writes and what most cards
    stay until something needs declaring. That gets a fresh fence at the end rather than
    a refusal, because the whole point of the control this serves is that the user should
    not have to go and learn the file format first.

    Only the one key is touched. A card is hand-written, and the polish, the prose and
    every other setting in the fence belong to whoever wrote them.
    """
    from .checks import CARD_SETTINGS

    card = pathlib.Path(path).with_suffix(".md")
    if not card.is_file():
        raise EditError(f"{card.name} does not exist yet, so there is nowhere to record this")
    text = card.read_text(encoding="utf-8")
    opening = f"```{CARD_SETTINGS}"
    line = f"supports = {'true' if on else 'false'}"

    if opening not in text:
        # A blank line before the fence and a newline after it, so the card still reads
        # as prose with a settings block at the end rather than as a run-on paragraph.
        block = f"\n[part]\n{line}\n"
        head, tail = text.rstrip("\n") + "\n\n", "\n"
    else:
        head, _, rest = text.partition(opening)
        block, closing, tail = rest.partition("```")
        if not closing:
            raise EditError(f"{card.name}: the settings block never closes")
        lines = block.split("\n")
        start = next((i for i, l in enumerate(lines) if _header(l) == ("part",)), None)
        if start is None:
            # No [part] table yet. It goes at the top of the fence, above whatever
            # tables are already there, so the part's own settings read before the
            # machine's and the variants' do.
            lead = 1 if lines and not lines[0].strip() else 0
            lines[lead:lead] = ["[part]", line, ""]
        else:
            end = next((j for j in range(start + 1, len(lines)) if _header(lines[j])), len(lines))
            at = next((j for j in range(start + 1, end) if _key(lines[j]) == "supports"), None)
            if at is not None:
                lines[at] = line
            else:
                lines[start + 1 : start + 1] = [line]
        block = "\n".join(lines)

    # Same self-check as `apply_variant`: this is someone's card, so the block has to
    # parse and read back as the answer that was asked for before it replaces the file.
    try:
        parsed = tomllib.loads(block)
    except tomllib.TOMLDecodeError as exc:
        raise EditError(f"updating {card.name} did not come out right ({exc})") from exc
    if parsed.get("part", {}).get("supports") is not on:
        raise EditError(f"updating {card.name} did not come out right")

    tmp = card.with_name(f"_{card.name}.tmp")
    tmp.write_text(head + opening + block + "```" + tail, encoding="utf-8")
    os.replace(tmp, card)
    return on
