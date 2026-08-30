from __future__ import annotations

import os
import platform


def current_platform() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    if system == "linux":
        return "linux"
    return system


def is_windows() -> bool:
    return os.name == "nt"
