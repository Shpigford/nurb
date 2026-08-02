"""Grade a candidate part behind a subprocess boundary, with a hard timeout.

The scorer launches candidate builds in their own process, keeping submitted code away
from the check functions and verdict channel. This outer process is still timed so a
pathological BREP import or check cannot hang the harness either.

Always prints one JSON object and exits zero; the score carries the verdict.
"""

import argparse
import json
import subprocess
import sys


def run(part, task_dir, seed, timeout=60.0):
    # Leave the trusted scorer time to import and grade completed BREP files after a
    # later flex build consumes the candidate timeout.
    # Short explicit caps spend most of their budget on process startup, BREP import,
    # and checks; the normal 60s cap still gives candidate builds a full 50 seconds.
    reserve = min(10.0, max(1.0, timeout * 0.75))
    inner_timeout = max(0.1, timeout - reserve)
    cmd = [
        sys.executable,
        "-m",
        "nurb_evals.scoring",
        str(part),
        str(task_dir),
        str(seed),
        "--timeout",
        str(inner_timeout),
    ]
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return _failure(f"timeout: no verdict within {timeout:.0f}s")
    if done.returncode != 0:
        tail = (done.stderr or "").strip().splitlines()[-3:]
        return _failure("grader crashed: " + (" | ".join(tail) or f"exit {done.returncode}"))
    try:
        return json.loads(done.stdout)
    except json.JSONDecodeError:
        return _failure("grader printed something that is not JSON")


def _failure(error):
    return {
        "built": False,
        "solids": 0,
        "error": error,
        "findings": [],
        "misfits": [],
        "flex_problems": [],
        "stages": {"lint": 0.0, "dims": 0.0, "flex": 0.0},
        "score": 0.0,
        "build_ms": None,
    }


def main():
    ap = argparse.ArgumentParser(description="grade one candidate part for one task")
    ap.add_argument("part")
    ap.add_argument("task_dir")
    ap.add_argument("seed", type=int)
    ap.add_argument("--timeout", type=float, default=60.0)
    args = ap.parse_args()
    print(json.dumps(run(args.part, args.task_dir, args.seed, timeout=args.timeout)))


if __name__ == "__main__":
    main()
