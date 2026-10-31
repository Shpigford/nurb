"""tools.json rewritten for the Anthropic Messages API, which rejects most JSON Schema.

The bounds still matter to the model, so they are folded into the description rather
than dropped: a rejected schema and a forgotten limit are both wrong answers.
"""

SENTENCES = {
    "pattern": lambda v: f"Matches {v}.",
    "minLength": lambda v: f"At least {v} character{'' if v == 1 else 's'}.",
    "maxLength": lambda v: f"At most {v} character{'' if v == 1 else 's'}.",
    "minimum": lambda v: f"At least {v}.",
    "maximum": lambda v: f"At most {v}.",
    "exclusiveMinimum": lambda v: f"Greater than {v}.",
    "exclusiveMaximum": lambda v: f"Less than {v}.",
    "multipleOf": lambda v: f"A multiple of {v}.",
    "maxItems": lambda v: f"At most {v} item{'' if v == 1 else 's'}.",
    "uniqueItems": lambda v: "Items are unique." if v else "",
}

# A pair reads better as one sentence than as two, so they are folded together.
PAIRS = [
    ("minimum", "maximum", "Between {0} and {1}."),
    ("minLength", "maxLength", "Between {0} and {1} characters."),
]

# The API takes a small minItems, so only a count it would reject becomes prose.
KEPT_MIN_ITEMS = (0, 1)


def strip(schema, defs=None):
    """One node of a JSON Schema, with the rejected keywords folded into description."""
    if not isinstance(schema, dict):
        return schema
    defs = {**(defs or {}), **schema.get("$defs", {}), **schema.get("definitions", {})}
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        target = defs.get(ref.rsplit("/", 1)[-1], {})
        merged = {**target, **{k: v for k, v in schema.items() if k != "$ref"}}
        return strip(merged, defs)

    out, notes = {}, []
    for key, value in schema.items():
        if key in ("$defs", "definitions"):
            continue
        if key in SENTENCES:
            continue
        if key == "minItems" and value not in KEPT_MIN_ITEMS:
            continue
        if key == "oneOf":
            key = "anyOf"
        if key in ("properties", "patternProperties"):
            value = {name: strip(child, defs) for name, child in value.items()}
        elif key in ("anyOf", "allOf", "oneOf", "prefixItems"):
            value = [strip(child, defs) for child in value]
        elif key in ("items", "additionalProperties", "not", "contains"):
            value = strip(value, defs)
        out[key] = value

    seen = set()
    for low, high, template in PAIRS:
        if low in schema and high in schema:
            notes.append(template.format(schema[low], schema[high]))
            seen |= {low, high}
    count = schema.get("minItems")
    if count is not None and count not in KEPT_MIN_ITEMS:
        notes.append(f"At least {count} items.")
    for key, sentence in SENTENCES.items():
        if key in schema and key not in seen:
            note = sentence(schema[key])
            if note:
                notes.append(note)
    if notes:
        description = " ".join([out.get("description", "").strip(), *notes]).strip()
        out["description"] = description

    types = out.get("type")
    types = types if isinstance(types, list) else [types]
    if "object" in types or "properties" in out:
        out.setdefault("additionalProperties", False)
    return out


def anthropic_tools(tools_json):
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": strip(tool["inputSchema"]),
        }
        for tool in tools_json
    ]
