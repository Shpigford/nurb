"""A mesh becomes a part's solid only where that is honest.

build123d's `import_stl` returns a `Face`, and subtracting from one segfaults instead
of raising. A part builds inside the `nurb dev` process, so the whole watcher dies with
no traceback: the one failure here that leaves no evidence. These tests pin both halves.
The flat-faced case comes back as a real solid that chamfers, and every other mesh is
refused in words that name what to run instead. Three of those refusals exist because
the mesh converts perfectly well and the result is silently wrong: an open surface gets
a volume, an inverted one runs its booleans backwards, a degenerate one encloses
nothing.
"""

import shlex

import pytest
import trimesh
from build123d import Box, Cylinder, Location, Mesher, Solid, export_stl, fillet

from nurb import chamfer, import_stl, mesh, polish, scan


def written(tmp_path, shape, name="part.stl"):
    target = tmp_path / name
    export_stl(shape, str(target))
    return target


def test_a_box_comes_back_as_a_box(tmp_path):
    """Six faces, not twelve triangles, and the size it went in at."""
    recovered = import_stl(written(tmp_path, Box(20, 30, 40)))
    assert isinstance(recovered, Solid)
    assert len(recovered.faces()) == 6
    assert recovered.volume == pytest.approx(24_000.0)
    size = recovered.bounding_box().size
    assert (size.X, size.Y, size.Z) == pytest.approx((20.0, 30.0, 40.0))


def test_an_uppercase_stl_extension_imports(tmp_path):
    """Lib3MF's extension dispatch is case-sensitive; the file format is not."""
    recovered = import_stl(written(tmp_path, Box(20, 30, 40), "BOX.STL"))
    assert recovered.is_valid
    assert recovered.volume == pytest.approx(24_000.0)


def test_the_recovered_box_chamfers_like_one_that_was_modelled(tmp_path):
    """The point of the `clean` pass, and the reason it is not optional.

    Without it the solid is twelve triangles, so a chamfer of "every edge" also
    chamfers the six diagonal seams the triangulation invented, and lands 44 faces
    where 26 is right. That result builds and looks plausible, which is what makes
    skipping the clean a silent wrong answer rather than an error.
    """
    recovered = import_stl(written(tmp_path, Box(20, 30, 40)))
    # 6 faces + 12 edge chamfers + 8 corner triangles.
    assert len(chamfer(recovered.edges(), 2.0).faces()) == 26


def test_a_flat_faced_part_keeps_every_face(tmp_path):
    bracket = Box(40, 40, 4) + Box(40, 4, 40)
    recovered = import_stl(written(tmp_path, bracket))
    assert len(recovered.faces()) == len(bracket.faces()) == 14


def test_an_open_surface_is_refused_rather_than_solidified(tmp_path):
    """OCCT builds a solid from a mesh with holes and reports a volume for it."""
    sheet = trimesh.Trimesh(
        vertices=[(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)],
        faces=[(0, 1, 2), (0, 2, 3)],
    )
    target = tmp_path / "sheet.stl"
    sheet.export(target)
    with pytest.raises(ValueError, match="not closed"):
        import_stl(target)


def test_multiple_shells_are_refused_when_the_kernel_result_is_invalid(tmp_path):
    """Positive volume is not enough to make Lib3MF's multi-shell Solid valid."""
    target = tmp_path / "two-bodies.stl"
    left = trimesh.creation.box(extents=(10, 10, 10))
    right = trimesh.creation.box(
        extents=(10, 10, 10),
        transform=trimesh.transformations.translation_matrix((30, 0, 0)),
    )
    trimesh.util.concatenate([left, right]).export(target)
    raw = Mesher().read(str(target))[0].clean()
    assert raw.volume > 0 and not raw.is_valid
    with pytest.raises(ValueError, match="valid body"):
        import_stl(target)


def test_a_dense_mesh_is_refused_even_when_it_is_closed(tmp_path):
    """Closure is not enough on its own: the conversion cost is the other half.

    Watertight and organic is exactly the shape that would convert, slowly, and hand
    back a facet soup. 5,120 triangles is a second; the download that started this was
    225,706 and took 111s to read plus 51s for one boolean.
    """
    target = tmp_path / "blob.stl"
    trimesh.creation.icosphere(subdivisions=4, radius=30).export(target)
    loaded, _, _ = scan.load(target)
    assert loaded.is_watertight and len(loaded.faces) > mesh.TRIANGLE_CEILING
    with pytest.raises(ValueError, match="triangles, over the"):
        import_stl(target)


def test_a_refusal_names_the_command_that_does_work(tmp_path):
    """An error that only says no leaves the agent to guess, and it guesses badly."""
    target = written(tmp_path, fillet(Box(20, 30, 40).edges(), 3), "downloaded.stl")
    with pytest.raises(ValueError) as exc:
        import_stl(target)
    command = shlex.join(("nurb", "scan", str(target)))
    assert f"`{command}`" in str(exc.value)


def test_the_ceiling_is_far_above_the_geometry_that_survives(tmp_path):
    """The gate must not fire on the case it exists to serve."""
    plate = Box(60, 60, 4) - [
        Box(6, 6, 10).locate(Location((x, y, 0))) for x in (-20, 20) for y in (-20, 20)
    ]
    loaded, _, _ = scan.load(written(tmp_path, plate))
    triangles = len(loaded.faces)
    assert loaded.is_watertight and triangles * 10 < mesh.TRIANGLE_CEILING
    assert mesh.refusal(".stl", loaded) is None


def test_the_import_is_the_size_the_scan_reported(tmp_path):
    """The two commands read one file, so they cannot disagree about how big it is.

    An STL carries no unit and scan apps export metres, so importing raw is a part
    1,000x too small that builds, checks clean and prints. `nurb scan` already owned
    that guess; reading through it is what keeps the reported size and the imported
    size the same number.
    """
    target = tmp_path / "small.stl"
    trimesh.creation.box(extents=(0.02, 0.03, 0.04)).export(target)
    loaded, unit, _ = scan.load(target)
    assert unit == "m"
    assert loaded.extents.max() == pytest.approx(40.0)
    size = import_stl(target).bounding_box().size
    assert (size.X, size.Y, size.Z) == pytest.approx((20.0, 30.0, 40.0))


def test_units_overrides_the_guess_the_way_the_flag_does(tmp_path):
    """`nurb scan --units` has to have a counterpart, or the escape hatch stops here."""
    size = import_stl(written(tmp_path, Box(20, 30, 40)), units="cm").bounding_box().size
    assert (size.X, size.Y, size.Z) == pytest.approx((200.0, 300.0, 400.0))


def test_a_closed_mesh_the_kernel_cannot_solidify_is_refused(tmp_path):
    """Zero-area triangles are closed, enclose nothing, and OCCT will not say so.

    Left to the kernel this is "Null TopoDS_Shape object", so the signed volume is
    what catches it: NaN here, which is also why `refusal` silences numpy first.
    """
    degenerate = trimesh.Trimesh(
        vertices=[(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)],
        faces=[(0, 1, 2), (1, 2, 3), (0, 1, 3), (0, 2, 3)],
    )
    target = tmp_path / "degenerate.stl"
    degenerate.export(target)
    assert degenerate.is_watertight  # the guard before this one lets it through
    with pytest.raises(ValueError, match="triangles enclose nothing"):
        import_stl(target)


def test_an_inside_out_mesh_is_refused_rather_than_inverted_silently(tmp_path):
    """The worst of them, because nothing downstream objects.

    A closed mesh wound inward is watertight and converts, with negative volume. Cutting
    a hole in one adds material instead of removing it, and the part builds, checks and
    exports without a word.
    """
    inverted = trimesh.creation.box(extents=(20, 30, 40))
    inverted.invert()
    target = tmp_path / "inverted.stl"
    inverted.export(target)
    assert inverted.is_watertight
    with pytest.raises(ValueError, match="inside out"):
        import_stl(target)


def test_a_curve_survives_as_facets_and_loses_its_selectors(tmp_path):
    """Accepted is not the same as faithful, which is why the skill says rebuild.

    A cylinder converts, and every way of asking for its round face fails: the rim a
    part would chamfer is 126 straight segments, so the selector finds nothing.
    """
    recovered = import_stl(written(tmp_path, Cylinder(10, 30)))
    assert recovered.volume == pytest.approx(Cylinder(10, 30).volume, rel=0.01)
    assert len(recovered.faces()) > 100
    assert not [f for f in recovered.faces() if f.geom_type.name == "CYLINDER"]
    assert not recovered.edges().filter_by(lambda e: e.geom_type.name == "CIRCLE")


def test_a_part_can_import_and_then_polish(tmp_path):
    """End to end, because the segfault only ever showed up past the import."""
    body = import_stl(written(tmp_path, Box(20, 30, 40)))
    cut = body - Cylinder(3, 200)
    assert polish(cut, cut.edges(), 1.0).volume < cut.volume


def test_a_format_that_measures_but_cannot_convert_says_which(tmp_path):
    """`nurb scan` reads more formats than lib3mf converts, and the gap misleads.

    Left to the kernel, a PLY fails with "Null TopoDS_Shape object", which this would
    report as degenerate triangles: a true-sounding diagnosis of the wrong problem,
    aimed at a file that is perfectly good.
    """
    box = trimesh.creation.box(extents=(20, 30, 40))
    for suffix in (".ply", ".obj", ".glb"):
        target = tmp_path / f"scan{suffix}"
        box.export(target)
        with pytest.raises(ValueError, match=f"is a {suffix}, and only"):
            import_stl(target)


def test_3mf_writes_a_mesh_whose_weld_collapses_a_triangle(tmp_path, monkeypatch):
    """Welding shared vertices can leave a triangle with two corners the same.

    lib3mf's SetGeometry rejects that as "invalid parameter" and the viewer's
    3mf button dies with ELib3MFException. Drop the collapsed triangle and write
    the rest; the STL has always carried the same holes.
    """
    import zipfile

    from nurb import builder

    mesh = trimesh.Trimesh(
        vertices=[[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0]],
        faces=[[0, 1, 2], [0, 1, 3]],
        process=False,
    )
    monkeypatch.setattr(builder, "to_mesh", lambda *a, **k: mesh)

    target = tmp_path / "collapsed.3mf"
    builder.write_3mf(Box(20, 30, 40), target)

    with zipfile.ZipFile(target) as z:
        model = z.read("3D/3dmodel.model").decode()
    assert 'unit="millimeter"' in model
    assert model.count("<triangle ") == 1


def test_3mf_says_what_to_do_instead_of_naming_a_missing_module(tmp_path):
    """The other half of a model site download, and trimesh cannot read it here.

    Without this the error is "part.3mf: No module named 'networkx'", which names an
    implementation detail at the exact moment a first-time user is deciding whether
    this tool works. Exporting STL from the slicer they already have is one menu item.
    """
    target = tmp_path / "part.3mf"
    mesher = Mesher()
    mesher.add_shape(Box(20, 30, 40))
    mesher.write(str(target))
    for call in (lambda: import_stl(target), lambda: scan.load(target)):
        with pytest.raises(ValueError, match="export the plate as STL"):
            call()


def test_the_scan_report_and_the_import_agree_about_every_file(tmp_path):
    """One shared conversion path, so the report cannot promise what the import refuses.

    The property, not the cases: every reason `import_stl` says no has to be a reason
    the report already knew, or `nurb scan` sends the agent at a call that fails. This
    is the test that catches the next reason someone adds in only one of the two.
    """
    inverted = trimesh.creation.box(extents=(20, 30, 40))
    inverted.invert()
    cases = {
        "good.stl": trimesh.creation.box(extents=(20, 30, 40)),
        "dense.stl": trimesh.creation.icosphere(subdivisions=4, radius=30),
        "open.stl": trimesh.Trimesh(
            vertices=[(0, 0, 0), (10, 0, 0), (10, 10, 0)], faces=[(0, 1, 2)]
        ),
        "inverted.stl": inverted,
        "degenerate.stl": trimesh.Trimesh(
            vertices=[(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)],
            faces=[(0, 1, 2), (1, 2, 3), (0, 1, 3), (0, 2, 3)],
        ),
        "wrongformat.ply": trimesh.creation.box(extents=(20, 30, 40)),
        "wrongformat.obj": trimesh.creation.box(extents=(20, 30, 40)),
        "overlap.stl": trimesh.util.concatenate(
            [
                trimesh.creation.box(extents=(20, 20, 20)),
                trimesh.creation.box(
                    extents=(20, 20, 20),
                    transform=trimesh.transformations.translation_matrix((10, 0, 0)),
                ),
            ]
        ),
    }
    for name, geometry in cases.items():
        target = tmp_path / name
        geometry.export(target)
        loaded, unit, source = scan.load(target)
        promised = "import_stl(" in scan.report(target, loaded, unit, source)[-1]
        try:
            import_stl(target)
            works = True
        except ValueError:
            works = False
        assert promised == works, name
    # Agreement is cheap if nothing passes: one case has to actually come through.
    assert import_stl(tmp_path / "good.stl").volume == pytest.approx(24_000.0)


def test_a_missing_file_is_a_clean_error(tmp_path):
    with pytest.raises(ValueError, match="no file"):
        import_stl(tmp_path / "absent.stl")
