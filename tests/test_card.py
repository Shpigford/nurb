"""A card carries a part's check settings, so parsing it has to fail loudly.

The second half covers the AUTO block, whose two properties are that it never disagrees
with the geometry and that regenerating it changes nothing unless the geometry moved.
"""

import pytest

from nurb import card
from nurb.checks import Context, configurations, from_card


def write(tmp_path, body):
    (tmp_path / "thing.md").write_text(body)
    return tmp_path / "thing.py"


def test_no_card_means_nothing_is_excused(tmp_path):
    ctx = from_card(tmp_path / "absent.py")
    assert ctx.accepted == {}


def test_card_without_a_settings_block_is_fine(tmp_path):
    part = write(tmp_path, "# thing\n\n## Design notes\n\nJust prose.\n")
    assert from_card(part).accepted == {}


def test_accepted_counts_are_read(tmp_path):
    part = write(tmp_path, "## Accepted\n\n```toml\n[accepted]\nsliver = 18\n```\n")
    assert from_card(part).accepted == {"sliver": 18}


def test_printer_settings_override_the_defaults(tmp_path):
    part = write(
        tmp_path,
        "```toml\n[printer]\nbridge_limit = 8\nbed = [180, 180, 180]\n```\n",
    )
    ctx = from_card(part)
    assert ctx.bridge_limit == 8
    assert ctx.bed == (180, 180, 180)
    assert ctx.overhang_limit == Context().overhang_limit  # untouched


def test_a_typo_in_a_setting_name_is_an_error_not_a_shrug(tmp_path):
    part = write(tmp_path, "```toml\n[printer]\nbridge_limt = 8\n```\n")
    with pytest.raises(ValueError, match="bridge_limt"):
        from_card(part)


def test_broken_toml_says_which_card(tmp_path):
    part = write(tmp_path, "```toml\n[accepted\nsliver = 3\n```\n")
    with pytest.raises(ValueError, match="thing.md"):
        from_card(part)


def test_the_real_cards_parse(tmp_path):
    import pathlib

    parts = pathlib.Path(__file__).parents[1] / "examples" / "notch" / "parts"
    for part in sorted(parts.glob("*.py")):
        assert from_card(part).accepted.get("sliver") is not None, part.name


# --- variants ----------------------------------------------------------------


def test_a_part_with_no_variants_is_one_configuration(tmp_path):
    part = write(tmp_path, "```toml\n[accepted]\nsliver = 2\n```\n")
    name, overrides, ctx = configurations(part)[0]
    assert (name, overrides, ctx.accepted) == ("thing", {}, {"sliver": 2})


def test_a_variant_carries_overrides_and_its_own_baseline(tmp_path):
    """A catalog entry is a name, some overrides and its own baselines. Nothing else."""
    part = write(
        tmp_path,
        "```toml\n"
        "[part]\nmin_wall = 1.0\n\n"
        "[accepted]\nsliver = 18\n\n"
        "[variants.wide.params]\ngrid_x = 3\nbracket_count = 6\n\n"
        "[variants.wide.accepted]\nsliver = 26\n"
        "```\n",
    )
    base, wide = configurations(part)
    assert base[:2] == ("thing", {})
    assert wide[0] == "wide"
    assert wide[1] == {"grid_x": 3, "bracket_count": 6}
    assert wide[2].accepted == {"sliver": 26}
    assert wide[2].min_wall == 1.0  # the part's own settings carry into its variants
    assert base[2].accepted == {"sliver": 18}  # and the base is not contaminated


def test_a_variant_that_forgets_params_is_an_error_not_a_shrug(tmp_path):
    """`[variants.wide] grid_x = 3` looks right and silently overrides nothing."""
    part = write(tmp_path, "```toml\n[variants.wide]\ngrid_x = 3\n```\n")
    with pytest.raises(ValueError, match=r"variants.wide.params"):
        configurations(part)


def test_the_block_records_every_shipped_configuration():
    """A card describing only the defaults leaves most of a family unrecorded."""
    import pathlib

    from nurb import builder, checks

    part = pathlib.Path(__file__).parents[1] / "examples" / "notch" / "parts" / "hook_scissors.py"
    built = []
    for name, overrides, ctx in configurations(part):
        shape, _, _ = builder.build(part, overrides=overrides or None)
        built.append((name, shape, ctx, checks.run(shape, ctx)))
    lines = card.facts(built[0][1], built[0][2], built[0][3], variants=built[1:])
    assert [line for line in lines if line.startswith("Variant hook_utility:")]
    assert [line for line in lines if line.startswith("Variant hook_utility_long:")]


def test_a_variant_line_records_disconnected_solids():
    """A variant must not say `clean` while hiding a broken one-solid contract."""
    from build123d import Box, Pos

    base = Box(10, 10, 10)
    split = base + Pos(20, 0, 0) * Box(10, 10, 10)
    ctx = Context()
    line = card.facts(base, ctx, [], variants=[("split", split, ctx, [])])[-1]
    assert "2 solids" in line
    assert "2000.0 mm3" in line


# --- the AUTO block ----------------------------------------------------------

FACTS = ["Size: 1 x 2 x 3 mm", "Checks: clean"]


def test_the_block_goes_under_the_title(tmp_path):
    out = card.graft("# thing\n\n## What it is\n\nA thing.\n", FACTS)
    assert out.startswith("# thing\n\n" + card.OPEN)
    assert "## What it is\n\nA thing.\n" in out


def test_regenerating_replaces_rather_than_stacks():
    once = card.graft("# thing\n\nprose\n", FACTS)
    twice = card.graft(once, FACTS)
    assert once == twice
    assert twice.count(card.OPEN) == 1


def test_new_facts_land_and_the_prose_survives():
    once = card.graft("# thing\n\nprose worth keeping\n", FACTS)
    twice = card.graft(once, ["Size: 9 x 9 x 9 mm", "Checks: clean"])
    assert "9 x 9 x 9" in twice
    assert "1 x 2 x 3" not in twice
    assert "prose worth keeping" in twice


def test_a_card_with_no_title_still_gets_a_block():
    assert card.graft("just prose\n", FACTS).startswith(card.OPEN)


def test_a_block_written_by_an_older_wording_is_replaced_not_duplicated():
    """The block is found by its marker, not by its exact opening sentence.

    Matching the whole sentence means that editing it once leaves every card on disk with
    an unrecognised block, and the next `nurb card` adds a second one underneath.
    """
    stale = "# thing\n\n<!-- AUTO some older wording -->\nSize: old\n<!-- /AUTO -->\n\nprose\n"
    out = card.graft(stale, FACTS)
    assert out.count(card.CLOSE) == 1
    assert "older wording" not in out
    assert "Size: old" not in out
    assert "prose" in out


def test_generated_lines_are_ascii():
    """A superscript here is encoding-dependent in a way prose is not.

    Written on a machine that is not utf-8, mm³ comes back as invalid utf-8 elsewhere and
    nothing can read the card at all. `checks.py` already writes mm2 for this reason.
    """
    for line in FACTS + ["Slivers: 6 under 1.0mm2, smallest 0.866mm2, 6 accepted"]:
        line.encode("ascii")  # raises if not
    import pathlib

    parts = pathlib.Path(__file__).parents[1] / "examples" / "notch" / "parts"
    for part in sorted(parts.glob("*.py")):
        text = part.with_suffix(".md").read_text(encoding="utf-8")
        block = text.split(card.MARK, 1)[1].split(card.CLOSE, 1)[0]
        block.encode("ascii")  # the block, not the prose around it


def test_an_empty_section_is_reported(tmp_path):
    text = "# thing\n\n## What it is\n\nA thing.\n\n## Design notes\n\n## Don't\n\n"
    thin = card.thin(text)
    assert "## Don't" in thin  # present but empty, which is the common way it goes wrong
    assert "## Design notes" in thin
    assert "## Changelog" in thin  # missing outright
    assert "## What it is" not in thin


def test_a_filled_card_is_not_thin():
    filled = "".join(f"{h}\n\nsomething\n\n" for h in card.REQUIRED)
    assert card.thin(filled) == []


def test_the_verdict_reads_as_a_summary():
    from nurb.checks import FAIL, WARN, Finding

    assert card._verdict(None) == "not run"
    assert card._verdict([]) == "clean"
    said = card._verdict(
        [Finding("overhang", FAIL, "x"), Finding("sliver", WARN, "y"), Finding("sliver", WARN, "z")]
    )
    assert said == "3 findings: 1 fail (overhang), 2 warn (sliver)"


def test_the_real_cards_are_current():
    """A stale AUTO block is a card disagreeing with its own part.

    This is the test that makes `nurb card` worth running: it builds every example part
    and asserts the blocks already on disk are what the geometry produces now.

    A part that renders text is skipped, because its glyph outlines come from a system
    font and so its volume, face count and sliver count are that machine's rather than
    the part's. The calibration coupon is the only one, and it measures 2600.6mm3 with
    88 faces here against 2601.0 and 83 on CI. The doctrine's "no text labels on parts"
    rule now has a second reason behind it: text is not reproducible.
    """
    import pathlib

    from nurb import builder, checks

    parts = pathlib.Path(__file__).parents[1] / "examples" / "notch" / "parts"
    for part in sorted(parts.glob("*.py")):
        if "Text(" in part.read_text(encoding="utf-8"):
            continue
        built = []
        for name, overrides, ctx in checks.configurations(part):
            shape, _, _ = builder.build(part, overrides=overrides or None, draft=False)
            built.append((name, shape, ctx, checks.run(shape, ctx)))
        _, shape, ctx, found = built[0]
        want = card.render(card.facts(shape, ctx, found, variants=built[1:]))
        assert want in part.with_suffix(".md").read_text(), f"{part.stem}: run nurb card"


# --- what changed since the card was written ---------------------------------


def block(lines):
    """A card carrying exactly these AUTO lines."""
    return card.render(lines)


def test_a_card_with_no_block_has_nothing_recorded(tmp_path):
    part = write(tmp_path, "# thing\n\nJust prose.\n")
    assert card.recorded(part) is None


def test_recorded_reads_back_what_facts_wrote(tmp_path):
    lines = ["Size: 60.00 x 30.00 x 6.00 mm, 10800.0 mm3, 1 solid, 6 faces", "Checks: clean"]
    (tmp_path / "thing.md").write_text(f"# thing\n\n{block(lines)}\n", encoding="utf-8")
    assert card.recorded(tmp_path / "thing.py") == lines


def test_an_unchanged_part_reports_nothing():
    lines = ["Size: 60.00 x 30.00 x 6.00 mm, 10800.0 mm3, 1 solid, 6 faces", "Checks: clean"]
    assert card.compare(lines, lines) == []


def test_a_lost_chamfer_shows_up_as_faces():
    """The case the command exists for: a part that still builds, still checks clean,
    still looks right, and quietly has three fewer faces than it did."""
    was = ["Size: 60.00 x 30.00 x 14.00 mm, 11694.8 mm3, 1 solid, 44 faces", "Checks: clean"]
    now = ["Size: 60.00 x 30.00 x 14.00 mm, 11674.9 mm3, 1 solid, 41 faces", "Checks: clean"]
    assert card.compare(was, now) == ["volume: 11694.8 -> 11674.9 mm3, -0.2%", "faces: 44 -> 41"]


def test_a_dimension_carries_its_delta():
    was = ["Size: 60.00 x 30.00 x 6.00 mm, 10800.0 mm3, 1 solid, 6 faces"]
    now = ["Size: 60.00 x 30.00 x 8.00 mm, 14400.0 mm3, 1 solid, 6 faces"]
    assert card.compare(was, now)[0] == "z: 6.00 -> 8.00 mm (+2.00)"


def test_a_new_verdict_is_reported_in_its_own_words():
    was = ["Size: 1.00 x 1.00 x 1.00 mm, 1.0 mm3, 1 solid, 6 faces", "Checks: clean"]
    now = [was[0], "Checks: 1 finding: 1 fail (min_wall)"]
    assert card.compare(was, now) == ["Checks: clean -> 1 finding: 1 fail (min_wall)"]


def test_a_line_that_appears_or_vanishes_says_which():
    size = "Size: 1.00 x 1.00 x 1.00 mm, 1.0 mm3, 1 solid, 6 faces"
    assert card.compare([size], [size, "Slivers: 4 under 1.0mm2"]) == ["gained Slivers: 4 under 1.0mm2"]
    assert card.compare([size, "Slivers: 4 under 1.0mm2"], [size]) == ["lost Slivers: 4 under 1.0mm2"]


def test_a_size_line_this_parser_cannot_read_still_reports_the_change():
    """An older card, or a format that moved on. Say the whole line rather than nothing."""
    changes = card.compare(["Size: who knows"], ["Size: 1.00 x 1.00 x 1.00 mm, 1.0 mm3, 1 solid, 6 faces"])
    assert len(changes) == 1 and "->" in changes[0]


def test_a_variant_is_measured_too_and_says_which_one():
    """A variant is a shipped configuration, so a chamfer it loses matters as much."""
    size = "Size: 1.00 x 1.00 x 1.00 mm, 1.0 mm3, 1 solid, 6 faces"
    was = [size, "Variant wide: 155.00 x 30.00 x 20.00 mm, 37000.0 mm3, 1 solid, 12 faces, 0 under 1.0mm2, clean"]
    now = [size, "Variant wide: 155.00 x 30.00 x 20.00 mm, 37000.0 mm3, 1 solid, 9 faces, 0 under 1.0mm2, clean"]
    assert card.compare(was, now) == ["wide faces: 12 -> 9"]


def test_a_variant_that_went_red_is_not_dropped():
    """The verdict sits past the numbers `_moved` names, so it needs reporting too."""
    size = "Size: 1.00 x 1.00 x 1.00 mm, 1.0 mm3, 1 solid, 6 faces"
    was = [size, "Variant wide: 10.00 x 10.00 x 10.00 mm, 1000.0 mm3, 1 solid, 6 faces, 0 under 1.0mm2, clean"]
    now = [size, "Variant wide: 10.00 x 10.00 x 10.00 mm, 1000.0 mm3, 1 solid, 6 faces, 0 under 1.0mm2, 1 finding: 1 fail (solids)"]
    assert card.compare(was, now) == ["wide clean -> 1 finding: 1 fail (solids)"]


def test_the_default_verdict_still_reads_as_its_own_line():
    """`Checks:` carries no measurements, so it falls to the plain branch."""
    size = "Size: 1.00 x 1.00 x 1.00 mm, 1.0 mm3, 1 solid, 6 faces"
    assert card.compare([size, "Checks: clean"], [size, "Checks: 1 finding: 1 warn (sliver)"]) == [
        "Checks: clean -> 1 finding: 1 warn (sliver)"
    ]


def test_the_card_can_declare_the_part_prints_on_supports(tmp_path):
    part = write(tmp_path, "```toml\n[part]\nsupports = true\n```")
    assert from_card(part).supports is True


def test_supports_is_off_unless_a_card_says_otherwise(tmp_path):
    part = write(tmp_path, "```toml\n[part]\nmin_wall = 2.0\n```")
    assert from_card(part).supports is False


def test_a_variant_can_decline_the_parts_supports(tmp_path):
    """Inheritance runs base-first, so a supported part hands the flag to every
    variant. The diagonal one, whose whole point is not needing them, has to be able
    to give it back."""
    part = write(
        tmp_path,
        "```toml\n[part]\nsupports = true\n\n"
        "[variants.upright.params]\nwidth = 12.0\n\n"
        "[variants.diagonal.params]\nwidth = 12.0\n\n"
        "[variants.diagonal.part]\nsupports = false\n```",
    )
    by_name = {name: ctx for name, _, ctx in configurations(part)}
    assert by_name["upright"].supports is True
    assert by_name["diagonal"].supports is False


def test_supports_written_as_a_string_is_an_error_not_a_shrug(tmp_path):
    """Every other setting is a number a rule compares against, so a wrong type gives
    itself away. This one is only tested for truth, and "false" is true."""
    part = write(tmp_path, '```toml\n[part]\nsupports = "false"\n```')
    with pytest.raises(ValueError, match="true or false"):
        from_card(part)
