"""Gate, then grade.

A candidate that does not build, or builds more than one solid, scores zero: an
unprintable file has no partial credit to give. Past the gate, three stages carry
weights: the printability rules, the task's own dimensional assertions, and the flex
probes that catch a decorative parameter. Graded rather than binary because partial
credit stabilizes small-sample means, which is what lets a leaderboard row cost three
trials instead of five.

The result is a plain dict so the subprocess boundary (see grade.py) is just JSON.
"""

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time

WEIGHTS = {"lint": 0.3, "dims": 0.5, "flex": 0.2}

FAIL_COST = 0.5
WARN_COST = 0.25


def _text(problem):
    """A misfit is a message, optionally weighted: `str` or `(str, weight)`.
    Function tasks weight their gates above fit-and-finish checks."""
    return problem[0] if isinstance(problem, tuple) else problem


def _cost(problem):
    return problem[1] if isinstance(problem, tuple) else 1


def load_task(task_dir):
    path = pathlib.Path(task_dir).resolve() / "task.py"
    spec = importlib.util.spec_from_file_location(f"_nurb_eval_task_{path.parent.name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def benchmark_identity(task_dir):
    """Versions plus a content revision for everything that can change a row."""
    import nurb

    versions = {
        "nurb_version": importlib.metadata.version("nurb"),
        "benchmark_version": importlib.metadata.version("nurb-evals"),
    }
    digest = hashlib.sha256()
    for name, value in sorted(versions.items()):
        digest.update(f"{name}\0{value}\0".encode())

    roots = (
        (
            "evals",
            pathlib.Path(__file__).parent,
            {"candidate.py", "grade.py", "harness.py", "run.py", "scoring.py"},
        ),
        (
            "task",
            pathlib.Path(task_dir).resolve(),
            None,
        ),
        (
            "nurb",
            pathlib.Path(nurb.__file__).parent,
            None,
        ),
    )
    suffixes = {".py", ".md", ".toml"}
    for label, root, names in roots:
        files = sorted(
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix in suffixes
            and (names is None or path.name in names)
        )
        for path in files:
            relative = path.relative_to(root).as_posix()
            digest.update(f"{label}/{relative}\0".encode())
            digest.update(path.read_bytes())
            digest.update(b"\0")

    lock = pathlib.Path(__file__).parents[2] / "uv.lock"
    if lock.is_file():
        digest.update(b"evals/uv.lock\0")
        digest.update(lock.read_bytes())
    return {**versions, "benchmark_revision": digest.hexdigest()[:12]}


def _gate_failure(error, solids=0, built=False):
    return {
        "built": built,
        "solids": solids,
        "error": error,
        "findings": [],
        "misfits": [],
        "flex_problems": [],
        "stages": {"lint": 0.0, "dims": 0.0, "flex": 0.0},
        "score": 0.0,
        "build_ms": None,
    }


def _candidate_builds(part_path, requests, timeout):
    """Build every requested parameter set beyond the scorer's trust boundary."""
    from build123d import import_brep

    with tempfile.TemporaryDirectory(prefix="nurb-eval-") as raw:
        root = pathlib.Path(raw)
        request = root / "request.json"
        out = root / "built"
        request.write_text(json.dumps(requests), encoding="utf-8")
        cmd = [
            sys.executable,
            "-m",
            "nurb_evals.candidate",
            str(pathlib.Path(part_path).resolve()),
            str(request),
            str(out),
        ]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            start_new_session=True,
        )
        timed_out = False
        try:
            _, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _, stderr = process.communicate()

        fallback = f"timeout: candidate did not finish within {timeout:.0f}s" if timed_out else None
        if process.returncode and not fallback:
            tail = (stderr or "").strip().splitlines()[-3:]
            fallback = "candidate builder crashed: " + (
                " | ".join(tail) or f"exit {process.returncode}"
            )

        rows = []
        manifest = out / "manifest.json"
        if manifest.is_file():
            try:
                loaded = json.loads(manifest.read_text(encoding="utf-8"))
                rows = loaded if isinstance(loaded, list) else []
            except (OSError, json.JSONDecodeError):
                pass
        if not rows and not fallback:
            fallback = "candidate builder produced no manifest"

        built = []
        for index in range(len(requests)):
            completed = index < len(rows) and isinstance(rows[index], dict)
            row = rows[index] if completed else {}
            # A later request can crash or time out after earlier BREP files were
            # committed to the manifest. Keep those completed builds; the fallback
            # belongs only to requests the worker never reported.
            error = row.get("error") if completed else fallback
            shape = None
            target = out / f"{index}.brep"
            if not error and target.is_file():
                try:
                    shape = import_brep(target)
                except Exception as exc:
                    error = f"invalid candidate BREP: {type(exc).__name__}: {exc}"
            elif not error:
                error = "candidate builder produced no BREP"
            built.append({"shape": shape, "error": error, "build_ms": row.get("build_ms")})
        return built


def _probe_name(spec):
    if spec.get("label"):
        return spec["label"]
    return ", ".join(f"{name}={value}" for name, value in (spec.get("params") or {}).items())


def _build_request(spec):
    """What the isolated builder needs from a probe spec: parameter overrides and,
    for measurement probes, the rewritten measurements.toml text."""
    return {key: spec[key] for key in ("params", "measurements") if spec.get(key)}


def grade(part_path, task_dir, seed, timeout=59.0):
    from nurb import checks

    task = load_task(task_dir)
    inst = task.instance(seed)
    probes = task.flex_probes(inst)
    # Read before the first build: a task whose audit grades the project's paperwork
    # must grade what the model left behind, not what the part writes as it imports.
    book = pathlib.Path(part_path).resolve().parent.parent / "measurements.toml"
    recorded = book.read_text(encoding="utf-8") if book.is_file() else None
    builds = _candidate_builds(
        part_path,
        [{}, *(_build_request(spec) for spec, _ in probes)],
        timeout=timeout,
    )

    shape = builds[0]["shape"]
    if shape is None:
        return _gate_failure(builds[0]["error"])
    solids = len(shape.solids())
    if solids != 1:
        return _gate_failure(f"{solids} solids, expected exactly 1", solids=solids, built=True)

    findings = checks.run(shape, task.context())
    lint = max(
        0.0,
        1.0 - sum(FAIL_COST if f.severity == checks.FAIL else WARN_COST for f in findings),
    )

    problems, total = task.misfits(shape, inst.dims)
    if hasattr(task, "audit"):
        # Paperwork checks that are not shape checks: a judgment task grades what the
        # model recorded next to the part, not only what it built.
        audit_problems, audit_total = task.audit(shape, inst, recorded)
        problems = problems + audit_problems
        total += audit_total
    dims = max(0.0, 1.0 - sum(_cost(p) for p in problems) / total)

    flex_problems = []
    for (spec, expected_dims), result in zip(probes, builds[1:]):
        name = _probe_name(spec)
        if result["shape"] is None:
            flex_problems.append(f"{name} does not build: {result['error']}")
            continue
        solids = len(result["shape"].solids())
        if solids != 1:
            flex_problems.append(f"{name} builds {solids} solids, expected exactly 1")
            continue
        wrong, _ = task.misfits(result["shape"], expected_dims)
        if wrong:
            flex_problems.append(f"{name} does not track: {'; '.join(_text(w) for w in wrong)}")
    flex = max(0.0, 1.0 - len(flex_problems) / len(probes))

    stages = {"lint": round(lint, 4), "dims": round(dims, 4), "flex": round(flex, 4)}
    return {
        "built": True,
        "solids": 1,
        "error": None,
        "findings": [
            {"rule": f.rule, "severity": f.severity, "message": f.message, "value": f.value}
            for f in findings
        ],
        "misfits": [_text(p) for p in problems],
        "flex_problems": flex_problems,
        "stages": stages,
        "score": round(sum(WEIGHTS[k] * stages[k] for k in WEIGHTS), 4),
        "build_ms": builds[0]["build_ms"],
    }


def main():
    import argparse

    ap = argparse.ArgumentParser(description="score one candidate part")
    ap.add_argument("part")
    ap.add_argument("task_dir")
    ap.add_argument("seed", type=int)
    ap.add_argument("--timeout", type=float, default=59.0)
    args = ap.parse_args()
    started = time.perf_counter()
    result = grade(args.part, args.task_dir, args.seed, timeout=args.timeout)
    result["grade_s"] = round(time.perf_counter() - started, 2)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
