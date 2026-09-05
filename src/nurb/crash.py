"""What happens when the CAD kernel itself dies.

OCCT can segfault on a legal-looking chamfer (issue #247: `Geom2dAdaptor_Curve::D0` on
a polished union). A signal is not a Python exception, so nothing in a part file or in
the server can catch it, and the default outcome is the interpreter dying with a signal:
exit 139 from `nurb build`, and under `nurb dev` a dead server plus a macOS "Python quit
unexpectedly" dialog for every restart that walks into the same build.

OCCT's own converter (`OSD::SetSignal`) does not help here: OCP builds it in longjmp
mode, so it only catches inside algorithms that opted in with OCC_CATCH_SIGNALS and
exits the process from everywhere else. So the handler is ours, installed through
ctypes because Python-level signal handlers run too late for a fault, and it does the
two things a fault leaves possible: say what was being built, then leave without dying
by the signal. A process that exits normally raises no crash dialog.

For a one-shot command that means exit 1 with a message. The dev server instead execs
itself with the crash described in the environment, so the same process (same pid,
same port, same pipes for the desktop supervisor) comes back and marks that part as
crashed until its inputs change, rather than building it again and dying again.
"""

import ctypes
import json
import os
import pathlib
import signal
import sys
import traceback

# The part being built right now, set by builder.build. None outside a build, which
# means a crash there is nurb's own bug and gets a plain exit rather than a restart.
part = None

# (variable, state, marker): the server's runtime settings and the active build. A restart carries both the previous faults and this one, so two broken parts cannot alternate forever.
restart = None

NAMES = {
    signal.SIGSEGV: "segmentation fault",
    signal.SIGBUS: "bus error",
    signal.SIGILL: "illegal instruction",
    signal.SIGFPE: "floating point error",
    signal.SIGABRT: "abort",
}

HINT = (
    "This is a fault inside the CAD kernel, not an error a part file can catch. It "
    "usually means a chamfer or polish on a body assembled from several unions. Polish "
    "the simple solids before uniting them, or take those edges out of the set."
)

_HANDLER = ctypes.CFUNCTYPE(None, ctypes.c_int)
_keep = []  # the callback object must outlive the installation


def _frame(path):
    """`file:line  source` for the innermost frame inside the part's project."""
    root = str(pathlib.Path(path).resolve().parent.parent)
    for entry in reversed(traceback.extract_stack()):
        if not entry.filename.startswith(root) or "site-packages" in entry.filename:
            continue
        where = pathlib.Path(entry.filename).relative_to(root).as_posix()
        if where.startswith("."):
            continue  # a .venv inside the project is not the user's code
        return f"{where}:{entry.lineno}  {entry.line or ''}".rstrip()
    return None


def describe(signum):
    """The message a crash gets, composed while the faulting stack is still there."""
    what = NAMES.get(signum, f"signal {signum}")
    if part is None:
        return f"nurb crashed ({what}) outside a part build; please report this"
    lines = [f"the CAD kernel crashed ({what}) building {pathlib.Path(part).stem}"]
    where = _frame(part)
    if where:
        lines.append(f"  at {where}")
    lines.append(HINT)
    return "\n".join(lines)


def _on_signal(signum):
    message = describe(signum)
    os.write(2, (message + "\n").encode("utf-8", "replace"))
    if restart is not None and part is not None:
        variable, state, marker = restart
        # The first line is the status the terminal and the rail show; the whole
        # message is the detail the viewer shows in the error's place.
        marker = {**marker, "error": message.splitlines()[0], "traceback": message}
        state = {**state, "crashed": {**state["crashed"], marker["path"]: marker}}
        env = {**os.environ, variable: json.dumps(state)}
        os.write(2, b"  restarting the server; the part stays marked until its file changes\n")
        try:
            # exec preserves signal masks, including the signal blocked while its handler runs. Leaving it blocked makes the next kernel fault hang.
            signal.pthread_sigmask(signal.SIG_UNBLOCK, {signum})
            os.execve(sys.executable, [sys.executable, *sys.orig_argv[1:]], env)
        except OSError:
            pass
    os._exit(1)


def install():
    """Route the fatal signals through _on_signal for the rest of this process."""
    if _keep:
        return
    libc = ctypes.CDLL(None)
    libc.signal.argtypes = [ctypes.c_int, _HANDLER]
    libc.signal.restype = ctypes.c_void_p
    handler = _HANDLER(_on_signal)
    _keep.append(handler)
    for signum in NAMES:
        libc.signal(signum, handler)
