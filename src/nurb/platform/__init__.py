"""Small cross-platform platform surface for nurb.

Keep OS-specific behavior here so upstream core modules stay easy to merge.
"""
from .system import current_platform, is_windows
from .paths import home_dir, user_config_dir, user_data_dir, user_cache_dir
from .runtime import executable_name, bundled_uv_name
from .process import run, popen_kwargs

__all__ = [
    "bundled_uv_name", "current_platform", "executable_name", "home_dir",
    "is_windows", "popen_kwargs", "run", "user_cache_dir", "user_config_dir",
    "user_data_dir",
]
