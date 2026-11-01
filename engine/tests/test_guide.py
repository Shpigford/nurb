"""The guide is the whole briefing, so it has to stay complete and stay small."""

import pathlib
import tomllib

import pytest

from nurb import __version__, api, db, guide, mcp_server

BASE = "http://127.0.0.1:7373"
PYPROJECT = pathlib.Path(__file__).parents[1] / "pyproject.toml"


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    conn = db.connect(tmp_path / "x.db")
    yield conn
    conn.close()


def test_guide_fits_in_a_single_tool_result():
    assert len(guide.text()) < 100000


def test_first_line_names_the_shipped_version():
    version = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    assert __version__ == version
    assert guide.text().splitlines()[0] == f"# nurb {version} guide"


def test_sections_without_a_tool_are_dropped():
    text = guide.text()
    assert "## Cards" not in text
    assert "## Assemblies" not in text
    assert "## Printability" in text


def test_the_vocabulary_rides_along():
    text = guide.text()
    assert "# nurb vocabulary" in text
    assert api.report()[0] in text


def test_the_build123d_reference_rides_along():
    assert "# build123d reference" in guide.text()


def test_read_guide_returns_the_markdown_itself(conn):
    result = mcp_server.dispatch(conn, "read_guide", {}, BASE)
    assert result.is_error is False
    assert len(result.content) == 1
    assert result.content[0].text.startswith("# nurb ")
