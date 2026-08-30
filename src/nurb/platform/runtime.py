from __future__ import annotations

import os


def executable_name(name: str) -> str:
    return f"{name}.exe" if os.name == "nt" and not name.lower().endswith(".exe") else name


def bundled_uv_name() -> str:
    return executable_name("uv")
