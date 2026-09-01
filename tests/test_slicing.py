"""The slicer handoff, against a profile tree built here rather than an installed app.

Nothing in CI has a slicer, and a test that skips when one is missing is a test that
never runs. So the vendor bundle is faked at its real shape and everything except the
subprocess itself is exercised: the profile picks, the refusals, and reading back the
two numbers from the files a slicer leaves behind.
"""

import json
import pathlib
from types import SimpleNamespace

import sys

import pytest

from nurb import checks, slicing


def vendor(tmp_path, machines=("Bambu Lab A1 mini 0.4 nozzle",), processes=(), filaments=()):
    """A profile tree laid out the way a slicer ships one."""
    root = tmp_path / "profiles" / "BBL"
    for kind, entries in (("machine", machines), ("process", processes), ("filament", filaments)):
        (root / kind).mkdir(parents=True, exist_ok=True)
        for entry in entries:
            name, compatible = entry if isinstance(entry, tuple) else (entry, [])
            (root / kind / f"{name}.json").write_text(
                json.dumps({"name": name, "instantiation": "true", "compatible_printers": compatible}),
                encoding="utf-8",
            )
    return tmp_path / "profiles"


# --- finding the machine ------------------------------------------------------


def test_the_machine_is_found_by_the_name_a_slicer_knows_it_under(tmp_path):
    found = slicing.machine(vendor(tmp_path), "Bambu Lab A1 mini")
    assert found.stem == "Bambu Lab A1 mini 0.4 nozzle"


def test_a_missing_machine_names_its_neighbours_not_the_alphabet(tmp_path):
    """Someone whose MK4S is absent needs the other Prusas, not the first six of 92."""
    profiles = vendor(tmp_path, machines=(
        "Anker M5 0.4 nozzle", "Prusa MINI 0.4 nozzle", "Prusa MK3S 0.4 nozzle",
    ))
    with pytest.raises(slicing.Unavailable) as exc:
        slicing.machine(profiles, "Prusa MK4S")
    assert "Prusa MINI, Prusa MK3S" in str(exc.value)
    assert "Anker" not in str(exc.value)


def test_a_maker_the_slicer_has_never_heard_of_says_so(tmp_path):
    with pytest.raises(slicing.Unavailable, match="nothing from Voron"):
        slicing.machine(vendor(tmp_path), "Voron 2.4")


def test_the_nozzle_is_part_of_the_machine(tmp_path):
    profiles = vendor(tmp_path, machines=("Bambu Lab A1 mini 0.4 nozzle", "Bambu Lab A1 mini 0.8 nozzle"))
    assert slicing.machine(profiles, "Bambu Lab A1 mini", "0.8").stem.endswith("0.8 nozzle")


def test_a_missing_nozzle_lists_sizes_for_this_machine(tmp_path):
    profiles = vendor(
        tmp_path,
        machines=("Bambu Lab A1 mini 0.4 nozzle", "Bambu Lab A1 mini 0.8 nozzle"),
    )
    with pytest.raises(slicing.Unavailable) as exc:
        slicing.machine(profiles, "Bambu Lab A1 mini", "9.9")
    assert "For this machine it has: 0.4mm, 0.8mm nozzle" in str(exc.value)
    assert "nothing from Bambu" not in str(exc.value)


# --- picking the process and the filament -------------------------------------


PRINTER = "Bambu Lab A1 mini 0.4 nozzle"


def test_compatibility_comes_from_the_bundle_not_from_the_name(tmp_path):
    """`compatible_printers` is the vendor's own answer, and name suffixes are not."""
    profiles = vendor(
        tmp_path,
        processes=[("0.20mm Standard @BBL A1M", [PRINTER]), ("0.20mm Standard @BBL X1C", ["Bambu Lab X1 Carbon 0.4 nozzle"])],
        filaments=[("Bambu PLA Basic @BBL A1M", [PRINTER])],
    )
    process, filament = slicing.profiles_for(profiles / "BBL" / "machine" / f"{PRINTER}.json")
    assert process.stem.endswith("A1M")
    assert filament.stem.endswith("A1M")


def test_the_asked_for_layer_height_wins(tmp_path):
    profiles = vendor(
        tmp_path,
        processes=[("0.20mm Standard @BBL A1M", [PRINTER]), ("0.28mm Extra Draft @BBL A1M", [PRINTER])],
        filaments=[("Bambu PLA Basic @BBL A1M", [PRINTER])],
    )
    machine = profiles / "BBL" / "machine" / f"{PRINTER}.json"
    assert slicing.profiles_for(machine, layer="0.28")[0].stem.startswith("0.28mm")


def test_a_coarse_nozzle_falls_back_rather_than_refusing(tmp_path):
    """No 0.20mm process exists for a 0.8 nozzle, and a slice is still worth having."""
    profiles = vendor(
        tmp_path,
        processes=[("0.40mm Standard @BBL A1M 0.8 nozzle", [PRINTER])],
        filaments=[("Bambu PLA Basic @BBL A1M", [PRINTER])],
    )
    machine = profiles / "BBL" / "machine" / f"{PRINTER}.json"
    assert slicing.profiles_for(machine, layer="0.20")[0].stem.startswith("0.40mm")


def test_a_filament_with_no_compatible_profile_is_named(tmp_path):
    profiles = vendor(tmp_path, processes=[("0.20mm Standard @BBL A1M", [PRINTER])])
    machine = profiles / "BBL" / "machine" / f"{PRINTER}.json"
    with pytest.raises(slicing.Unavailable, match="no filament profile"):
        slicing.profiles_for(machine)


def test_an_unknown_filament_does_not_fall_back_to_another_material(tmp_path):
    profiles = vendor(
        tmp_path,
        processes=[("0.20mm Standard @BBL A1M", [PRINTER])],
        filaments=[("Bambu ABS @BBL A1M", [PRINTER])],
    )
    machine = profiles / "BBL" / "machine" / f"{PRINTER}.json"
    with pytest.raises(slicing.Unavailable, match="no filament profile matching 'PLA'"):
        slicing.profiles_for(machine, filament="PLA")


def test_plain_pla_does_not_fall_back_to_pla_cf(tmp_path):
    profiles = vendor(
        tmp_path,
        processes=[("0.20mm Standard @BBL A1M", [PRINTER])],
        filaments=[("Bambu PLA-CF @BBL A1M", [PRINTER])],
    )
    machine = profiles / "BBL" / "machine" / f"{PRINTER}.json"
    with pytest.raises(slicing.Unavailable, match="no filament profile matching 'PLA'"):
        slicing.profiles_for(machine, filament="PLA")


def test_a_profile_that_is_only_a_template_is_never_picked(tmp_path):
    """Vendor bundles carry uninstantiable fragments beside the real presets."""
    profiles = vendor(
        tmp_path,
        processes=[("0.20mm Standard @BBL A1M", [PRINTER])],
        filaments=[("Bambu PLA Basic @BBL A1M", [PRINTER])],
    )
    # A fragment: compatible with this printer, and not a preset anyone can pick.
    (profiles / "BBL" / "process" / "template.json").write_text(
        json.dumps({"compatible_printers": [PRINTER]}), encoding="utf-8"
    )
    machine = profiles / "BBL" / "machine" / f"{PRINTER}.json"
    assert slicing.profiles_for(machine)[0].stem != "template"


# --- complete profiles for the CLI -------------------------------------------


def test_inherited_profiles_are_flattened_base_to_leaf(tmp_path):
    profiles = vendor(tmp_path)
    folder = profiles / "BBL" / "filament"
    (folder / "fdm_filament_pla.json").write_text(
        json.dumps({"name": "fdm_filament_pla", "filament_type": ["PLA"], "temperature": ["220"]})
    )
    (folder / "Bambu PLA Basic @base.json").write_text(
        json.dumps({"name": "Bambu PLA Basic @base", "inherits": "fdm_filament_pla", "temperature": ["225"]})
    )
    leaf = folder / "Bambu PLA Basic @BBL A1M.json"
    leaf.write_text(
        json.dumps({"name": leaf.stem, "inherits": "Bambu PLA Basic @base", "hot_plate_temp": ["60"]})
    )
    full = slicing._flatten(leaf)
    assert full["filament_type"] == ["PLA"]
    assert full["temperature"] == ["225"]
    assert full["hot_plate_temp"] == ["60"]
    assert "inherits" not in full


def test_a_parent_can_live_in_the_global_filament_library(tmp_path):
    profiles = vendor(tmp_path)
    library = profiles / "OrcaFilamentLibrary" / "filament"
    library.mkdir(parents=True)
    (library / "Generic PLA @System.json").write_text(
        json.dumps({"name": "Generic PLA @System", "filament_type": ["PLA"]})
    )
    leaf = profiles / "BBL" / "filament" / "Generic PLA @BBL.json"
    leaf.write_text(json.dumps({"name": leaf.stem, "inherits": "Generic PLA @System"}))
    assert slicing._flatten(leaf)["filament_type"] == ["PLA"]


def test_split_out_template_fields_are_part_of_the_full_profile(tmp_path):
    profiles = vendor(tmp_path)
    leaf = profiles / "BBL" / "machine" / f"{PRINTER}.json"
    template = leaf.with_name(f"{leaf.stem} template machine_start_gcode.json")
    template.write_text(
        json.dumps(
            {
                "name": f"{leaf.stem} template machine_start_gcode",
                "instantiation": "false",
                "machine_start_gcode": "M109 S[nozzle_temperature_initial_layer]",
            }
        )
    )
    full = slicing._flatten(leaf)
    assert full["name"] == PRINTER
    assert full["instantiation"] == "true"
    assert full["machine_start_gcode"] == "M109 S[nozzle_temperature_initial_layer]"


def test_run_hands_the_slicer_complete_profiles(tmp_path, monkeypatch):
    profiles = vendor(
        tmp_path,
        processes=[("0.20mm Standard @BBL A1M", [PRINTER])],
        filaments=[("Bambu PLA Basic @BBL A1M", [PRINTER])],
    )
    machine = profiles / "BBL" / "machine" / f"{PRINTER}.json"
    machine.write_text(
        json.dumps(
            {
                "name": PRINTER,
                "instantiation": "true",
                "inherits": "machine base",
            }
        )
    )
    (machine.parent / "machine base.json").write_text(
        json.dumps({"name": "machine base", "printable_height": "180"})
    )
    (machine.parent / f"{PRINTER} template machine_start_gcode.json").write_text(
        json.dumps({"name": "template", "machine_start_gcode": "M109 S[first_layer]"})
    )
    process, filament = slicing.profiles_for(machine)
    process.write_text(
        json.dumps(
            {
                "name": process.stem,
                "instantiation": "true",
                "compatible_printers": [PRINTER],
                "inherits": "process base",
            }
        )
    )
    (process.parent / "process base.json").write_text(
        json.dumps({"name": "process base", "layer_height": "0.2"})
    )
    filament.write_text(
        json.dumps(
            {
                "name": filament.stem,
                "instantiation": "true",
                "compatible_printers": [PRINTER],
                "inherits": "filament base",
            }
        )
    )
    (filament.parent / "filament base.json").write_text(
        json.dumps({"name": "filament base", "filament_type": ["PLA"]})
    )

    def sliced(command, **kwargs):
        machine_file, process_file = map(
            pathlib.Path, command[command.index("--load-settings") + 1].split(";")
        )
        filament_file = pathlib.Path(command[command.index("--load-filaments") + 1])
        assert json.loads(machine_file.read_text())["printable_height"] == "180"
        assert json.loads(machine_file.read_text())["machine_start_gcode"] == "M109 S[first_layer]"
        assert json.loads(process_file.read_text())["layer_height"] == "0.2"
        assert json.loads(filament_file.read_text())["filament_type"] == ["PLA"]
        assert command[command.index("--curr-bed-type") + 1] == "Textured PEI Plate"
        out = pathlib.Path(command[command.index("--outputdir") + 1])
        (out / "plate_1.gcode").write_text(
            "; total estimated time: 12m\n; total filament weight [g] : 1.5\n"
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(slicing.subprocess, "run", sliced)
    model = tmp_path / "thing.stl"
    model.write_text("solid thing\nendsolid thing\n")
    predicted, target = slicing.run(
        model,
        tmp_path / "thing.gcode",
        machine,
        process,
        filament,
        exe=tmp_path / "slicer",
    )
    assert predicted == (720, 1.5)
    assert target.is_file()


def test_a_failed_slice_removes_the_previous_gcode(tmp_path, monkeypatch):
    profiles = vendor(
        tmp_path,
        processes=[("0.20mm Standard @BBL A1M", [PRINTER])],
        filaments=[("Bambu PLA Basic @BBL A1M", [PRINTER])],
    )
    machine = profiles / "BBL" / "machine" / f"{PRINTER}.json"
    process, filament = slicing.profiles_for(machine)
    model = tmp_path / "thing.stl"
    model.write_text("solid thing\nendsolid thing\n")
    target = tmp_path / "thing.gcode"
    target.write_text("yesterday's print")
    monkeypatch.setattr(
        slicing.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="bad model"),
    )
    with pytest.raises(slicing.Unavailable):
        slicing.run(model, target, machine, process, filament, exe=tmp_path / "slicer")
    assert not target.exists()


# --- reading back what it predicted -------------------------------------------


def test_time_comes_from_the_structured_file(tmp_path):
    (tmp_path / "result.json").write_text(json.dumps({"sliced_plates": [{"total_predication": 1668.9}]}))
    (tmp_path / "plate_1.gcode").write_text(
        "; total filament length [mm] : 1016.96\n; total filament weight [g] : 3.08\n"
    )
    seconds, grams = slicing._predicted(tmp_path)
    assert seconds == pytest.approx(1668.9)
    assert grams == pytest.approx(3.08)


def test_the_gcode_footer_answers_when_the_structured_file_does_not(tmp_path):
    """The totals are written as a footer, so reading only the head would miss them."""
    body = "G1 X1 Y1\n" * 4000
    (tmp_path / "plate_1.gcode").write_text(
        f"; generated\n{body}; total estimated time: 1h 4m 12s\n"
        "; total filament length [mm] : 900.5\n; total filament weight [g] : 2.73\n"
    )
    seconds, grams = slicing._predicted(tmp_path)
    assert seconds == 3852
    assert grams == pytest.approx(2.73)


def test_a_number_that_is_not_there_stays_none(tmp_path):
    """A slicer that changes how it reports is a reason to say less, not to invent."""
    (tmp_path / "plate_1.gcode").write_text("; nothing useful here\n")
    assert slicing._predicted(tmp_path) == (None, None)


@pytest.mark.parametrize(
    "seconds,said", [(None, "unknown"), (0, "unknown"), (90, "1m"), (1668, "27m"), (3852, "1h 04m")]
)
def test_a_duration_reads_at_a_glance(seconds, said):
    assert slicing.spoken(seconds) == said


# --- the machine name lives with the machine ----------------------------------


def test_every_shipped_profile_names_itself_for_a_slicer():
    """A profile with no slicer name is one `nurb slice` would refuse for no reason."""
    for name, facts in checks.profiles().items():
        assert facts.get("slicer"), f"{name} has no slicer name"


def test_the_slicer_name_never_reaches_the_check_settings(tmp_path):
    """Every other key in a profile is a Context field, and this one is not."""
    ctx = checks.printer(tmp_path, "bambu_a1_mini")
    assert ctx.bed == (180.0, 180.0, 180.0)
    assert not hasattr(ctx, "slicer")


def test_the_project_s_own_choice_is_what_gets_sliced(tmp_path):
    (tmp_path / "printer.toml").write_text('profile = "bambu_a1_mini"\n', encoding="utf-8")
    assert checks.slicer_name(tmp_path) == ("Bambu Lab A1 mini", "bambu_a1_mini")


def test_no_chosen_printer_is_a_question_not_a_default(tmp_path, monkeypatch):
    monkeypatch.setattr(checks, "global_file", lambda: tmp_path / "absent.toml")
    assert checks.slicer_name(tmp_path) == (None, None)


def test_an_unknown_profile_name_lists_the_real_ones(tmp_path):
    with pytest.raises(ValueError, match="bambu_a1_mini"):
        checks.slicer_name(tmp_path, "bambu_a2_maxi")


# --- finding the slicer -------------------------------------------------------


def test_no_slicer_installed_is_none_not_a_crash():
    assert slicing.app(search=("NoSuchSlicerExistsHere",)) is None


@pytest.mark.skipif(sys.platform == "win32", reason="which() needs a PATHEXT extension on Windows")
def test_a_hyphenated_linux_command_and_share_tree_are_found(tmp_path, monkeypatch):
    exe = tmp_path / "usr" / "bin" / "orca-slicer"
    exe.parent.mkdir(parents=True)
    exe.write_text("#!/bin/sh\n")
    exe.chmod(0o755)
    profiles = tmp_path / "usr" / "share" / "OrcaSlicer" / "profiles"
    profiles.mkdir(parents=True)
    monkeypatch.setenv("PATH", str(exe.parent))
    found = slicing.app(search=("OrcaSlicer",))
    assert found == exe
    assert slicing.vendors(found) == profiles


@pytest.mark.skipif(sys.platform != "win32", reason="Program Files discovery is Windows-only")
def test_a_program_files_install_and_resources_tree_are_found(tmp_path, monkeypatch):
    exe = tmp_path / "Program Files" / "OrcaSlicer" / "orca-slicer.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    profiles = exe.parent / "resources" / "profiles"
    profiles.mkdir(parents=True)
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "Program Files"))
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    found = slicing.app(search=("OrcaSlicer",))
    assert found == exe
    assert slicing.vendors(found) == profiles


@pytest.mark.skipif(sys.platform != "win32", reason="the spaced folder is the Bambu installer's")
def test_bambu_studios_spaced_install_folder_is_found(tmp_path, monkeypatch):
    exe = tmp_path / "Program Files" / "Bambu Studio" / "bambu-studio.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "Program Files"))
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert slicing.app(search=("BambuStudio",)) == exe


def test_a_print_over_a_day_keeps_its_days():
    """Dropping the unit would not fail, it would report 28 hours as four."""
    assert slicing._clock("1d 4h 20m 12s") == 102_012
    assert slicing.spoken(102_012) == "1d 4h 20m"


def test_a_unit_this_parser_does_not_know_answers_nothing():
    """The module's rule: a slicer reporting differently says less, never invents."""
    assert slicing._clock("2w 3h") is None


# --- what it weighs ------------------------------------------------------------
# Grams, because a spool is a kilogram and a length of filament is a number nobody has
# ever decided anything from. The weight line is the slicer's own answer where it has
# one; the arithmetic exists for the profile whose density never resolved and wrote 0,
# which used to be the whole reason this reported millimetres instead.


def test_a_zero_weight_falls_through_to_the_arithmetic(tmp_path):
    (tmp_path / "plate_1.gcode").write_text(
        "; total filament weight [g] : 0\n"
        "; total filament length [mm] : 47949.45\n"
        "; filament_density: 1.26\n; filament_diameter: 1.75\n"
    )
    assert slicing._predicted(tmp_path)[1] == pytest.approx(145.32, abs=0.01)


def test_the_computed_weight_agrees_with_the_slicers_own(tmp_path):
    """Same header, both routes: a cylinder of filament is the whole calculation, so
    the fallback cannot quietly disagree with the figure it stands in for."""
    parts = (
        "; total filament length [mm] : 47949.45\n"
        "; filament_density: 1.26\n; filament_diameter: 1.75\n"
    )
    (tmp_path / "plate_1.gcode").write_text(parts + "; total filament weight [g] : 145.32\n")
    theirs = slicing._predicted(tmp_path)[1]
    (tmp_path / "plate_1.gcode").write_text(parts)
    assert slicing._predicted(tmp_path)[1] == pytest.approx(theirs, abs=0.01)


def test_a_header_with_nothing_to_weigh_says_nothing(tmp_path):
    (tmp_path / "plate_1.gcode").write_text("; total estimated time: 12m\n")
    assert slicing._predicted(tmp_path)[1] is None


def test_a_weight_reads_against_a_spool_not_a_micrometer():
    assert slicing.weighed(145.32) == "145g"
    assert slicing.weighed(2.34) == "2.3g"  # a fit coupon must not round to nothing
    assert slicing.weighed(None) == "unknown"


# --- the settings a part justifies ----------------------------------------------
# The one exception to leaving settings to the slicer, drawn on a line: what follows
# from the geometry nurb built is nurb's knowledge, flow and temperature are not.


def test_every_part_gets_the_functional_defaults():
    from build123d import Box

    settings, notes = slicing.tuned(Box(20, 20, 10))
    assert settings["sparse_infill_pattern"] == "gyroid"
    assert settings["sparse_infill_density"] == "10%"
    assert settings["wall_loops"] == "3"
    assert "brim_type" not in settings  # a well-footed part keeps the profile's own
    assert notes == ["gyroid 10%", "3 walls"]


def test_a_part_that_earns_a_warp_finding_earns_a_brim():
    from build123d import Box

    settings, notes = slicing.tuned(Box(200, 200, 2))
    assert settings["brim_type"] == "outer_only"
    assert any("corners lift" in note for note in notes)


def test_the_overrides_land_in_the_process_profile_alone(tmp_path):
    profiles = vendor(
        tmp_path,
        processes=(("0.20mm Standard @BBL A1M", ["Bambu Lab A1 mini 0.4 nozzle"]),),
        filaments=(("Bambu PLA Basic @BBL A1M", ["Bambu Lab A1 mini 0.4 nozzle"]),),
    )
    machine = profiles / "BBL" / "machine" / "Bambu Lab A1 mini 0.4 nozzle.json"
    process = profiles / "BBL" / "process" / "0.20mm Standard @BBL A1M.json"
    filament = profiles / "BBL" / "filament" / "Bambu PLA Basic @BBL A1M.json"
    out = tmp_path / "out"
    out.mkdir()
    slicing._preset_args(out, machine, process, filament, settings={"sparse_infill_pattern": "gyroid"})
    assert json.loads((out / "process.json").read_text())["sparse_infill_pattern"] == "gyroid"
    assert "sparse_infill_pattern" not in json.loads((out / "machine.json").read_text())
    assert "sparse_infill_pattern" not in json.loads((out / "filament.json").read_text())


def test_the_kit_says_what_a_bare_3mf_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(slicing, "app", lambda search=None: None)
    kit, why = slicing.kit(tmp_path)
    assert kit is None and "no slicer" in why

    monkeypatch.setattr(slicing, "app", lambda search=None: tmp_path / "slicer")
    kit, why = slicing.kit(tmp_path)  # a slicer but no printer named anywhere
    assert kit is None and "no printer" in why


def test_supports_reach_the_slicer_only_when_the_part_declares_them():
    """Declared, not derived: no amount of looking at a solid says whether its owner
    is willing to cut support material off it."""
    from build123d import Box

    from nurb import checks

    plain, notes = slicing.tuned(Box(20, 20, 10))
    assert "enable_support" not in plain
    assert "supports" not in notes

    carried, notes = slicing.tuned(Box(20, 20, 10), checks.Context(supports=True))
    assert carried["enable_support"] == "1"
    assert "supports" in notes


def test_a_supported_mark_turns_the_slicer_on_by_itself():
    """The mark is the declaration too, so a part that never touches its card still
    exports a 3MF that will actually print."""
    from build123d import Box, Pos

    from nurb import supports

    with supports.collecting() as marked:
        shape = Box(60, 20, 30) - Pos(0, 0, -5) * Box(44, 20, 16)
        supports.supported(Pos(0, 0, -5) * Box(44, 20, 16), "the bundle sets this span")
    shape._nurb_supported = tuple(marked)

    settings, notes = slicing.tuned(shape)
    assert settings["enable_support"] == "1"
    assert "supports" in notes


def test_tuned_still_answers_without_a_context():
    """`tuned` defaults its own ctx: `checks.run` does that internally, but the
    declaration is read here, before it gets there."""
    from build123d import Box

    settings, _ = slicing.tuned(Box(20, 20, 10))
    assert "enable_support" not in settings
