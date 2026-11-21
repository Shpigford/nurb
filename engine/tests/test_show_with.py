import io
import re
import zipfile

import trimesh

from nurb import engine_run

STAND = '''from nurb import *

@part
def stand(text_color: FilamentColor = "#ffffff"):
    body = add_text(add_color(Box(40, 20, 10), "#d8ceb6"), "HI")
    phone = Pos(0, 0, 45) * Box(30, 4, 70)
    return show_with(body, phone)
'''


def test_a_stand_in_is_shown_but_never_checked_or_printed(tmp_path):
    """The phone a stand holds rides beside the part: drawn, never judged or exported."""
    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "stand.py").write_text(STAND)

    result = engine_run._build_in_process(tmp_path, "stand")
    assert result["error"] is None, result.get("traceback")
    scene = trimesh.load(io.BytesIO(result["glb_bytes"]), file_type="glb")
    assert "context" in scene.geometry
    assert "text" in scene.geometry  # the part keeps its own bodies beside it
    # A phone that floats above the part would fail as a second piece if it were printed.
    assert not [f for f in result["findings"] if f["severity"] == "fail"], result["findings"]

    # The 3MF is what the person downloads: nothing in it stands as tall as the phone.
    exported = engine_run._export_in_process(tmp_path, "stand", "3mf")
    with zipfile.ZipFile(io.BytesIO(exported["bytes"])) as bundle:
        model = bundle.read("3D/3dmodel.model").decode()
    heights = [float(z) for z in re.findall(r' z="([-0-9.e]+)"', model)]
    assert heights and max(heights) - min(heights) < 15
