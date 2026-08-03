"""The contribution wizard: one command from a person with a subscription to a
submission-ready leaderboard row.

Nobody should have to know that the harness spells its flagship "fable" or which
effort levels exist: the wizard detects the agent CLIs on PATH, offers a numbered
menu from the curated models.toml, runs the trials, sanitizes machine-specific paths
out of everything, stages the result under submissions/, and prints the two steps
that remain. Every question has a flag, so an agent can run it non-interactively:

    uv run python -m nurb_evals.contribute --harness claude --model fable --effort high
"""

import argparse
import getpass
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tomllib

from . import harness as harnesses
from .run import trial

EVALS = pathlib.Path(__file__).parents[2]
TASKS = ("cable_clip", "bundle_holder", "leg_cup")
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


def sanitize(text, pairs):
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
    ap.add_argument("--trials", type=int, default=1)
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
                "(https://claude.com/claude-code) or codex (https://openai.com/codex), "
                "sign in, and rerun."
            )
        name = ask(
            "Which AI do you want to benchmark", [(n, f"{n} ({v})") for n, v in have],
            default=have[0][0] if len(have) == 1 else None,
        )
    if not shutil.which(name):
        sys.exit(f"{name} is not on PATH on this machine.")

    menu = catalog().get(name, [])
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
    label = f"{name}-{model}-{effort}"
    out = EVALS / "results" / label
    out.mkdir(parents=True, exist_ok=True)
    minutes = len(tasks) * args.trials * 8
    print(
        f"\nRunning {model} at {effort} effort: {args.trials} trial(s) on "
        f"{len(tasks)} job(s), on your own {name} subscription. Ballpark "
        f"{minutes} minutes of agent time; slow models can take much longer.\n"
    )

    h = harnesses.HARNESSES[name]
    staged = []
    with open(out / "results.jsonl", "a", encoding="utf-8") as sink:
        for task in tasks:
            for _ in range(args.trials):
                n = next_trial(out, task)
                print(f"[{task} trial {n}] running...", flush=True)
                row = trial(
                    h, EVALS / "tasks" / task, args.seed, n, out,
                    model=model, effort=effort, timeout=args.timeout,
                )
                sink.write(json.dumps(row) + "\n")
                sink.flush()
                note = f"  ({row['error']})" if row["error"] else ""
                print(f"[{task} trial {n}] score {row['score']:.3f}{note}", flush=True)
                staged.append(stage_submission(out, label, task, n))

    # The staged submission needs the matching rows; sanitize the whole file so a
    # custom --out or odd path never leaks through a row's error string.
    pairs = replacements(out)
    rows_text = (out / "results.jsonl").read_text(encoding="utf-8")
    sub = EVALS / "submissions" / label
    (sub / "results.jsonl").write_text(sanitize(rows_text, pairs), encoding="utf-8")

    leak = re.compile(re.escape(str(pathlib.Path.home())) + r"|" + re.escape(getpass.getuser()))
    dirty = [
        p
        for p in sub.rglob("*")
        if p.is_file() and leak.search(p.read_text(encoding="utf-8", errors="replace"))
    ]
    if dirty:
        sys.exit(f"sanitizer missed something in {dirty[0]}; please open an issue instead of a PR")

    # The published page regenerates here, not as a step the contributor has to
    # remember: the submission ships with the benchmarks.html it produces, so the
    # stale-page test passes on the PR as opened.
    from . import report as report_module
    from . import site as site_module

    paths = sorted(
        str(p) for p in (EVALS / "submissions").iterdir() if (p / "results.jsonl").is_file()
    )
    site_module.SITE.write_text(
        site_module.render(site_module.summarize(site_module.rows_from(paths))),
        encoding="utf-8",
    )
    report_module.write(EVALS / "submissions", EVALS / "REPORT.md")

    repo = EVALS.parent
    print(
        f"\nDone. Staged in this checkout ({repo}):\n"
        f"  {sub}\n"
        f"  {site_module.SITE}\n"
        f"  {EVALS / 'REPORT.md'}\n"
    )

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
        url, problem = open_pr(label, repo)
        if url:
            print(
                f"\nSubmitted: {url}\n\n"
                f"Every run counts, including a single one: matching rows pool on the "
                f"leaderboard, and a bad score is data, not an embarrassment."
            )
            return
        print(f"\nCould not open the PR automatically ({problem}); the manual steps:")
    _manual_steps(label, repo)


def _gh_ready(repo):
    if not shutil.which("gh"):
        return False
    return _run(["gh", "auth", "status"], repo).returncode == 0


def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _tail(done):
    text = (done.stderr or done.stdout or "").strip()
    return text.splitlines()[-1] if text else f"exit {done.returncode}"


def open_pr(label, repo):
    """Branch, commit, push, and open the PR from the wizard's own checkout,
    forking first only when push access is missing. Re-running the same label
    appends to the same branch, which updates the same PR: that is how one
    contributor's runs pool. Returns (url, None) or (None, what went wrong)."""
    branch = f"bench-{label}"
    if _run(["git", "rev-parse", "--verify", branch], repo).returncode == 0:
        done = _run(["git", "checkout", branch], repo)
    else:
        done = _run(["git", "checkout", "-b", branch], repo)
    if done.returncode != 0:
        return None, f"git checkout: {_tail(done)}"

    _run(["git", "add", "evals/submissions", "evals/REPORT.md", "site/benchmarks.html"], repo)
    done = _run(["git", "commit", "-m", f"benchmark row: {label}"], repo)
    if done.returncode != 0 and "nothing to commit" not in (done.stdout + done.stderr):
        return None, f"git commit: {_tail(done)}"

    push = _run(["git", "push", "-u", "origin", branch], repo)
    if push.returncode != 0:
        fork = _run(["gh", "repo", "fork", "--remote", "--remote-name", "fork"], repo)
        if fork.returncode != 0:
            return None, f"gh repo fork: {_tail(fork)}"
        push = _run(["git", "push", "-u", "fork", branch], repo)
        if push.returncode != 0:
            return None, f"git push: {_tail(push)}"

    done = _run(
        [
            "gh", "pr", "create",
            "--title", f"benchmark row: {label}",
            "--body",
            "Automated submission from the contribute wizard. Matching rows pool on "
            "the leaderboard; transcripts, parts, and the regenerated report and "
            "page are included.",
        ],
        repo,
    )
    if done.returncode == 0:
        return done.stdout.strip().splitlines()[-1], None
    # A PR for this branch may already exist from an earlier run of the same label.
    view = _run(["gh", "pr", "view", branch, "--json", "url", "-q", ".url"], repo)
    if view.returncode == 0 and view.stdout.strip():
        return view.stdout.strip(), None
    return None, f"gh pr create: {_tail(done)}"


def _manual_steps(label, repo):
    print(
        f"\nFrom {repo}:\n"
        f"  git checkout -b bench-{label}   # or 'git checkout bench-{label}' if it exists\n"
        f"  git add evals/submissions evals/REPORT.md site/benchmarks.html\n"
        f"  git commit -m 'benchmark row: {label}'\n"
        f"  gh repo fork Shpigford/nurb --remote   # skip if you have push access\n"
        f"  git push -u origin bench-{label}\n"
        f"  gh pr create --title 'benchmark row: {label}' --fill\n\n"
        f"Every run counts, including a single one: matching rows pool on the "
        f"leaderboard, and a bad score is data, not an embarrassment."
    )


if __name__ == "__main__":
    main()
