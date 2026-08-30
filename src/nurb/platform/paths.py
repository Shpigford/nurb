from __future__ import annotations

import os
import platform
from pathlib import Path


def home_dir() -> Path:
    """The user's home, honoring an explicit HOME override.

    ``Path.home()`` ignores ``HOME`` on Windows and reads ``USERPROFILE``
    instead. Honoring ``HOME`` when it is set (Git Bash sets it, and tests
    move it to a scratch directory) keeps one notion of "home" everywhere
    while falling back to the native location on a normal Windows session.
    """
    override = os.environ.get("HOME")
    if override:
        return Path(override)
    return Path.home()


def _windows_base(env_name: str, fallback: str) -> Path:
    return Path(os.environ.get(env_name) or fallback).expanduser()


def user_data_dir() -> Path:
    """The directory where the application keeps its own state (not user projects).

    %APPDATA%\\nurb on Windows, ~/Library/Application Support/nurb on macOS,
    $XDG_DATA_HOME/nurb (or ~/.local/share/nurb) on Linux.
    """
    if os.name == "nt":
        return _windows_base("APPDATA", str(home_dir() / "AppData" / "Roaming")) / "nurb"
    if platform.system() == "Darwin":
        return home_dir() / "Library" / "Application Support" / "nurb"
    return Path(os.environ.get("XDG_DATA_HOME") or home_dir() / ".local" / "share") / "nurb"


def user_config_dir() -> Path:
    """The directory for configuration files: nurb's own config.toml lives here.

    %APPDATA%\\nurb on Windows (tests may still point XDG_CONFIG_HOME at a
    scratch directory), ~/Library/Application Support/nurb on macOS,
    $XDG_CONFIG_HOME/nurb (or ~/.config/nurb) on Linux.
    """
    if os.name == "nt":
        override = os.environ.get("XDG_CONFIG_HOME")
        if override:
            return Path(override) / "nurb"
        return user_data_dir()
    if platform.system() == "Darwin":
        return home_dir() / "Library" / "Application Support" / "nurb"
    return Path(os.environ.get("XDG_CONFIG_HOME") or home_dir() / ".config") / "nurb"


def user_cache_dir() -> Path:
    """The directory for disposable caches: the PyPI check, render temp files.

    %LOCALAPPDATA%\\nurb\\cache on Windows, ~/Library/Caches/nurb on macOS,
    $XDG_CACHE_HOME/nurb (or ~/.cache/nurb) on Linux.
    """
    if os.name == "nt":
        return _windows_base("LOCALAPPDATA", str(home_dir() / "AppData" / "Local")) / "nurb" / "cache"
    if platform.system() == "Darwin":
        return home_dir() / "Library" / "Caches" / "nurb"
    return Path(os.environ.get("XDG_CACHE_HOME") or home_dir() / ".cache") / "nurb"
