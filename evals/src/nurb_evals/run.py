"""Run a leaderboard row's trials: harness in, JSONL rows out.

Each trial gets a fresh materialized project, the harness CLI runs there on the
contributor's own subscription, and whatever lands at the task's stated part path is
graded by the Phase 1 subprocess grader. The wall-clock timeout exists to stop
runaway sessions, not to measure anything: time per part is one of the three numbers
a user actually decides on (time, money, accuracy), so the cap sits high enough that
a model that finishes gets its true time recorded, a capped trial is labeled as
censored everywhere the time is shown, and the cap itself lands in the row.

Everything is kept: the result row, the harness transcript, and the project the model
left behind, because a leaderboard row nobody can audit is a rumor.
"""

import argparse
import contextlib
import json
import os
import pathlib
import signal
import shutil
import subprocess
import sys
import tempfile
import time

from . import grade, harness as harnesses, scoring

# The shipped skill assumes a live viewer and a human answering questions; a benchmark
# has neither, and a model that follows those directives anyway burns its budget
# waiting. This overrides them without touching what the skill says about design.
PREAMBLE = """\
You are being benchmarked, non-interactively, inside a throwaway nurb project (the
current directory). There is no human to ask and no browser to look at: never run
`nurb dev`, never wait for input, and never ask questions. The `nurb` CLI is on PATH;
`nurb build`, `nurb check`, and `nurb inspect` are your only feedback. When you are
done, the part file named below must exist at its stated path.

"""


@contextlib.contextmanager
def _isolated_nurb_environment(env, raw):
    """Install the locked nurb build outside the checkout for one agent run.

    The benchmark itself is editable, so handing its Python or nurb executable to an
    agent also hands it a path back to tests/solutions and tasks/*/task.py. A locked,
    non-editable install in the trial's temp directory removes that breadcrumb without
    changing shared checkout permissions. Concurrent and interrupted trials therefore
    cannot expose answers to one another or leave the repository unreadable.
    """
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required to prepare the isolated nurb runtime")

    evals = pathlib.Path(__file__).parents[2]
    runtime = pathlib.Path(raw) / "runtime"
    venv = runtime / "venv"
    setup_env = dict(os.environ)
    setup_env["VIRTUAL_ENV"] = str(venv)
    commands = (
        [uv, "venv", "--python", sys.executable, str(venv)],
        [
            uv,
            "sync",
            "--project", str(evals),
            "--active",
            "--frozen",
            "--offline",
            "--no-editable",
            "--no-dev",
            "--no-install-project",
            "--no-progress",
        ],
    )
    for command in commands:
        done = subprocess.run(command, env=setup_env, capture_output=True, text=True)
        if done.returncode != 0:
            detail = (done.stderr or done.stdout).strip().splitlines()
            raise RuntimeError(
                "could not prepare isolated nurb runtime"
                + (f": {detail[-1]}" if detail else "")
            )

    # Local wheel metadata records where it was built. It is irrelevant at runtime
    # and would recreate the checkout breadcrumb this environment exists to remove.
    site = next((venv / "lib").glob("python*/site-packages"))
    for direct_url in site.glob("nurb-*.dist-info/direct_url.json"):
        direct_url.unlink()

    clean = dict(env)
    benchmark_bin = pathlib.Path(sys.executable).parent.resolve()
    inherited = [
        entry
        for entry in clean.get("PATH", "").split(os.pathsep)
        if not entry or pathlib.Path(entry).expanduser().resolve() != benchmark_bin
    ]
    clean["PATH"] = os.pathsep.join((str(venv / "bin"), *inherited))
    clean["VIRTUAL_ENV"] = str(venv)
    yield clean


def _invoke(cmd, *, cwd, env, timeout):
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout or "", stderr or "", False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        return process.returncode, stdout or "", stderr or "", True


class HarnessKilled(RuntimeError):
    """The agent process died by an external signal: no row exists for this trial."""


KILL_RETRIES = 2  # fresh sessions to try after a killed one, before giving up


def _grave(task_out, n):
    """A unique resting place for a killed session, next to the trial slots but
    never mistaken for one: the slot stays free for the retry, and the dead
    session stays auditable."""
    k = 1
    while (task_out / f"trial_{n}_killed_{k}").exists():
        k += 1
    grave = task_out / f"trial_{n}_killed_{k}"
    grave.mkdir(parents=True)
    return grave


def completed_trial(h, task_dir, seed, n, out, **kwargs):
    """One row from one finished agent session. A killed session is never scored:
    the trial reruns fresh, and persistent kills abort the run loudly instead of
    writing rows that measure the machine."""
    for attempt in range(KILL_RETRIES + 1):
        try:
            return trial(h, task_dir, seed, n, out, **kwargs)
        except HarnessKilled as killed:
            last = killed
            if attempt < KILL_RETRIES:
                print(f"trial {n}: {killed}; retrying with a fresh session", flush=True)
    raise RuntimeError(
        f"trial {n}: {KILL_RETRIES + 1} agent sessions in a row were killed "
        f"({last}); something on this machine is terminating agents, fix that "
        f"and rerun"
    )


def trial(h, task_dir, seed, n, out, model=None, effort=None, timeout=3600.0):
    task = scoring.load_task(task_dir)
    benchmark = scoring.benchmark_identity(task_dir)
    task_name = pathlib.Path(task_dir).name
    part_file = f"parts/{task_name}.py"
    slot = out / task_name / f"trial_{n}"
    if slot.exists():
        # A pre-seeded project would grade a planted solution the harness never wrote,
        # and produce a perfect row with audit-plausible artifacts. Refusing is the
        # fix that cannot silently destroy anything.
        raise RuntimeError(f"{slot} already exists; every trial gets a fresh directory")
    with tempfile.TemporaryDirectory(prefix="nurb-eval-trial-") as raw:
        project = pathlib.Path(raw) / "project"
        task.materialize(seed, project)
        prompt = PREAMBLE + task.instance(seed).instruction

        env = dict(os.environ)
        # Do not hand the agent an environment-variable path back to the checkout we
        # just moved it away from. None of these variables is required by a harness.
        for name in tuple(env):
            inherited_path = name in {"OLDPWD", "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"}
            if name.startswith("CONDUCTOR_") or inherited_path:
                env.pop(name)
        env["PATH"] = f"{pathlib.Path(sys.executable).parent}:{env.get('PATH', '')}"
        env["PWD"] = str(project)

        error = None
        stdout = ""
        # Build the adapter command before swapping in the agent's isolated runtime.
        cmd = h.command(
            prompt,
            model=model,
            effort=effort,
            instructions=(project / "AGENTS.md").read_text(encoding="utf-8"),
        )
        with _isolated_nurb_environment(env, raw) as isolated_env:
            started = time.monotonic()
            with h.environment(isolated_env) as clean_env:
                returncode, stdout, stderr, timed_out = _invoke(
                    cmd, cwd=project, env=clean_env, timeout=timeout,
                )
        harness_s = round(time.monotonic() - started, 1)

        # A session the machine killed mid-run (an updater cycling instances, a
        # process reaper, a closed shell) measures the environment, not the model,
        # so it never becomes a row. Direct signal deaths report a negative code;
        # CLIs that catch the signal exit 128 plus its number. The runner's own
        # wall-clock kill is excluded: a timeout is deliberate and stays a row.
        if not timed_out and (returncode < 0 or returncode >= 128):
            grave = _grave(out / task_name, n)
            shutil.move(str(project), grave / "project")
            (grave / "transcript.txt").write_text(stdout, encoding="utf-8")
            raise HarnessKilled(
                f"{h.name} was killed mid-session (exit {returncode}); "
                f"the dead session is kept at {grave} and was not scored"
            )

        # The model must not run below the benchmark checkout, where walking to a
        # parent reveals the task scorer and reference solutions. Keep the resulting
        # project only after the harness exits so the audit artifact stays unchanged.
        slot.mkdir(parents=True)
        kept_project = slot / "project"
        shutil.move(str(project), kept_project)
        project = kept_project
    if timed_out:
        error = f"{h.name} hit the {timeout:.0f}s wall-clock cap"
    elif returncode != 0:
        tail = stderr.strip().splitlines()[-2:]
        error = f"{h.name} exited {returncode}: {' | '.join(tail)}"
    (slot / "transcript.txt").write_text(stdout, encoding="utf-8")

    part = project / part_file
    if part.is_file():
        verdict = grade.run(part, task_dir, seed)
    else:
        verdict = grade._failure(error or f"no part file at {part_file}")

    return {
        "task": task_name,
        "seed": seed,
        "trial": n,
        "harness": h.name,
        "harness_version": harnesses.version(h.name),
        "model": model,
        "effort": effort,
        **benchmark,
        "built": verdict["built"],
        "score": verdict["score"],
        "stages": verdict["stages"],
        "error": verdict["error"] or error,
        "harness_s": harness_s,
        "timeout_s": timeout,
        "usage": h.usage(stdout),
    }


def parser():
    ap = argparse.ArgumentParser(description="run one leaderboard row's trials")
    ap.add_argument("--harness", required=True, choices=sorted(harnesses.HARNESSES))
    ap.add_argument("--task", default="tasks/cable_clip")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--trials", type=_positive_int, default=3)
    ap.add_argument("--model", required=True)
    ap.add_argument("--effort", required=True)
    ap.add_argument("--timeout", type=float, default=3600.0)
    ap.add_argument("--out", default=None, help="defaults to results/<harness>-<model>-<effort>")
    return ap


def _positive_int(raw):
    value = int(raw)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def main():
    args = parser().parse_args()

    h = harnesses.HARNESSES[args.harness]
    label = "-".join(filter(None, (args.harness, args.model, args.effort)))
    out = pathlib.Path(args.out or f"results/{label}")
    out.mkdir(parents=True, exist_ok=True)

    scores = []
    with open(out / "results.jsonl", "a", encoding="utf-8") as sink:
        for n in range(1, args.trials + 1):
            row = completed_trial(
                h, args.task, args.seed, n, out,
                model=args.model, effort=args.effort, timeout=args.timeout,
            )
            sink.write(json.dumps(row) + "\n")
            sink.flush()
            scores.append(row["score"])
            print(f"trial {n}: score {row['score']:.3f}  stages {row['stages']}"
                  + (f"  ({row['error']})" if row["error"] else ""), flush=True)

    print(f"\n{label}: mean {sum(scores) / len(scores):.3f} over {len(scores)} trials, "
          f"pass@1 candidates {scores}", flush=True)


if __name__ == "__main__":
    main()
