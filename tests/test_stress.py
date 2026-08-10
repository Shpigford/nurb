"""The stress solver: physics first, then the part-facing surface.

The cantilever is the calibration: a beam with a textbook answer, solved on the same
voxel path a real part takes. If that number drifts, everything downstream is noise.
"""

import numpy as np
import pytest
from build123d import Box, Pos

from nurb import stress


def test_cantilever_matches_beam_theory():
    # 100x10x10mm PLA cantilever, 10 N at the tip. Timoshenko: bending plus shear.
    L, w, t, P = 100.0, 10.0, 10.0, 10.0
    I = w * t**3 / 12
    G = stress.E_PLA / (2 * (1 + stress.NU))
    expected = P * L**3 / (3 * stress.E_PLA * I) + P * L / (5 / 6 * w * t * G)

    pitch = 1.25
    filled = np.ones((round(L / pitch), round(w / pitch), round(t / pitch)), bool)
    model = stress._Voxels(filled, pitch, (0, 0, 0))
    fixed = np.where(model.node_xyz[:, 0] < 1e-9)[0]
    tip = np.where(model.node_xyz[:, 0] > L - 1e-9)[0]
    u = model.solve(fixed, tip, (0, 0, -P))
    deflection = -u[tip * 3 + 2].mean()
    assert deflection == pytest.approx(expected, rel=0.05)


def test_load_shared_with_fixed_nodes_is_redistributed_to_the_free_face():
    model = stress._Voxels(np.ones((2, 1, 1), bool), 1.0, (0, 0, 0))
    fixed = np.where(model.node_xyz[:, 0] == 0)[0]
    tip = np.where(model.node_xyz[:, 0] == 2)[0]

    expected = model.solve(fixed, tip, (0, 0, -10))
    shared = model.solve(fixed, np.concatenate((fixed, tip)), (0, 0, -10))

    assert shared == pytest.approx(expected)

    with pytest.raises(ValueError, match="overlaps the held face"):
        model.solve(fixed, fixed, (0, 0, -10))


def test_voxel_model_preserves_a_sealed_cavity():
    import trimesh

    from nurb import builder

    hollow = Box(20, 20, 20) - Box(16, 16, 16)
    points, tris, _ = builder._triangulate(hollow, 0.1)
    mesh = trimesh.Trimesh(vertices=np.asarray(points), faces=np.asarray(tris), process=False)

    model = stress._voxel_model(hollow, mesh, pitch=1.0)

    assert not np.any(np.all(np.abs(model.centers) < 6, axis=1))


def test_analyze_finds_the_root_of_a_bent_plate():
    # A plate held by one end face and pushed down across its top bends like a
    # cantilever: stress belongs at the held end, not the free one.
    plate = Pos(0, 0, 2.5) * Box(60, 12, 5)
    out = stress.analyze(plate, hold=[(-30, 0, 2.5)], load=(0, 0, 5), kg=2.0, pitch=1.25)

    from nurb import builder

    points, _, _ = builder._triangulate(plate, 0.1)
    assert len(out["values"]) == len(points)
    assert out["max_mpa"] > 0
    assert out["hotspot"][0] < -15  # the held end is at x=-30
    # Bending this plate stretches it along X while its layers stack along Z, so the
    # layer seams see almost none of it and the bulk plastic is what gives.
    assert out["material"] == "PLA"
    assert out["across_mpa"] < out["max_mpa"] / 2
    assert out["gives"] == "plastic"

    # The map itself agrees: vertices near the root carry more than the free end.
    pts = np.asarray(points)
    vals = np.asarray(out["values"])
    root = vals[pts[:, 0] < -25].max()
    tip = vals[pts[:, 0] > 25].max()
    assert root > 3 * tip


def test_a_second_hold_shares_the_load():
    # Held at both ends instead of one, the same weight bends the plate less: the
    # cantilever becomes a bridge. This is what multiple mounting points are for.
    plate = Pos(0, 0, 2.5) * Box(60, 12, 5)
    one = stress.analyze(plate, hold=[(-30, 0, 2.5)], load=(0, 0, 5), kg=2.0, pitch=1.25)
    two = stress.analyze(
        plate, hold=[(-30, 0, 2.5), (30, 0, 2.5)], load=(0, 0, 5), kg=2.0, pitch=1.25
    )
    assert len(two["hold_centers"]) == 2
    assert two["max_mpa"] < one["max_mpa"] / 2
    assert two["deflection_mm"] < one["deflection_mm"] / 4


def test_analyze_refuses_what_it_cannot_answer():
    plate = Pos(0, 0, 2.5) * Box(60, 12, 5)
    with pytest.raises(ValueError, match="positive weight"):
        stress.analyze(plate, hold=[(-30, 0, 2.5)], load=(0, 0, 5), kg=0)
    with pytest.raises(ValueError, match="at least one spot"):
        stress.analyze(plate, hold=[], load=(0, 0, 5), kg=1.0)
    with pytest.raises(ValueError, match="same face"):
        stress.analyze(plate, hold=[(0, 0, 5)], load=(1, 1, 5), kg=1.0, pitch=1.25)


def test_layer_orientation_changes_the_verdict():
    # The same plate printed standing up (layers stacking along X) puts its bending
    # tension straight across the seams: the seams now see the full pull and govern.
    plate = Pos(0, 0, 2.5) * Box(60, 12, 5)
    flat = stress.analyze(plate, hold=[(-30, 0, 2.5)], load=(0, 0, 5), kg=2.0, pitch=1.25)
    standing = stress.analyze(
        plate, hold=[(-30, 0, 2.5)], load=(0, 0, 5), kg=2.0, pitch=1.25, up=(1, 0, 0)
    )
    assert standing["across_mpa"] > 3 * flat["across_mpa"]
    assert standing["gives"] == "layers"
    assert standing["factor"] < flat["factor"]


def test_material_moves_the_numbers_and_tpu_refuses():
    plate = Pos(0, 0, 2.5) * Box(60, 12, 5)
    pla = stress.analyze(plate, hold=[(-30, 0, 2.5)], load=(0, 0, 5), kg=2.0, pitch=1.25)
    petg = stress.analyze(
        plate, hold=[(-30, 0, 2.5)], load=(0, 0, 5), kg=2.0, pitch=1.25, material="petg"
    )
    assert petg["material"] == "PETG"
    # Softer plastic, same force: it sags further while the stress stays put.
    assert petg["deflection_mm"] > pla["deflection_mm"] * 1.3
    assert petg["max_mpa"] == pytest.approx(pla["max_mpa"], rel=0.05)
    with pytest.raises(ValueError, match="TPU bends"):
        stress.analyze(plate, hold=[(-30, 0, 2.5)], load=(0, 0, 5), kg=2.0, material="TPU")
    with pytest.raises(ValueError, match="no material called"):
        stress.analyze(plate, hold=[(-30, 0, 2.5)], load=(0, 0, 5), kg=2.0, material="wood")


def test_default_spots_hold_below_and_load_above():
    plate = Pos(0, 0, 2.5) * Box(60, 12, 5)
    holds, load = stress.default_spots(plate)
    assert holds[0][2] == pytest.approx(0)   # the bottom face holds
    assert load[2] == pytest.approx(5)       # the top face takes the weight
