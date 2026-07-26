"""A card carries a part's check settings, so parsing it has to fail loudly."""

import pytest

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
