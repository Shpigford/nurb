"""Reference photos: what find_photos picks, and how small it makes them."""

import base64
import io
import json
import random

import pytest
from PIL import Image

from nurb import db, folder, mcp_server

BASE = "http://127.0.0.1:7373"
PART = """from nurb import *


@part
def x(w=10.0):
    return Box(w, w, w)
"""


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    conn = db.connect(tmp_path / "x.db")
    yield conn
    conn.close()


def noise(width, height, mode="RGB"):
    rng = random.Random(width * height)
    image = Image.new(mode, (width, height))
    image.putdata(
        [
            tuple(rng.randrange(256) for _ in range(len(mode)))
            for _ in range(width * height)
        ]
    )
    return image


def encoded(width, height, fmt):
    buf = io.BytesIO()
    noise(width, height, "RGBA" if fmt == "PNG" else "RGB").save(buf, fmt)
    return buf.getvalue()


def photograph(width, height, fmt):
    """A compressible image, so a normal photo stays at the full 800 px edge."""
    mode = "RGBA" if fmt == "PNG" else "RGB"
    alpha = (128,) if mode == "RGBA" else ()
    image = Image.new(mode, (width, height))
    image.putdata(
        [
            (x * 255 // width, y * 255 // height, (x + y) % 256) + alpha
            for y in range(height)
            for x in range(width)
        ]
    )
    buf = io.BytesIO()
    image.save(buf, fmt)
    return buf.getvalue()


def project_with(conn, tmp_path, images):
    root = tmp_path / "proj"
    (root / "parts").mkdir(parents=True)
    (root / "parts" / "x.py").write_text(PART, encoding="utf-8")
    if images:
        (root / "references").mkdir()
        for name, data in images.items():
            (root / "references" / name).write_bytes(data)
    project_id, _ = folder.import_folder(conn, root)
    return project_id


def call(conn, project_id, query):
    return mcp_server.dispatch(
        conn, "find_photos", {"project_id": project_id, "query": query}, BASE
    )


def images_of(result):
    return [block for block in result.content if block.type == "image"]


def test_two_photos_come_back_downscaled(conn, tmp_path):
    project_id = project_with(
        conn,
        tmp_path,
        {"front.png": photograph(1600, 1200, "PNG"), "side.jpg": photograph(2000, 1500, "JPEG")},
    )
    result = call(conn, project_id, "front")
    assert result.is_error is False
    blocks = images_of(result)
    assert len(blocks) == 2
    payload = json.loads(result.content[0].text)
    assert [photo["name"] for photo in payload["photos"]] == ["front.png", "side.jpg"]
    for block, photo in zip(blocks, payload["photos"]):
        assert block.mime_type == "image/jpeg"
        with Image.open(io.BytesIO(base64.b64decode(block.data))) as decoded:
            assert max(decoded.size) <= 800
            assert decoded.size == (photo["width"], photo["height"])
        print(f"{photo['name']}: {decoded.size} {len(block.data)} base64 characters")
    assert len(result.model_dump_json(by_alias=True, exclude_none=True)) < 150000


def test_no_attachments_says_where_to_put_them(conn, tmp_path):
    project_id = project_with(conn, tmp_path, {})
    result = call(conn, project_id, "front")
    assert result.is_error is True
    assert result.content[0].text == (
        "no reference photos in this project; add images to references/ in the folder"
        " or attach them in the app"
    )


def test_unreadable_attachments_return_an_actionable_error(conn, tmp_path):
    project_id = project_with(conn, tmp_path, {"broken.png": b"not an image"})
    result = call(conn, project_id, "broken")
    assert result.is_error is True
    assert result.content[0].text == (
        "reference photos are attached, but none could be read; replace them with valid PNG or JPEG images"
    )


def test_the_query_ranks_matching_names_first(conn, tmp_path):
    names = ["alpha.png", "hinge_left.png", "beta.png", "hinge_right.png", "gamma.png"]
    project_id = project_with(
        conn, tmp_path, {name: photograph(400, 300, "PNG") for name in names}
    )
    result = call(conn, project_id, "hinge")
    payload = json.loads(result.content[0].text)
    got = [photo["name"] for photo in payload["photos"]]
    assert len(got) == 3
    assert set(got[:2]) == {"hinge_left.png", "hinge_right.png"}
    assert len(images_of(result)) == 3


def test_huge_photos_shrink_until_they_fit(conn, tmp_path):
    project_id = project_with(
        conn,
        tmp_path,
        {f"big_{i}.jpg": encoded(4000, 3000, "JPEG") for i in range(3)},
    )
    result = call(conn, project_id, "big")
    assert result.is_error is False
    payload = json.loads(result.content[0].text)
    assert len(payload["photos"]) == 3
    assert max(payload["photos"][0]["width"], payload["photos"][0]["height"]) < 800
    size = len(result.model_dump_json(by_alias=True, exclude_none=True))
    print(f"shrunk to {payload['photos'][0]['width']} px, {size} characters")
    assert size < 150000
