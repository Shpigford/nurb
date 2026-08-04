import pytest


@pytest.fixture(autouse=True)
def hermetic_global_config(monkeypatch, tmp_path_factory):
    """The developer's real ~/.config/nurb/config.toml must never leak into the
    suite: it names their printer, and every default-context assertion would
    quietly become an assertion about their workshop."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("xdg")))
