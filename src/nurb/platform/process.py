from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Sequence


def popen_kwargs() -> dict:
    """Return safe subprocess options shared by platform-aware launchers."""
    kwargs: dict = {}
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kwargs


def run(args: Sequence[str | Path], **kwargs) -> subprocess.CompletedProcess:
    options = popen_kwargs()
    options.update(kwargs)
    return subprocess.run([str(a) for a in args], **options)
