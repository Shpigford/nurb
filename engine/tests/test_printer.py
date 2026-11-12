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
    printer_line,
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


def test_choosing_a_printer_writes_the_workshop_file(tmp_path):
    """The first pick is a workshop fact, so the next project does not ask again."""
    project(tmp_path)
    written = choose_profile(tmp_path, "bambu_a1_mini")
    assert written == global_file()
    assert written.read_text() == 'profile = "bambu_a1_mini"\n'
    assert not (tmp_path / "printer.toml").exists()
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
    project(tmp_path, '# a hand-written note\nprofile = "bambu_a1_mini"\n\n[export]\nformats = ["stl"]\n')
    choose_profile(tmp_path, "bambu_x1c")
    text = (tmp_path / "printer.toml").read_text()
    assert text.index("profile") < text.index("[export]")
    assert "a hand-written note" in text
    assert 'profile = "bambu_x1c"' in text


def test_a_printer_nurb_does_not_ship_is_refused_before_it_is_written(tmp_path):
    project(tmp_path)
    with pytest.raises(ValueError, match="no printer profile"):
        choose_profile(tmp_path, "voron_2_4")
    assert not (tmp_path / "printer.toml").exists()
    assert not global_file().exists()


def test_the_first_pick_inserts_above_export_in_an_existing_workshop_file(tmp_path):
    """Replacing the file would wipe standing export formats."""
    project(tmp_path)
    global_config('# keep me\n[export]\nformats = ["stl", "step"]\n')
    written = choose_profile(tmp_path, "bambu_a1_mini")
    assert written == global_file()
    text = written.read_text()
    assert "keep me" in text
    assert text.index("profile") < text.index("[export]")
    assert 'formats = ["stl", "step"]' in text
    assert not (tmp_path / "printer.toml").exists()


def test_export_only_printer_toml_is_not_an_exception_project(tmp_path):
    project(tmp_path, '[export]\nformats = ["stl"]\n')
    choose_profile(tmp_path, "bambu_a1_mini")
    assert global_file().read_text() == 'profile = "bambu_a1_mini"\n'
    assert (tmp_path / "printer.toml").read_text() == '[export]\nformats = ["stl"]\n'


def test_a_later_different_pick_writes_the_project_override(tmp_path):
    project(tmp_path)
    global_config('profile = "bambu_a1_mini"\n')
    written = choose_profile(tmp_path, "prusa_mk4s")
    assert written == tmp_path / "printer.toml"
    assert global_file().read_text() == 'profile = "bambu_a1_mini"\n'
    assert written.read_text() == 'profile = "prusa_mk4s"\n'


def test_picking_the_workshop_machine_again_writes_nothing(tmp_path):
    project(tmp_path)
    global_config('profile = "bambu_a1_mini"\n')
    written = choose_profile(tmp_path, "bambu_a1_mini")
    assert written == global_file()
    assert not (tmp_path / "printer.toml").exists()
    assert global_file().read_text() == 'profile = "bambu_a1_mini"\n'


def test_printer_line_names_the_source_and_the_bed(tmp_path):
    project(tmp_path)
    global_config('profile = "bambu_a1_mini"\n')
    assert printer_line(tmp_path) == (
        "printer: bambu_a1_mini (global)  180 x 180 x 180 mm"
    )
    (tmp_path / "printer.toml").write_text('profile = "prusa_mk4s"\n')
    assert printer_line(tmp_path) == (
        "printer: prusa_mk4s (printer.toml)  250 x 210 x 220 mm"
    )


def test_printer_line_unnamed_uses_the_resolved_bed(tmp_path):
    project(tmp_path, "bed = [180, 120, 180]\n")
    line = printer_line(tmp_path)
    assert line.startswith("printer: unnamed (default)  180 x 120 x 180 mm")
    assert "config.toml" in line


def test_printer_line_survives_broken_toml(tmp_path):
    project(tmp_path, "profile = \n")
    line = printer_line(tmp_path)
    assert line.startswith("printer: unnamed (default)  256 x 256 x 256 mm")


def test_printer_line_announces_the_flag_profile(tmp_path):
    project(tmp_path)
    assert printer_line(tmp_path, "prusa_mk4s") == (
        "printer: prusa_mk4s (--printer)  250 x 210 x 220 mm"
    )


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
        "label": "Bambu Lab X2D",
        "brand": "Bambu Lab",
    }


def test_the_p2s_profile_matches_the_vendor_and_slicer():
    have = profiles()
    assert have["bambu_p2s"] == {
        "bed": [256.0, 256.0, 256.0],
        "slicer": "Bambu Lab P2S",
        "label": "Bambu Lab P2S",
        "brand": "Bambu Lab",
    }


def test_the_k2_plus_profile_matches_the_vendor_and_slicer():
    """The only Creality on the list was the Ender-3 V3, so a K2 Plus owner had no
    profile to name and no way to add one: profiles ship inside the package, and
    printer.toml can name a machine but not define one, because a `slicer` key there
    is refused as an unknown check setting. Hand-adding the entry worked until the
    next upgrade rewrote the file and took it out again."""
    have = profiles()
    assert have["creality_k2_plus"] == {
        "bed": [350.0, 350.0, 350.0],
        "slicer": "Creality K2 Plus",
        "label": "Creality K2 Plus",
        "brand": "Creality",
    }


def test_anycubic_kobra_2_profile_matches_the_vendor_and_slicer():
    have = profiles()
    assert have["anycubic_kobra_2"] == {
        "bed": [220.0, 220.0, 250.0],
        "slicer": "Anycubic Kobra 2",
        "label": "Anycubic Kobra 2",
        "brand": "Anycubic",
    }


def test_the_core_one_and_the_other_current_prusas_are_shipped():
    """The only Prusas were the MK4S, MINI and XL, so a CORE One or CORE One L owner had
    no profile to name and every print estimate dead-ended at the picker. Each preset
    name is one PrusaSlicer's and OrcaSlicer's own bundles carry."""
    have = profiles()
    assert have["prusa_core_one"] == {
        "bed": [250.0, 220.0, 270.0],
        "slicer": "Prusa CORE One",
        "prusaslicer": "Prusa CORE One 0.4 nozzle",
        "label": "Prusa CORE One / One+",
        "brand": "Prusa",
    }
    assert have["prusa_core_one_l"] == {
        "bed": [300.0, 300.0, 330.0],
        "slicer": "Prusa CORE One L",
        "prusaslicer": "Prusa CORE One L 0.4 nozzle",
        "label": "Prusa CORE One L / L+",
        "brand": "Prusa",
    }
    assert have["prusa_mk4"]["bed"] == [250.0, 210.0, 220.0]
    assert have["prusa_mk3_5"]["bed"] == [250.0, 210.0, 210.0]
    assert have["prusa_mk3s"]["bed"] == [250.0, 210.0, 210.0]
    assert have["prusa_mk3s"]["prusaslicer"] == "Original Prusa i3 MK3S & MK3S+"


def test_the_voron_printers_are_shipped_one_entry_per_size():
    """A Voron is sold by size, and OrcaSlicer carries one machine per size, so each size
    is its own profile rather than a setting on one."""
    have = profiles()
    vorons = {name: block["bed"] for name, block in have.items() if block.get("brand") == "Voron"}
    assert vorons == {
        "voron_0_2": [120.0, 120.0, 120.0],
        "voron_trident_250": [250.0, 250.0, 250.0],
        "voron_trident_300": [300.0, 300.0, 250.0],
        "voron_trident_350": [350.0, 350.0, 250.0],
        "voron_2_4_250": [250.0, 250.0, 210.0],
        "voron_2_4_300": [300.0, 300.0, 260.0],
        "voron_2_4_350": [350.0, 350.0, 310.0],
        "voron_switchwire": [250.0, 210.0, 230.0],
    }
    assert have["voron_0_2"]["slicer"] == "Voron 0.1"
    assert have["voron_switchwire"]["slicer"] == "Voron Switchwire 250"


def test_the_workshop_list_adds_removes_and_hands_on_the_default(tmp_path):
    """A printer is a fact about the workshop, so the list and its default live in
    the global config and a project with no printer.toml inherits them."""
    from nurb import workshop

    assert workshop.workshop_printers() == []
    assert workshop.default_printer() is None

    assert workshop.add_workshop_printer("bambu_p1s") == ["bambu_p1s"]
    assert workshop.default_printer() == "bambu_p1s"  # the first one is the default
    assert workshop.add_workshop_printer("prusa_mk4s") == ["bambu_p1s", "prusa_mk4s"]
    assert workshop.default_printer() == "bambu_p1s"

    # A project that names nothing prints on the workshop default.
    part = project(tmp_path)
    assert list(printer(part.parents[1]).bed) == profiles()["bambu_p1s"]["bed"]

    assert workshop.set_default_printer("prusa_mk4s") == ["prusa_mk4s", "bambu_p1s"]
    assert workshop.remove_workshop_printer("prusa_mk4s") == ["bambu_p1s"]
    assert workshop.default_printer() == "bambu_p1s"  # the next one standing inherits
    assert workshop.remove_workshop_printer("bambu_p1s") == []
    assert workshop.default_printer() is None  # nothing left to name

    with pytest.raises(ValueError, match="no printer profile called"):
        workshop.add_workshop_printer("nosuchprinter")
    with pytest.raises(ValueError, match="not in the workshop"):
        workshop.remove_workshop_printer("bambu_p1s")
    with pytest.raises(ValueError, match="Add it first"):
        workshop.set_default_printer("bambu_p1s")


def test_the_workshop_list_keeps_the_comments_and_tables_in_the_config():
    """The config is hand-written: an [export] table must not swallow the new keys."""
    from nurb import workshop

    global_config('# my machines\nprofile = "bambu_a1"\n\n[export]\nformat = "3mf"\n')
    assert workshop.workshop_printers() == ["bambu_a1"]  # an older config still counts
    workshop.add_workshop_printer("prusa_mini")
    text = global_file().read_text()
    assert "# my machines" in text
    assert text.index("printers = ") < text.index("[export]")
    assert workshop.workshop_printers() == ["bambu_a1", "prusa_mini"]


MULTILINE = '''# my machines
printers = [
  "bambu_a1",
  "prusa_mini",
]
profile = "bambu_a1"

[export]
format = "3mf"
'''


@pytest.mark.parametrize(
    "act, expect",
    [
        (lambda w: w.add_workshop_printer("bambu_p1s"), ["bambu_a1", "prusa_mini", "bambu_p1s"]),
        (lambda w: w.remove_workshop_printer("prusa_mini"), ["bambu_a1"]),
        (lambda w: w.set_default_printer("prusa_mini"), ["prusa_mini", "bambu_a1"]),
    ],
)
def test_a_hand_written_multiline_list_survives_every_edit(act, expect):
    """A list written over several lines is one value, so a rewrite takes all of it.
    Replacing only its first line left the entries behind and the config stopped
    parsing, which took every project read down with it."""
    import tomllib

    from nurb import workshop

    global_config(MULTILINE)
    assert act(workshop) == expect

    text = global_file().read_text()
    read = tomllib.loads(text)  # raises if orphan entries were left behind
    # The file keeps insertion order; the default is moved to the front on read.
    assert sorted(read["printers"]) == sorted(expect)
    assert read.get("profile") == expect[0]
    assert read["export"] == {"format": "3mf"}
    assert "# my machines" in text
    assert text.index("printers = ") < text.index("[export]")
    assert workshop.workshop_printers() == expect
