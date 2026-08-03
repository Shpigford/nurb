"""Printer profiles: the machine's facts, picked once per project.

A bed size belongs to the machine, so it lives in a shipped profile named by
printer.toml, never on a card. A card still wins for what its part has justified,
because the card is applied on top of the machine.
"""

import pytest

from nurb.checks import Context, _apply, from_card, global_file, printer, profiles


def project(tmp_path, printer_toml=None, card=None):
    (tmp_path / "parts").mkdir()
    if printer_toml is not None:
        (tmp_path / "printer.toml").write_text(printer_toml)
    part = tmp_path / "parts" / "thing.py"
    if card is not None:
        (tmp_path / "parts" / "thing.md").write_text(card)
    return part


def global_config(text):
    """conftest points XDG_CONFIG_HOME at a fresh directory for every test."""
    global_file().parent.mkdir(parents=True, exist_ok=True)
    global_file().write_text(text)


def test_every_shipped_profile_is_valid_context_settings():
    have = profiles()
    assert have, "no shipped profiles"
    for name, block in have.items():
        ctx = _apply(Context(), {"printer": block}, name)  # raises on a bad key
        assert len(ctx.bed) == 3, name
        assert all(v > 0 for v in ctx.bed), name


def test_no_printer_file_means_the_defaults(tmp_path):
    assert printer(tmp_path).bed == Context().bed


def test_the_file_names_a_shipped_profile(tmp_path):
    part = project(tmp_path, 'profile = "bambu_a1_mini"\n')
    assert from_card(part).bed == (180.0, 180.0, 180.0)


def test_an_unknown_profile_says_what_exists(tmp_path):
    project(tmp_path, 'profile = "made_up"\n')
    with pytest.raises(ValueError, match="bambu_a1_mini"):
        printer(tmp_path)


def test_the_export_table_is_not_a_printer_setting(tmp_path):
    """`[export]` belongs to `nurb export`; a check must walk past it, not choke."""
    project(tmp_path, 'profile = "bambu_a1_mini"\n\n[export]\nformats = ["stl"]\n')
    assert printer(tmp_path).bed == (180.0, 180.0, 180.0)


def test_a_direct_setting_overrides_the_profile(tmp_path):
    """The file can describe a machine no profile ships, or correct one that does."""
    project(tmp_path, 'profile = "bambu_a1_mini"\nbed = [300, 300, 300]\n')
    assert printer(tmp_path).bed == (300, 300, 300)


def test_a_name_on_the_command_line_beats_the_file(tmp_path):
    project(tmp_path, 'profile = "bambu_a1_mini"\n')
    assert printer(tmp_path, "prusa_mk4s").bed == (250.0, 210.0, 220.0)


def test_the_card_still_wins_for_what_the_part_justified(tmp_path):
    part = project(
        tmp_path,
        'profile = "bambu_a1_mini"\nmin_wall = 1.5\n',
        card="```toml\n[part]\nmin_wall = 1.0\n```\n",
    )
    ctx = from_card(part)
    assert ctx.bed == (180.0, 180.0, 180.0)  # the machine's
    assert ctx.min_wall == 1.0  # the part's


def test_broken_toml_names_the_file(tmp_path):
    project(tmp_path, "profile = \n")
    with pytest.raises(ValueError, match="printer.toml"):
        printer(tmp_path)


# --- the global config -------------------------------------------------------


def test_the_global_config_names_the_profile(tmp_path):
    """A printer is a fact about the workshop, so naming it once covers every project."""
    project(tmp_path)
    global_config('profile = "bambu_a1_mini"\n')
    assert printer(tmp_path).bed == (180.0, 180.0, 180.0)


def test_the_projects_profile_beats_the_globals(tmp_path):
    project(tmp_path, 'profile = "prusa_mk4s"\n')
    global_config('profile = "bambu_a1_mini"\n')
    assert printer(tmp_path).bed == (250.0, 210.0, 220.0)


def test_a_global_setting_layers_under_the_project(tmp_path):
    """The global file can override machine facts too, and the project still wins."""
    project(tmp_path, "min_wall = 1.5\n")
    global_config("min_wall = 0.8\nbed = [300, 300, 300]\n")
    ctx = printer(tmp_path)
    assert ctx.min_wall == 1.5  # the project's
    assert ctx.bed == (300, 300, 300)  # the global's, unopposed


def test_broken_global_toml_names_the_file(tmp_path):
    project(tmp_path)
    global_config("profile = \n")
    with pytest.raises(ValueError, match="config.toml"):
        printer(tmp_path)


def test_a_typo_in_a_setting_is_an_error_not_a_shrug(tmp_path):
    project(tmp_path, "bedd = [1, 2, 3]\n")
    with pytest.raises(ValueError, match="bedd"):
        printer(tmp_path)
