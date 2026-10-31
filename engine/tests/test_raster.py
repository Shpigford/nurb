"""The flat-shaded renderer, asserted on pixels rather than on file size."""

import base64
import struct
import zlib

import numpy as np
import pytest
import trimesh

from nurb import raster


def _glb(*geoms):
    scene = trimesh.Scene()
    for name, mesh in geoms:
        scene.add_geometry(mesh, node_name=name, geom_name=name)
    return scene.export(file_type="glb")


def _split_faces(mesh):
    """What the engine's exporter does: one vertex per face corner, for crisp normals."""
    return trimesh.Trimesh(vertices=mesh.vertices[mesh.faces].reshape(-1, 3), faces=np.arange(len(mesh.faces) * 3).reshape(-1, 3), process=False)


def _box_glb(extents=(40, 30, 20)):
    box = trimesh.creation.box(extents=extents)
    box.apply_translation([0, 0, extents[2] / 2])
    return _glb(("part", _split_faces(box)))


def _cradle_glb():
    tray = trimesh.creation.box(extents=(60, 60, 8))
    tray.apply_translation([0, 0, 4])
    speaker = trimesh.creation.cylinder(radius=20, height=80)
    speaker.apply_translation([0, 0, 48])
    return _glb(("fixed", tray), ("context", speaker))


def _rails_glb():
    base = trimesh.creation.box(extents=(100, 40, 5))
    base.apply_translation([0, 0, 2.5])
    parts = [base]
    for y in (-12, 12):
        rail = trimesh.creation.box(extents=(100, 6, 10))
        rail.apply_translation([0, y, 10])
        parts.append(rail)
    return _glb(("part", trimesh.util.concatenate(parts)))


def _ihdr(png):
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert png[12:16] == b"IHDR"
    w, h, depth, color_type = struct.unpack(">IIBB", png[16:26])
    return w, h, depth, color_type


def _tones(image):
    rgb = image[..., :3] if image.shape[2] == 4 else image
    flat = rgb.reshape(-1, 3)
    if image.shape[2] == 4:
        flat = flat[image[..., 3].reshape(-1) > 250]
    return {tuple(int(c) for c in row) for row in flat}


def test_png_is_transparent_at_the_asked_size():
    png = raster.render(_box_glb(), width=200, height=120)
    assert _ihdr(png) == (200, 120, 8, 6)


def test_a_box_paints_the_palette_and_a_darker_stroke():
    image = raster.frame(_box_glb(), width=240, height=160)
    tones = _tones(image)
    for tone in (raster.TOP, raster.FRONT, raster.SIDE):
        assert tone in tones
    assert raster.SHADOW in tones
    assert raster.EDGE in tones
    assert sum(raster.EDGE) < sum(raster.SIDE)


def test_context_is_a_ghost_in_looks_and_absent_from_render():
    plain = raster.frame(_cradle_glb(), width=240, height=160, ghost=False)
    ghosted = raster.frame(_cradle_glb(), width=240, height=160, ghost=True)
    assert not (ghosted == plain).all()
    # The ghost's own alpha shows wherever it hangs over empty space.
    over_nothing = (plain[..., 3] == 0) & (ghosted[..., 3] > 0)
    assert over_nothing.any()
    alphas = ghosted[..., 3][over_nothing]
    # Modal, not maximum: the ghost's own edge stroke is darker on purpose.
    assert np.bincount(alphas).argmax() == round(raster.GHOST_ALPHA * 255)


def test_glb_without_triangles_is_unrenderable():
    cloud = trimesh.Scene(trimesh.PointCloud(np.zeros((3, 3)))).export(file_type="glb")
    with pytest.raises(raster.Unrenderable):
        raster.render(cloud)


def test_garbage_bytes_raise():
    with pytest.raises(Exception):
        raster.render(b"not a glb at all")


def test_the_same_glb_renders_the_same_bytes():
    glb = _box_glb()
    assert raster.render(glb, width=160, height=120) == raster.render(glb, width=160, height=120)


def test_rails_do_not_paint_over_the_top_face():
    """The z-buffer regression: a far rail's sliver must not cover the near rail."""
    glb = _rails_glb()
    mesh, _ = raster._split(glb)
    width, height = 320, 200
    image = raster.frame(glb, raster.VIEW, width=width, height=height, ghost=False)
    ss = raster.SUPERSAMPLE
    project, _ = raster._camera(np.asarray(mesh.vertices), raster.VIEW / np.linalg.norm(raster.VIEW), width * ss, height * ss)
    for x in (-30.0, 0.0, 30.0):
        # The near rail's front face (y = -15) and its top face (z = 15).
        for point, tone in (((x, -15.0, 10.0), raster.FRONT), ((x, -12.0, 15.0), raster.TOP)):
            pts, _ = project([point])
            px, py = int(pts[0, 0] / ss), int(pts[0, 1] / ss)
            assert tuple(int(c) for c in image[py, px, :3]) == tone, f"{point} painted {image[py, px, :3]}"


def test_named_views_come_back_in_order():
    out = raster.looks(_box_glb(), list(raster.VIEWS), width=160, height=120)
    assert list(out) == ["iso", "back", "top", "under"]
    assert all(_ihdr(png) == (160, 120, 8, 6) for png in out.values())


def test_under_has_no_shadow_and_back_differs_from_iso():
    frames = {name: raster.frame(_box_glb(), name, width=160, height=120, ghost=False) for name in raster.VIEWS}
    assert raster.SHADOW not in _tones(frames["under"])
    assert raster.SHADOW in _tones(frames["iso"])
    assert not (frames["back"] == frames["iso"]).all()


def test_unknown_view_is_refused():
    with pytest.raises(ValueError, match="unknown view 'side'"):
        raster.looks(_box_glb(), ["iso", "side"])


def test_a_cut_removes_the_half_above_the_plane():
    glb = _box_glb()
    mesh, _ = raster._split(glb)
    kept, cap_normal = raster._sliced(mesh, ("z", 10.0), raster.VIEW)
    assert kept.bounds[1][2] == pytest.approx(10.0)
    assert tuple(cap_normal) == (0.0, 0.0, 1.0)
    whole = raster.frame(glb, "iso", width=200, height=140, ghost=False)
    half = raster.frame(glb, "iso", width=200, height=140, ghost=False, cut=("z", 10.0))
    assert not (half == whole).all()
    # Looking straight down into the cut still finds a lid: the cap.
    lid = raster.frame(glb, "top", width=200, height=140, ghost=False, cut=("z", None))
    assert raster.TOP in _tones(lid)


def _decode_png(png):
    """The pixels back out of an encode_png file: one zlib stream, filter 0 on every row."""
    w, h, depth, color_type = _ihdr(png)
    channels = {2: 3, 6: 4}[color_type]
    idat = b""
    pos = 8
    while pos < len(png):
        length = struct.unpack(">I", png[pos : pos + 4])[0]
        kind = png[pos + 4 : pos + 8]
        if kind == b"IDAT":
            idat += png[pos + 8 : pos + 8 + length]
        pos += 12 + length
    rows = np.frombuffer(zlib.decompress(idat), dtype=np.uint8).reshape(h, 1 + w * channels)
    assert (rows[:, 0] == 0).all()
    return rows[:, 1:].reshape(h, w, channels)


def test_the_composite_is_the_four_views_in_order_under_their_labels():
    glb = _box_glb()
    tw, th = 200, 130
    png = raster.composite(glb, tile=(tw, th))
    pixels = _decode_png(png)
    strip = (pixels.shape[0] - 1) // 2 - th
    assert strip > 0 and pixels.shape[1] == tw * 2 + 1
    for i, name in enumerate(raster.VIEWS):
        y = (i // 2) * (th + strip + 1)
        x = (i % 2) * (tw + 1)
        expected = raster._flatten(raster.frame(glb, name, width=tw, height=th, ghost=False))
        assert (pixels[y + strip : y + strip + th, x : x + tw] == expected).all(), name
        label = pixels[y : y + strip, x : x + tw]
        assert (label == raster.LABEL).all(axis=2).any(), f"no {name} label"
    # The four quadrants are four different pictures.
    frames = [raster._flatten(raster.frame(glb, n, width=tw, height=th, ghost=False)) for n in raster.VIEWS]
    assert all(not (a == b).all() for k, a in enumerate(frames) for b in frames[k + 1 :])
    for corner in (pixels[0, 0], pixels[0, -1], pixels[-1, 0], pixels[-1, -1]):
        assert tuple(corner) == raster.PAPER
    assert len(base64.b64encode(png)) < 80_000


def test_encode_png_takes_rgb_and_rgba():
    rgb = np.zeros((4, 6, 3), dtype=np.uint8)
    rgba = np.zeros((4, 6, 4), dtype=np.uint8)
    assert _ihdr(raster.encode_png(rgb)) == (6, 4, 8, 2)
    assert _ihdr(raster.encode_png(rgba)) == (6, 4, 8, 6)
    with pytest.raises(ValueError):
        raster.encode_png(np.zeros((4, 6, 2), dtype=np.uint8))


def test_encode_png_round_trips_through_zlib():
    import zlib

    array = np.random.default_rng(0).integers(0, 255, (5, 7, 3), dtype=np.uint8)
    png = raster.encode_png(array)
    start = 8 + 25
    length = struct.unpack(">I", png[start : start + 4])[0]
    raw = zlib.decompress(png[start + 8 : start + 8 + length])
    stride = 7 * 3 + 1
    rows = np.frombuffer(raw, dtype=np.uint8).reshape(5, stride)
    assert (rows[:, 0] == 0).all()
    assert (rows[:, 1:].reshape(5, 7, 3) == array).all()


def test_a_cut_past_the_part_says_where_the_part_is():
    with pytest.raises(raster.Unrenderable, match=r"z=40 misses the part, which spans z -?0 to 20"):
        raster.render(_box_glb(), cut=("z", 40.0))
