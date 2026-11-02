"""The slicer handoff, against a profile tree built here rather than an installed app.

Nothing in CI has a slicer, and a test that skips when one is missing is a test that
never runs. So the vendor bundle is faked at its real shape and everything except the
subprocess itself is exercised: the profile picks, the refusals, and reading back the
two numbers from the files a slicer leaves behind.
"""

import json
import os
import pathlib
from types import SimpleNamespace

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


def _fake_slicer(root, name, machines):
    """An unpacked-AppImage layout: the executable beside resources/profiles."""
    exe = root / name / name
    exe.parent.mkdir(parents=True)
    exe.write_text("#!/bin/sh\n")
    exe.chmod(0o755)
    folder = root / name / "resources" / "profiles" / "Vendor" / "machine"
    folder.mkdir(parents=True)
    for machine in machines:
        (folder / f"{machine} 0.4 nozzle.json").write_text("{}")
    return exe


def test_the_slicer_that_carries_the_printer_wins(tmp_path, monkeypatch):
    """Bambu Studio ships two Prusas, so finding it first must not fail an MK4S that
    the other installed slicer can slice (#263)."""
    first = _fake_slicer(tmp_path, "SlicerA", ["Prusa MINI"])
    second = _fake_slicer(tmp_path, "SlicerB", ["Prusa MINI", "Prusa MK4S"])
    monkeypatch.setenv("PATH", f"{first.parent}{os.pathsep}{second.parent}")
    search = ("SlicerA", "SlicerB")
    assert slicing.app(search=search, printer="Prusa MK4S") == second
    assert slicing.app(search=search, printer="Prusa MINI") == first
    # Nobody carries it: the first one, so its error names the missing machine.
    assert slicing.app(search=search, printer="Voron 2.4") == first


def test_a_prusa_opens_in_prusaslicer_and_everything_else_in_the_slicer_that_has_it(monkeypatch):
    bambu = pathlib.Path("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
    prusa = pathlib.Path("/Applications/PrusaSlicer.app")
    monkeypatch.setattr(slicing, "installed", lambda: [("BambuStudio", bambu), ("PrusaSlicer", prusa)])
    monkeypatch.setattr(slicing, "app", lambda search=None, printer=None: bambu)
    assert slicing.opener("Prusa MK4S", "Prusa") == ("PrusaSlicer", prusa)
    assert slicing.opener("Bambu Lab X1 Carbon", "Bambu Lab") == ("BambuStudio", bambu)
    # PrusaSlicer alone still opens a Bambu part: it is the slicer that is here.
    monkeypatch.setattr(slicing, "installed", lambda: [("PrusaSlicer", prusa)])
    monkeypatch.setattr(slicing, "app", lambda search=None, printer=None: None)
    assert slicing.opener("Bambu Lab X1 Carbon", "Bambu Lab") == ("PrusaSlicer", prusa)
    monkeypatch.setattr(slicing, "installed", lambda: [])
    assert slicing.opener("Prusa MK4S", "Prusa") is None


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


def test_a_bambu_machine_weighs_by_the_per_extruder_block(tmp_path):
    # Orca writes no total weight line for a Bambu machine; the per-extruder block is
    # the only gram figure in the file, and it is summed because a second extruder can
    # be a real number.
    (tmp_path / "plate_1.gcode").write_text("; filament used [g] = 3.08, 0.50\n; total estimated time: 12m\n")
    assert slicing._predicted(tmp_path) == (720, pytest.approx(3.58))


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
    monkeypatch.setattr(slicing, "app", lambda search=None, printer=None: None)
    kit, why = slicing.kit(tmp_path)
    assert kit is None and "no slicer" in why

    monkeypatch.setattr(slicing, "app", lambda search=None, printer=None: tmp_path / "slicer")
    kit, why = slicing.kit(tmp_path)  # a slicer but no printer named anywhere
    assert kit is None and "no printer" in why


def test_the_kit_reason_is_one_line(tmp_path, monkeypatch):
    """A missing machine explains itself over several lines; the kit keeps the first (#301)."""
    (tmp_path / "printer.toml").write_text('profile = "prusa_mk4s"\n')
    monkeypatch.setattr(slicing, "app", lambda search=None, printer=None: tmp_path / "slicer")
    monkeypatch.setattr(slicing, "vendors", lambda exe: tmp_path)

    def missing(bundle, name):
        raise slicing.Unavailable(f"this slicer has no profile for {name!r}.\n  It has: others.")

    monkeypatch.setattr(slicing, "machine", missing)
    kit, why = slicing.kit(tmp_path)
    assert kit is None
    assert why == "this slicer has no profile for 'Prusa MK4S'."


# --- PrusaSlicer ---------------------------------------------------------------
# One INI holds Prusa's whole bundle, and a preset inherits from a list of parents.

PRUSA_INI = """
[printer_model:MK4S]
default_materials = Prusament PLA @MK4S HF0.4; Generic PLA @MK4S HF0.4; Generic PETG @MK4S HF0.4

[printer:*common*]
binary_gcode = 1
nozzle_diameter = 0.6
default_print_profile = 0.15mm QUALITY @MK4S 0.4

[printer:*mk4s*]
printer_model = MK4S
nozzle_diameter = 0.5

[printer:Original Prusa MK4S 0.4 nozzle]
inherits = *common*; *mk4s*
nozzle_diameter = 0.4
default_filament_profile = "Prusament PLA @MK4S"

[print:0.15mm QUALITY @MK4S 0.4]
layer_height = 0.15

[print:0.20mm QUALITY @MK4S 0.4]
layer_height = 0.2

[filament:Generic PLA @MK4S]
filament_type = PLA

[filament:Generic PETG @MK4S HF0.4]
filament_type = PETG
"""


def _fake_prusa(tmp_path, footer):
    """A PrusaSlicer bundle whose executable writes a G-code ending in `footer`."""
    exe = tmp_path / "PrusaSlicer.app" / "Contents" / "MacOS" / "PrusaSlicer"
    exe.parent.mkdir(parents=True)
    exe.write_text(
        "#!/bin/sh\n"
        'while [ "$1" != "--output" ]; do shift; done\n'
        f"printf '; estimated printing time (normal mode) = 1h 2m 3s\\n; filament used [g] = 8.92\\n%s' > \"$2\"\n"
        % footer
    )
    exe.chmod(0o755)
    profiles = tmp_path / "PrusaSlicer.app" / "Contents" / "Resources" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "PrusaResearch.ini").write_text(PRUSA_INI)
    return exe


def test_prusa_parents_apply_left_to_right_and_the_preset_wins(tmp_path):
    exe = _fake_prusa(tmp_path, "")
    (_, printer), (process, _), (material, _) = slicing.prusa_presets(exe, "Original Prusa MK4S 0.4 nozzle")
    assert printer["nozzle_diameter"] == "0.4" and printer["printer_model"] == "MK4S"
    # The default print at the asked layer, and the generic filament for this nozzle,
    # not the HF one the model's material list happens to name first.
    assert process == "0.20mm QUALITY @MK4S 0.4"
    assert material == "Generic PLA @MK4S"
    # PETG has no generic for this nozzle, so the model's own list answers.
    *_, (petg, _) = slicing.prusa_presets(exe, "Original Prusa MK4S 0.4 nozzle", filament="PETG")
    assert petg == "Generic PETG @MK4S HF0.4"
    with pytest.raises(slicing.Unavailable, match="no printer profile 'Original Prusa XL'"):
        slicing.prusa_presets(exe, "Original Prusa XL")


def test_prusa_totals_are_read_past_the_config_dump(tmp_path):
    """PrusaSlicer prints its totals and then several thousand config lines."""
    exe = _fake_prusa(tmp_path, "; some_setting = 1\\n" * 3000)
    presets = slicing.prusa_presets(exe, "Original Prusa MK4S 0.4 nozzle")
    model = tmp_path / "part.stl"
    model.write_text("solid part\nendsolid part\n")
    (seconds, grams), out = slicing.prusa_run(model, tmp_path / "part.gcode", exe, presets)
    assert (seconds, grams) == (3723, 8.92)
    assert out.is_file() and not (tmp_path / ".part.slicing").exists()
