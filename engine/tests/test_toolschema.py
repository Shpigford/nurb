"""tools.json has to survive the trip into an Anthropic tool definition."""

import json
import pathlib

from nurb import toolschema

TOOLS_FILE = pathlib.Path(__file__).parents[1] / "src" / "nurb" / "tools.json"

REJECTED = {
    "pattern",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "multipleOf",
    "oneOf",
    "$ref",
    "$defs",
    "definitions",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "maxItems",
    "uniqueItems",
}


def contract():
    return json.loads(TOOLS_FILE.read_text(encoding="utf-8"))


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def test_no_rejected_keyword_survives_at_any_depth():
    for node in walk(toolschema.anthropic_tools(contract())):
        assert REJECTED.isdisjoint(node), sorted(REJECTED & set(node))


def test_every_object_node_closes_its_properties():
    for tool in toolschema.anthropic_tools(contract()):
        for node in walk(tool["input_schema"]):
            if node.get("type") == "object" or "properties" in node:
                assert node["additionalProperties"] is False


def test_every_tool_keeps_its_name_and_description():
    tools = toolschema.anthropic_tools(contract())
    assert [t["name"] for t in tools] == [t["name"] for t in contract()]
    assert [t["description"] for t in tools] == [t["description"] for t in contract()]


def test_a_bound_becomes_a_sentence_in_the_description():
    tools = {tool["name"]: tool for tool in toolschema.anthropic_tools(contract())}
    limit = tools["get_project"]["input_schema"]["properties"]["source_limit"]
    assert "100000" in limit["description"]


def test_one_of_becomes_any_of_and_a_ref_is_inlined():
    schema = {
        "type": "object",
        "properties": {
            "size": {"oneOf": [{"type": "number"}, {"type": "string"}]},
            "point": {"$ref": "#/$defs/point"},
        },
        "$defs": {"point": {"type": "object", "properties": {"x": {"type": "number"}}}},
    }
    out = toolschema.strip(schema)
    assert "$defs" not in out
    assert out["properties"]["size"]["anyOf"] == [{"type": "number"}, {"type": "string"}]
    assert out["properties"]["point"]["properties"]["x"] == {"type": "number"}
    assert out["properties"]["point"]["additionalProperties"] is False


def test_enum_and_default_are_left_alone():
    schema = {"type": "string", "enum": ["a", "b"], "default": "a", "minLength": 1}
    out = toolschema.strip(schema)
    assert out["enum"] == ["a", "b"]
    assert out["default"] == "a"
    assert "At least 1 character." in out["description"]


def test_a_schema_valued_additional_properties_is_kept():
    out = toolschema.strip(
        {"type": "object", "properties": {"a": {"type": "string"}}, "additionalProperties": {"type": "string", "minLength": 1}}
    )
    assert out["additionalProperties"] == {"type": "string", "description": "At least 1 character."}

