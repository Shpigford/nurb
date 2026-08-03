"""Render the user-facing benchmarks page from the committed submissions.

REPORT.md is the audit trail; this page answers the only question a nurb user
actually has: which AI should I run this with, given what I subscribe to. Numbers
come from the same rows as the report so the two can never disagree; the verdict
sentences are editorial, keyed to a specific model and effort, and a row without a
verdict still renders with its numbers.

Written for people with printers, not programmers: jobs instead of tasks, first-try
prints instead of pass@1, minutes instead of tokens.
"""

import argparse
import html
import pathlib

from .report import PASS, rows_from, summarize

SITE = pathlib.Path(__file__).parents[3] / "site" / "benchmarks.html"
SUBMISSIONS = pathlib.Path(__file__).parents[2] / "submissions"

# What each benchmark job measures, in the words of the person printing the part.
JOBS = {
    "cable_clip": (
        "Follow the spec",
        "A cable clip with every dimension stated. Can it build exactly what you asked?",
    ),
    "bundle_holder": (
        "Design from a problem",
        "“Hold this cable bundle on the wall with one screw.” No shape given: it has to design one that works and prints.",
    ),
    "leg_cup": (
        "Handle a missing measurement",
        "One dimension nobody measured. Does it guess silently, or handle the unknown the honest way?",
    ),
}

# Editorial layer, keyed by (harness, model, effort). Grounded in the committed rows;
# update alongside them. Combos without an entry render numbers-only.
VERDICTS = {
    ("claude", "fable", "high"): (
        "Claude subscription",
        "Flawless so far: every part, every job, right the first time. When a measurement was missing, it did the honest thing unprompted. The premium pick.",
    ),
    ("claude", "opus", "high"): (
        "Claude subscription",
        "Also flawless, every part on every job, just slower than fable: it twice ran the clock out double-checking a part that was already perfect. If fable is not on your plan, this is the same answer with more patience required.",
    ),
    ("codex", "gpt-5.5", "medium"): (
        "ChatGPT subscription (Codex)",
        "Excellent and fast, and honest about the unmeasured dimension. One design quietly stopped fitting when the cable bundle grew, which is the kind of flaw you find after printing.",
    ),
    ("claude", "sonnet", "high"): (
        "Claude subscription",
        "Perfect on instructions and honest about the unmeasured dimension. Its own designs are the gap: elegant cradles that would fail on the printer, with big unsupported overhangs, one wall too thin, one that tips. Check its parts before printing.",
    ),
    ("claude", "haiku", "low"): (
        "Claude subscription (budget model)",
        "Fine when you spell everything out, and cheap. Asked to design, it produced parts you would not print: paper-thin walls, screw holes that are not round. And it wrote its guess for the unmeasured dimension down as if it had measured it, the mistake that ruins a print six months later.",
    ),
}

HEAD = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>nurb &middot; which AI designs the best parts?</title>
<meta name="description" content="The popular AI models, given the same real part-design jobs, graded by machine against print physics. Pick the one that fits your subscription.">
<style>
  @font-face {
    font-family: "JetBrains Mono";
    src: url(vendor/jetbrains-mono/JetBrainsMono-VariableFont_wght.ttf) format("truetype");
    font-weight: 100 800;
    font-display: swap;
  }
  :root {
    --bg: #16181d; --panel: #1d2027; --panel2: #191c22; --line: #2b2f38;
    --text: #e6e8ec; --dim: #868d9b; --dimmer: #565d6b;
    --accent: #6ee7a8; --amber: #f0c274; --bad: #f87171;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font: 15px/1.65 "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
    background: var(--bg); color: var(--text); -webkit-font-smoothing: antialiased;
  }
  ::selection { background: rgba(110,231,168,.25); }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  body::before {
    content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background:
      linear-gradient(rgba(110,231,168,.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(110,231,168,.035) 1px, transparent 1px);
    background-size: 44px 44px;
  }
  header { display: flex; align-items: baseline; gap: 1.5rem; padding: 1.4rem 2rem; border-bottom: 1px solid var(--line); }
  header b { color: var(--accent); }
  header nav { margin-left: auto; display: flex; gap: 1.2rem; }
  header nav a { color: var(--dim); }
  main { max-width: 880px; margin: 0 auto; padding: 3rem 1.5rem 4rem; }
  h1 { font-size: 1.7rem; line-height: 1.3; margin-bottom: .8rem; }
  .lead { color: var(--dim); margin-bottom: 2.5rem; }
  h2 { font-size: 1.05rem; margin: 2.8rem 0 1rem; color: var(--accent); }
  .jobs { display: grid; gap: .7rem; margin-bottom: .4rem; }
  .job { background: var(--panel2); border: 1px solid var(--line); border-radius: 8px; padding: .8rem 1rem; }
  .job b { display: block; }
  .job span { color: var(--dim); font-size: .88rem; }
  .card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
  .card .top { display: flex; flex-wrap: wrap; align-items: baseline; gap: .6rem 1rem; margin-bottom: .3rem; }
  .card .top .model { font-size: 1.15rem; font-weight: 700; }
  .card .top .runs { color: var(--dim); font-size: .85rem; }
  .card .top .first { margin-left: auto; font-size: .85rem; color: var(--dim); }
  .card .top .first b { color: var(--text); }
  .verdict { color: var(--dim); font-size: .92rem; margin-bottom: .9rem; }
  .bars { display: grid; grid-template-columns: max-content 1fr max-content; gap: .35rem .8rem; align-items: center; font-size: .85rem; }
  .bars .name { color: var(--dim); white-space: nowrap; }
  .bar { position: relative; height: 8px; background: var(--panel2); border: 1px solid var(--line); border-radius: 4px; }
  .bar i { display: block; height: 100%; background: var(--accent); border-radius: 3px; }
  .bar u { position: absolute; top: -3px; width: 2px; height: 12px; background: var(--text); opacity: .55; border-radius: 1px; }
  .bar i.mid { background: var(--amber); }
  .bar i.low { background: var(--bad); }
  .pct { text-align: right; min-width: 6.5ch; }
  .pct.na { color: var(--dimmer); }
  .fine { color: var(--dimmer); font-size: .82rem; margin-top: 1.1rem; }
  .fine:first-of-type { margin-top: 2.4rem; }
  .fine a { color: var(--dim); }
  .contribute { margin-top: 2.4rem; background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 1.1rem 1.3rem; }
  .contribute b { color: var(--accent); }
  .contribute code { display: block; margin-top: .6rem; background: var(--panel2); border: 1px solid var(--line); border-radius: 6px; padding: .55rem .8rem; overflow-x: auto; white-space: nowrap; }
  .contribute span { color: var(--dim); font-size: .88rem; }
  footer { border-top: 1px solid var(--line); padding: 1.4rem 2rem; display: flex; gap: 1.4rem; color: var(--dimmer); font-size: .85rem; }
</style>
</head>
<body>
<header>
  <a href="index.html"><b>nurb</b></a>
  <nav>
    <a href="index.html">home</a>
    <a href="https://github.com/Shpigford/nurb">github &nearr;</a>
  </nav>
</header>
<main>
<h1>Which AI designs the best parts?</h1>
<p class="lead">nurb works with the AI subscription you already have. We give each model the same real part-design jobs and grade the parts by machine: the actual geometry, checked against what was asked and against print physics. No cherry-picking, no vibes. Here is how they did.</p>

<h2>The jobs</h2>
<div class="jobs">
{jobs}
</div>

<h2>The models</h2>
{cards}

<div class="contribute">
  <b>Add your model to this page.</b>
  <span> One line, your own subscription, a wizard for the rest. A single run counts; it pools with everyone else's.</span>
  <code>curl -fsSL https://nurb.dev/bench.sh | sh</code>
  <span>Or paste that line to your AI and let it drive.</span>
</div>

<p class="fine">Early days: {trial_count} graded parts across {job_count} jobs. Each bar averages every attempt on file, and the ticks are the attempts themselves; a small sample should look like one.</p>
<p class="fine">Grading is a fixed rubric measured on the part's actual geometry, so the only randomness is the model's. Raw results, full transcripts, and the grading code are <a href="https://github.com/Shpigford/nurb/blob/main/evals/REPORT.md">on GitHub</a>.</p>
</main>
<footer>
  <a href="index.html">nurb.dev</a>
  <a href="https://github.com/Shpigford/nurb/blob/main/evals/REPORT.md">full results</a>
  <a href="https://github.com/Shpigford/nurb/issues/new">send feedback</a>
</footer>
</body>
</html>
"""


def _combos(summary):
    """Fold per-task rows into one entry per harness+model+effort, best score first."""
    combos = {}
    for row in summary:
        key = (row["harness"], row["model"], row["effort"])
        combos.setdefault(key, {})[row["task"]] = row
    order = []
    for key, tasks in combos.items():
        mean = sum(r["score"] for r in tasks.values()) / len(tasks)
        order.append((mean, key, tasks))
    order.sort(key=lambda item: -item[0])
    return [(key, tasks) for _, key, tasks in order]


def _bar(score, scores):
    """The bar is the mean; the ticks are the individual attempts. Three attempts is
    a small sample and the honest rendering shows all three instead of dressing
    their mean up as a precise percentage."""
    pct = round(score * 100)
    tone = "" if score >= 0.9 else " class=\"mid\"" if score >= 0.6 else " class=\"low\""
    ticks = "".join(
        f'<u style="left:calc({min(s * 100, 99.0):.1f}% - 1px)" title="attempt: {s:.3f}"></u>'
        for s in scores
    )
    return f'<div class="bar"><i{tone} style="width:{pct}%"></i>{ticks}</div><div class="pct">{pct}%</div>'


def _card(key, tasks):
    harness, model, effort = key
    runs_on, verdict = VERDICTS.get(
        key, (f"{harness} harness", "")
    )
    total = sum(r["trials"] for r in tasks.values())
    firsts = sum(sum(s >= PASS for s in r["scores"]) for r in tasks.values())
    minutes = sum(r["wall_s"] for r in tasks.values()) / len(tasks) / 60
    capped = sum(r.get("capped", 0) for r in tasks.values())
    # A capped trial was killed mid-session, so its duration is a floor: say so
    # instead of averaging kills in as if they were finishes.
    time_note = f"~{minutes:.0f} min/part"
    if capped:
        time_note = f"~{minutes:.0f}+ min/part (hit the 15 min limit on {capped})"
    bars = []
    for task in JOBS:
        name = html.escape(JOBS[task][0])
        row = tasks.get(task)
        if row is None:
            bars.append(
                f'<div class="name">{name}</div>'
                '<div class="bar"></div><div class="pct na">not yet run</div>'
            )
        else:
            bars.append(f'<div class="name">{name}</div>{_bar(row["score"], row["scores"])}')
    verdict_html = f'\n  <p class="verdict">{html.escape(verdict)}</p>' if verdict else ""
    return f"""<div class="card">
  <div class="top">
    <span class="model">{html.escape(model)} <small>({html.escape(effort)} effort)</small></span>
    <span class="runs">{html.escape(runs_on)}</span>
    <span class="first">first-try prints <b>{firsts}/{total}</b> &middot; {time_note}</span>
  </div>{verdict_html}
  <div class="bars">
    {"".join(bars)}
  </div>
</div>"""


def render(summary):
    jobs = "\n".join(
        f'<div class="job"><b>{html.escape(title)}</b><span>{html.escape(blurb)}</span></div>'
        for title, blurb in JOBS.values()
    )
    combos = _combos(summary)
    cards = "\n".join(_card(key, tasks) for key, tasks in combos)
    page = HEAD  # plain token replacement: the CSS is full of braces str.format would eat
    for token, value in (
        ("{jobs}", jobs),
        ("{cards}", cards),
        ("{trial_count}", str(sum(r["trials"] for r in summary))),
        ("{job_count}", str(len({r["task"] for r in summary}))),
    ):
        page = page.replace(token, value)
    return page


def main():
    ap = argparse.ArgumentParser(description="render site/benchmarks.html from submissions")
    ap.add_argument("results", nargs="*", help="results dirs; defaults to evals/submissions/*")
    ap.add_argument("--out", default=str(SITE))
    args = ap.parse_args()
    paths = args.results or sorted(
        str(p) for p in SUBMISSIONS.iterdir() if (p / "results.jsonl").is_file()
    )
    page = render(summarize(rows_from(paths)))
    pathlib.Path(args.out).write_text(page, encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
