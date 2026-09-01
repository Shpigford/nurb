"""Printer profiles: the machine's facts, picked once per project.

A bed size belongs to the machine, so it lives in a shipped profile named by
printer.toml, never on a card. A card still wins for what its part has justified,
because the card is applied on top of the machine.
"""

import pytest

from nurb.checks import (
    Context,
    _apply,
    choose_profile,
    from_card,
    global_file,
    printer,
    profiles,
)


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
    """Every key is a check setting except the few that are facts about the machine."""
    from nurb.checks import NOT_SETTINGS, machine_only

    have = profiles()
    assert have, "no shipped profiles"
    for name, block in have.items():
        ctx = _apply(Context(), {"printer": machine_only(block)}, name)  # raises on a bad key
        assert len(ctx.bed) == 3, name
        assert all(v > 0 for v in ctx.bed), name
        # The exclusions are for keys that exist, not a licence to write anything.
        assert set(block) - set(NOT_SETTINGS), name


def test_no_printer_file_means_the_defaults(tmp_path):
    assert printer(tmp_path).bed == Context().bed


def test_the_file_names_a_shipped_profile(tmp_path):
    part = project(tmp_path, 'profile = "bambu_a1_mini"\n')
    assert from_card(part).bed == (180.0, 180.0, 180.0)


def test_an_unknown_profile_says_what_exists(tmp_path):
    project(tmp_path, 'profile = "made_up"\n')
    with pytest.raises(ValueError, match="bambu_a1_mini"):
        printer(tmp_path)


def test_an_unknown_material_says_what_exists(tmp_path):
    project(tmp_path, 'material = "wood"\n')
    with pytest.raises(ValueError, match="petg"):
        printer(tmp_path)


def test_the_material_reaches_the_context_lowercased(tmp_path):
    """The file can say ABS; the SHRINK table speaks lowercase."""
    project(tmp_path, 'material = "ABS"\n')
    assert printer(tmp_path).material == "abs"


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


# --- choosing the machine from the viewer -------------------------------------
# The picker behind a print estimate writes the same `profile` line every command
# already reads, so naming the machine once in the app also settles the bed the rules
# check against. A printer.toml is usually hand-written, so only that line is touched.


def test_choosing_a_printer_writes_the_line_every_command_reads(tmp_path):
    project(tmp_path)
    written = choose_profile(tmp_path, "bambu_a1_mini")
    assert written == tmp_path / "printer.toml"
    assert written.read_text() == 'profile = "bambu_a1_mini"\n'
    assert printer(tmp_path).bed == (180.0, 180.0, 180.0)


def test_choosing_again_replaces_the_line_instead_of_adding_one(tmp_path):
    project(tmp_path, '# the machine, not the parts\nprofile = "bambu_a1_mini"\n')
    choose_profile(tmp_path, "prusa_mk4s")
    assert (tmp_path / "printer.toml").read_text() == (
        '# the machine, not the parts\nprofile = "prusa_mk4s"\n'
    )


def test_a_chosen_printer_lands_above_the_tables_not_inside_the_last_one(tmp_path):
    """Appended, `profile` would become a key of whatever table happens to be last,
    which parses as export.profile and leaves the machine still unnamed."""
    project(tmp_path, '# a hand-written note\nbed = [200.0, 200.0, 200.0]\n\n[export]\nformats = ["stl"]\n')
    choose_profile(tmp_path, "bambu_x1c")
    text = (tmp_path / "printer.toml").read_text()
    assert text.index("profile") < text.index("[export]")
    assert "a hand-written note" in text
    assert printer(tmp_path).bed == (200.0, 200.0, 200.0)  # the file still wins


def test_a_printer_nurb_does_not_ship_is_refused_before_it_is_written(tmp_path):
    project(tmp_path)
    with pytest.raises(ValueError, match="no printer profile"):
        choose_profile(tmp_path, "voron_2_4")
    assert not (tmp_path / "printer.toml").exists()


def test_the_h2_series_is_shipped_because_it_is_what_bambu_sells_now(tmp_path):
    """The gap this filled: a current flagship missing from the list makes every print
    estimate on it dead-end at the picker."""
    have = profiles()
    assert have["bambu_h2c"]["slicer"] == "Bambu Lab H2C"
    assert {"bambu_h2c", "bambu_h2d", "bambu_h2s"} <= set(have)


def test_the_x2d_is_shipped_because_it_is_what_bambu_sells_now():
    """Same gap as the H2 series: a current machine missing from the list makes every
    print estimate on it dead-end at the picker."""
    have = profiles()
    assert have["bambu_x2d"] == {
        "bed": [256.0, 256.0, 261.0],
        "slicer": "Bambu Lab X2D",
    }


def test_the_p2s_profile_matches_the_vendor_and_slicer():
    have = profiles()
    assert have["bambu_p2s"] == {
        "bed": [256.0, 256.0, 256.0],
        "slicer": "Bambu Lab P2S",
    }


def test_anycubic_kobra_2_profile_matches_the_vendor_and_slicer():
    have = profiles()
    assert have["anycubic_kobra_2"] == {
        "bed": [220.0, 220.0, 250.0],
        "slicer": "Anycubic Kobra 2",
    }


def test_the_machine_cannot_declare_a_part_prints_on_supports(tmp_path):
    """A judgement about one part, and machine-wide it would quietly excuse every
    cantilever in every project on the machine, from a file nothing prints."""
    project(tmp_path, "supports = true\n")
    with pytest.raises(ValueError, match="not about the machine"):
        printer(tmp_path)


def test_the_global_config_cannot_declare_supports_either(tmp_path):
    project(tmp_path)
    global_config("supports = true\n")
    with pytest.raises(ValueError, match="supports"):
        printer(tmp_path)


def test_a_card_may_still_declare_supports(tmp_path):
    """The refusal is about where it is written, not about the setting."""
    part = project(tmp_path, card="```toml\n[part]\nsupports = true\n```\n")
    assert from_card(part).supports is True
