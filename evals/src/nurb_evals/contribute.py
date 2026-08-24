"""The contribution wizard: one command from a person with a subscription to a
submission-ready leaderboard row.

Nobody should have to know that the harness spells its flagship "fable" or which
effort levels exist: the wizard detects the agent CLIs on PATH, offers a numbered
menu from the curated models.toml, runs the trials, sanitizes machine-specific paths
out of everything, stages the result under submissions/, and prints the two steps
that remain. Every question has a flag, so an agent can run it non-interactively:

    uv run python -m nurb_evals.contribute --harness claude --model claude-fable-5 --effort high
"""

import argparse
import getpass
import json
import pathlib
import re
import secrets
import shutil
import subprocess
import sys
import tomllib

from . import harness as harnesses
from .run import completed_trial

EVALS = pathlib.Path(__file__).parents[2]
TASKS = ("cable_clip", "bit_block", "bundle_holder", "pole_rest", "valve_knob", "leg_cup")
SEED = 13


def catalog():
    return tomllib.loads((EVALS / "models.toml").read_text(encoding="utf-8"))


def detected():
    """Harnesses actually on this machine, with versions."""
    out = []
    for name in sorted(harnesses.HARNESSES):
        if shutil.which(name):
            out.append((name, harnesses.version(name)))
    return out


def flagship(name):
    """The harness CLI's own top-listed model, for the staleness nudge: catalogs
    list newest first, so a curated menu missing the top entry is out of date.
    Older tiers we deliberately leave off the menu never trigger it. Best-effort:
    claude has no list command, and any failure just skips the nudge."""
    probes = {"codex": ["codex", "debug", "models"], "grok": ["grok", "models"]}
    cmd = probes.get(name)
    if not cmd:
        return None
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    if name == "codex":
        try:
            data = json.loads(out[out.index("{"):])
        except ValueError:
            return None
        for m in data.get("models", []):
            if m.get("visibility") == "list" and m.get("slug"):
                return m["slug"]
        return None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith(("*", "-")):
            return line.lstrip("*- ").split()[0]
    return None


def ask(prompt, options, default=None):
    """A numbered menu. Options are (value, label); returns the value."""
    print()
    for i, (_, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    hint = f" [{default}]" if default else ""
    while True:
        try:
            raw = input(f"{prompt}{hint}: ").strip()
        except EOFError:
            sys.exit(
                "\nNo terminal to ask on. Pass flags instead: "
                "--harness, --model, --effort (see --help)."
            )
        if not raw and default is not None:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1][0]
        print(f"  pick a number between 1 and {len(options)}")


def replacements(project_root):
    """Machine-specific strings that must not reach a public submission, longest
    first so nested paths collapse cleanly."""
    home = str(pathlib.Path.home())
    pairs = [(str(project_root), "<workspace>"), (str(EVALS), "<repo>"), (home, "<home>")]
    user = getpass.getuser()
    if user and len(user) > 2:
        pairs.append((user, "<user>"))
    return sorted(pairs, key=lambda p: -len(p[0]))


# grok's transcript repeats every tool result as a raw byte array next to the
# sanitized text, and paths hide from string replacement inside the integers.
_BYTE_ARRAY = re.compile(r'"output":\[[0-9,]+\]')


def sanitize(text, pairs):
    text = _BYTE_ARRAY.sub('"output":[]', text)
    for needle, token in pairs:
        text = text.replace(needle, token)
    return text


def stage_submission(out, label, task, n):
    """Copy one trial's auditable artifacts into submissions/, sanitized."""
    src = out / task / f"trial_{n}"
    dst = EVALS / "submissions" / label / task / f"trial_{n}"
    (dst / "project" / "parts").mkdir(parents=True, exist_ok=True)
    pairs = replacements(src / "project")
    transcript = (src / "transcript.txt").read_text(encoding="utf-8", errors="replace")
    (dst / "transcript.txt").write_text(sanitize(transcript, pairs), encoding="utf-8")
    for source in sorted((src / "project" / "parts").glob("*.py")):
        text = source.read_text(encoding="utf-8", errors="replace")
        (dst / "project" / "parts" / source.name).write_text(
            sanitize(text, pairs), encoding="utf-8"
        )
    book = src / "project" / "measurements.toml"
    if book.is_file():
        (dst / "project" / "measurements.toml").write_text(
            sanitize(book.read_text(encoding="utf-8"), pairs), encoding="utf-8"
        )
    return dst


def next_trial(out, task):
    """Continue numbering after earlier local runs instead of refusing the slot."""
    n = 1
    while (out / task / f"trial_{n}").exists():
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="run and stage a leaderboard contribution")
    ap.add_argument("--harness", choices=sorted(harnesses.HARNESSES))
    ap.add_argument("--model")
    ap.add_argument("--effort")
    ap.add_argument(
        "--trials",
        type=int,
        default=None,
        help="rounds per job; the wizard asks when omitted (default there: 1)",
    )
    ap.add_argument("--tasks", default=",".join(TASKS), help="comma-separated, default all")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--timeout", type=float, default=3600.0)
    ap.add_argument(
        "--pr",
        choices=("ask", "yes", "no"),
        default="ask",
        help="open the pull request automatically (default: ask)",
    )
    args = ap.parse_args()

    print("\nnurb benchmark contribution\n———————————————————————————")
    if args.harness:
        name = args.harness
    else:
        have = detected()
        if not have:
            sys.exit(
                "No supported agent CLI found on PATH. Install claude "
                "(https://claude.com/claude-code), codex (https://openai.com/codex), "
                "or grok (https://x.ai), sign in, and rerun."
            )
        name = ask(
            "Which AI do you want to benchmark", [(n, f"{n} ({v})") for n, v in have],
            default=have[0][0] if len(have) == 1 else None,
        )
    if not shutil.which(name):
        sys.exit(f"{name} is not on PATH on this machine.")

    menu = catalog().get(name, [])
    newest = flagship(name)
    if newest and newest not in {m["id"] for m in menu}:
        print(f"\n  note: {name} now lists {newest}, which models.toml does not "
              f"offer yet; pick \"another model\" to run it, and consider a PR "
              f"updating the menu.")
    if args.model:
        model, efforts, default_effort = args.model, [], args.effort or "high"
        entry = next((m for m in menu if m["id"] == args.model), None)
        if entry:
            efforts, default_effort = entry["efforts"], entry["default_effort"]
    else:
        options = [(m, m["label"]) for m in menu] + [(None, "another model (type its id)")]
        entry = ask("Which model", options)
        if entry is None:
            try:
                model = input("model id exactly as the CLI accepts it: ").strip()
            except EOFError:
                sys.exit("\nNo terminal to ask on; pass --model.")
            efforts, default_effort = [], "high"
        else:
            model, efforts, default_effort = entry["id"], entry["efforts"], entry["default_effort"]

    effort = args.effort or (
        ask("Thinking effort", [(e, e) for e in efforts], default=default_effort)
        if efforts
        else default_effort
    )

    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]

    # Rounds are the sample size: scores vary run to run, and the leaderboard pools
    # every submitted trial, so more rounds tighten this model's number. The wizard
    # says why so the choice is informed, not a magic knob. Scripted runs (no
    # terminal) keep the old behavior: one round unless --trials says otherwise.
    if args.trials is None and not sys.stdin.isatty():
        trials = 1
    elif args.trials is None:
        print(
            "\nEach round is one fresh attempt at every job. Scores vary between"
            "\nattempts, so more rounds mean a steadier average on the leaderboard;"
            "\none round is still a valid contribution, and later runs pool with it."
            f"\nBallpark {len(tasks) * 8} minutes of agent time per round."
        )
        trials = ask(
            "How many rounds",
            [
                (1, "1 round: a quick single sample"),
                (3, "3 rounds: a steady average"),
                (5, "5 rounds: tight error bars"),
                (None, "another number (type it)"),
            ],
            default=1,
        )
        if trials is None:
            try:
                trials = int(input("rounds: ").strip() or "1")
            except (EOFError, ValueError):
                sys.exit("\nCould not read a number; pass --trials instead.")
    else:
        trials = args.trials
    if trials < 1:
        sys.exit("--trials must be at least 1")
    # Every run gets its own directory, branch, and PR: the same person running the
    # same combo ten times, or in three sessions at once, produces ten independent
    # pure-addition PRs that merge in any order with zero conflicts. Matching rows
    # pool by identity no matter which directory they arrive in.
    run_id = secrets.token_hex(3)
    label = f"{name}-{model}-{effort}"
    run_name = f"{label}-{run_id}"
    out = EVALS / "results" / run_name
    out.mkdir(parents=True, exist_ok=True)
    minutes = len(tasks) * trials * 8
    print(
        f"\nRunning {model} at {effort} effort: {trials} round(s) on "
        f"{len(tasks)} job(s), on your own {name} subscription. Ballpark "
        f"{minutes} minutes of agent time; slow models can take much longer.\n"
    )

    h = harnesses.HARNESSES[name]
    staged = []
    with open(out / "results.jsonl", "a", encoding="utf-8") as sink:
        for task in tasks:
            for _ in range(trials):
                n = next_trial(out, task)
                print(f"[{task} trial {n}] running...", flush=True)
                row = completed_trial(
                    h, EVALS / "tasks" / task, args.seed, n, out,
                    model=model, effort=effort, timeout=args.timeout,
                )
                sink.write(json.dumps(row) + "\n")
                sink.flush()
                note = f"  ({row['error']})" if row["error"] else ""
                print(f"[{task} trial {n}] score {row['score']:.3f}{note}", flush=True)
                staged.append(stage_submission(out, run_name, task, n))

    # The staged submission needs the matching rows; sanitize the whole file so a
    # custom --out or odd path never leaks through a row's error string.
    pairs = replacements(out)
    rows_text = (out / "results.jsonl").read_text(encoding="utf-8")
    sub = EVALS / "submissions" / run_name
    (sub / "results.jsonl").write_text(sanitize(rows_text, pairs), encoding="utf-8")

    leak = re.compile(re.escape(str(pathlib.Path.home())) + r"|" + re.escape(getpass.getuser()))
    dirty = [
        p
        for p in sub.rglob("*")
        if p.is_file() and leak.search(p.read_text(encoding="utf-8", errors="replace"))
    ]
    if dirty:
        sys.exit(f"sanitizer missed something in {dirty[0]}; please open an issue instead of a PR")

    # The submission is deliberately a pure addition: one new directory, nothing
    # shared touched. REPORT.md and the page regenerate on main after merge (the
    # leaderboard workflow), so any number of open submission PRs merge in any
    # order without a conflict.
    repo = EVALS.parent
    print(f"\nDone. Staged in this checkout ({repo}):\n  {sub}\n")

    # Handing a contributor five git commands is where two dogfooding runs died
    # (wrong checkout, stale branch, accidental nested-repo add). The wizard owns
    # the whole submission: it knows the right checkout because it is standing in it.
    want = args.pr
    if want == "ask":
        if _gh_ready(repo):
            try:
                raw = input("Open the pull request now? [Y/n]: ").strip().lower()
                want = "no" if raw in ("n", "no") else "yes"
            except EOFError:
                want = "no"
        else:
            print("GitHub CLI (gh) not found or not signed in; printing the manual steps.")
            want = "no"
    if want == "yes":
        url, problem = open_pr(run_name, repo)
        if url:
            print(
                f"\nSubmitted: {url}\n\n"
                f"Every run counts, including a single one: matching rows pool on the "
                f"leaderboard, and a bad score is data, not an embarrassment. Run it "
                f"again whenever you like; every run is its own PR."
            )
            return
        print(f"\nCould not open the PR automatically ({problem}); the manual steps:")
    _manual_steps(run_name, repo)


def _gh_ready(repo):
    if not shutil.which("gh"):
        return False
    return _run(["gh", "auth", "status"], repo).returncode == 0


def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _tail(done):
    text = (done.stderr or done.stdout or "").strip()
    return text.splitlines()[-1] if text else f"exit {done.returncode}"


def open_pr(run_name, repo):
    """Branch, commit, push, and open the PR from the wizard's own checkout,
    forking first only when push access is missing. The branch is unique per run
    and carries only this run's directory, branched from origin's main, so any
    number of runs from any number of sessions produce independent PRs that merge
    in any order. Returns (url, None) or (None, what went wrong)."""
    branch = f"bench-{run_name}"
    base = ["-b", branch]
    if _run(["git", "fetch", "origin", "main"], repo).returncode == 0:
        base += ["FETCH_HEAD"]
    done = _run(["git", "checkout", *base], repo)
    if done.returncode != 0:
        return None, f"git checkout: {_tail(done)}"

    _run(["git", "add", f"evals/submissions/{run_name}"], repo)
    done = _run(["git", "commit", "-m", f"benchmark run: {run_name}"], repo)
    if done.returncode != 0:
        return None, f"git commit: {_tail(done)}"

    head = branch
    push = _run(["git", "push", "-u", "origin", branch], repo)
    if push.returncode != 0:
        fork = _run(["gh", "repo", "fork", "--remote", "--remote-name", "fork"], repo)
        if fork.returncode != 0:
            return None, f"gh repo fork: {_tail(fork)}"
        push = _run(["git", "push", "-u", "fork", branch], repo)
        if push.returncode != 0:
            return None, f"git push: {_tail(push)}"
        login = _run(["gh", "api", "user", "-q", ".login"], repo)
        if login.returncode == 0 and login.stdout.strip():
            head = f"{login.stdout.strip()}:{branch}"

    # --base and --head make pr create fully non-interactive: without them gh can
    # decide it has a question to ask, and a question with no terminal is an abort
    # (a dogfooding run died exactly there, one step from the URL).
    done = _run(
        [
            "gh", "pr", "create",
            "--repo", "Shpigford/nurb",
            "--base", "main",
            "--head", head,
            "--title", f"benchmark run: {run_name}",
            "--body",
            "Automated submission from the contribute wizard: one run, one new "
            "directory, nothing shared touched. Matching rows pool on the "
            "leaderboard, and the report and page regenerate on main after merge.",
        ],
        repo,
    )
    if done.returncode != 0:
        return None, f"gh pr create: {_tail(done)}"
    return done.stdout.strip().splitlines()[-1], None


def _manual_steps(run_name, repo):
    print(
        f"\nFrom {repo}:\n"
        f"  git checkout -b bench-{run_name}\n"
        f"  git add evals/submissions/{run_name}\n"
        f"  git commit -m 'benchmark run: {run_name}'\n"
        f"  gh repo fork Shpigford/nurb --remote   # skip if you have push access\n"
        f"  git push -u origin bench-{run_name}\n"
        f"  gh pr create --repo Shpigford/nurb --base main --head bench-{run_name} --title 'benchmark run: {run_name}' --fill\n\n"
        f"Every run counts, including a single one: matching rows pool on the "
        f"leaderboard, and a bad score is data, not an embarrassment."
    )


if __name__ == "__main__":
    main()
