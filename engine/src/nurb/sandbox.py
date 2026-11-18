"""The walls around the build worker.

A part is Python, and a part can arrive from a stranger's share link, so the process
that runs it gets no network, can write only where a build writes, and can start no
program at all. Reading stays open: Python and the CAD kernel live all over the
disk, and with no way out a part can read but has nowhere to send what it read. The
slicer needs all three, so it runs outside on the finished file: it reads geometry,
never the part's code.

macOS only, through the same Seatbelt the agents already run under. Elsewhere the
worker runs as before.
"""

import ctypes
import os
import pathlib
import sys
import tempfile

# The ways to hand data to something outside the walls without starting a program:
# opening a link goes through Launch Services, scripting another app goes through
# Apple Events, and the clipboard is one paste away from anywhere.
SERVICES = (
    "com.apple.coreservices.launchservicesd",
    "com.apple.lsd.mapdb",
    "com.apple.coreservices.appleevents",
    "com.apple.pasteboard.1",
)


def _quoted(path):
    return '"' + str(path).replace("\\", "\\\\").replace('"', '\\"') + '"'


def walls(scratch):
    """The folders a worker that builds out of `scratch` may write. Its own temp folder
    lives inside, so scratch is the one place a part can write."""
    return [os.path.realpath(scratch)]


def use_temp(scratch):
    """Point this process's temp files inside `scratch`, before the walls go up."""
    folder = pathlib.Path(scratch) / ".tmp"
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.environ["TMPDIR"] = str(folder)
    tempfile.tempdir = str(folder)


def profile(writable):
    allowed = " ".join(f"(subpath {_quoted(p)})" for p in writable)
    services = " ".join(f'(global-name "{name}")' for name in SERVICES)
    lines = [
        "(version 1)",
        "(allow default)",
        "(deny network*)",
        "(deny file-write*)",
        f'(allow file-write* {allowed} (literal "/dev/null") (literal "/dev/tty") (regex #"^/dev/fd/"))',
        "(deny process-exec*)",
        f"(deny mach-lookup {services})",
    ]
    return "\n".join(lines)


def confine(writable):
    """Wall in this process and everything it starts, for good. Raises OSError when
    macOS refuses, so a caller can fail closed rather than build in the open."""
    if sys.platform != "darwin":
        return
    lib = ctypes.CDLL("/usr/lib/libSystem.dylib")
    lib.sandbox_check.restype = ctypes.c_int
    if lib.sandbox_check(os.getpid(), None, 0) == 1:
        # Started inside someone else's sandbox (an agent's, say). macOS refuses a
        # second one, and the outer walls are already the ones that apply.
        return
    lib.sandbox_init.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_char_p)]
    lib.sandbox_init.restype = ctypes.c_int
    error = ctypes.c_char_p()
    if lib.sandbox_init(profile(writable).encode(), 0, ctypes.byref(error)) != 0:
        said = error.value.decode(errors="replace") if error.value else "no reason given"
        raise OSError(f"macOS would not sandbox the build worker: {said}")
