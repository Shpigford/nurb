"""A card carries a part's check settings, so parsing it has to fail loudly.

The second half covers the AUTO block, whose two properties are that it never disagrees
with the geometry and that regenerating it changes nothing unless the geometry moved.
"""

import pytest

from nurb import card
from nurb.checks import Context, from_card


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

    This is the test that makes `nurb card` worth running: it builds all three example
    parts and asserts the blocks already on disk are what the geometry produces now.
    """
    import pathlib

    from nurb import builder, checks

    parts = pathlib.Path(__file__).parents[1] / "examples" / "notch" / "parts"
    for part in sorted(parts.glob("*.py")):
        shape, _, _ = builder.build(part, draft=False)
        ctx = checks.from_card(part)
        want = card.render(card.facts(shape, ctx, checks.run(shape, ctx)))
        assert want in part.with_suffix(".md").read_text(), f"{part.stem}: run nurb card"
