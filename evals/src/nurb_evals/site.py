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
import math
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
    "bit_block": (
        "Survive the kernel",
        "A bit block dense with chamfers, right at the CAD kernel's limits. One wrong move and the part never builds.",
    ),
    "bundle_holder": (
        "Design from a problem",
        "“Hold this cable bundle on the wall with one screw.” No shape given: it has to design one that works and prints.",
    ),
    "pole_rest": (
        "Design a curve",
        "A rest that must cradle a measured pole along a real arc. Flat answers touch at lines and lose; only curvature passes.",
    ),
    "valve_knob": (
        "Make it fit",
        "A knob for a measured D-shaft. The grader drives the real stem: too tight jams, too loose rattles, a round bore spins.",
    ),
    "leg_cup": (
        "Handle a missing measurement",
        "One dimension nobody measured. Does it guess silently, or handle the unknown the honest way?",
    ),
}

# Subscriptions are the constraint a visitor arrives with, so they partition the
# page (the answer cards) and color the chart. Chart identity colors are validated
# for the dark surface and deliberately distinct from the score bars' status
# colors: green/amber/red mean good/mid/poor everywhere on this page, never "which
# subscription".
SUBSCRIPTIONS = {
    "claude": ("Claude", "#2f9fb5"),
    "codex": ("ChatGPT (Codex)", "#8f75e0"),
}

# One line of honest nuance under the answer cards; editorial, updated with the data.
GAP_NOTE = (
    "In a hurry on a Claude plan? No fast Claude option has been benchmarked yet: "
    "every Claude row so far ran at its usual effort. Lower-effort rows are next, "
    "and the chart below will grow a line per model as they land."
)

# Editorial layer, keyed by (harness, model, effort). Grounded in the committed rows;
# update alongside them. Combos without an entry render numbers-only.
VERDICTS = {
    ("claude", "fable", "high"): (
        "Claude subscription",
        "Flawless so far: every part, every job, right the first time. When a measurement was missing, it did the honest thing unprompted. The premium pick.",
    ),
    ("claude", "opus", "high"): (
        "Claude subscription",
        "Flawless on everything it has rows for, a notch slower than fable. Its design-job row is being re-run under a longer session limit after the old limit cut its trials short; the numbers here are only from completed sessions.",
    ),
    ("codex", "gpt-5.5", "medium"): (
        "ChatGPT subscription (Codex)",
        "Excellent and fast, and honest about the unmeasured dimension. One design quietly stopped fitting when the cable bundle grew, which is the kind of flaw you find after printing.",
    ),
    ("claude", "sonnet", "high"): (
        "Claude subscription",
        "Perfect on instructions and honest about the unmeasured dimension, but slow. Its design-job trials all ran past the old session limit and were graded mid-thought, which is not a fair grade in either direction, so that row was thrown out and is being re-run with a longer limit.",
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
  .answers { display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; }
  @media (max-width: 640px) { .answers { grid-template-columns: 1fr; } }
  .answer { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.2rem; border-top: 3px solid var(--line); }
  .answer .have { font-size: .85rem; color: var(--dim); }
  .answer .pick { font-size: 1.15rem; font-weight: 700; margin: .15rem 0; }
  .answer .pick small { color: var(--dim); font-weight: 400; font-size: .8em; }
  .answer .why { color: var(--dim); font-size: .88rem; }
  .gap { color: var(--dimmer); font-size: .82rem; margin-top: .8rem; }
  .chart-lead { color: var(--dim); font-size: .88rem; margin-bottom: .8rem; }
  .chart { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: .6rem; }
  .chart svg { display: block; width: 100%; height: auto; }
  .chart-legend { display: flex; flex-wrap: wrap; gap: .4rem 1.4rem; padding: .55rem .6rem .3rem; border-top: 1px solid var(--line); margin-top: .4rem; font-size: .8rem; color: var(--dim); }
  .chart-legend span { display: inline-flex; align-items: center; gap: .45rem; }
  .chart-legend i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .chart-legend b { font-weight: 400; color: var(--text); }
  .chart .dot { transition: r .1s; }
  .chart .dot:hover { r: 8; }
  .card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 0 1.4rem; margin-bottom: .7rem; }
  .card summary { cursor: pointer; list-style: none; padding: 1rem 0; }
  .card summary::-webkit-details-marker { display: none; }
  .card summary::after { content: "+"; float: right; color: var(--dimmer); }
  .card[open] summary::after { content: "\\2212"; }
  .card .body { padding-bottom: 1.2rem; }
  .card .top { display: flex; flex-wrap: wrap; align-items: baseline; gap: .6rem 1rem; }
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
<p class="lead">nurb works with the AI subscription you already have. We give each model the same real part-design jobs and grade the parts by machine: the actual geometry, checked against what was asked and against print physics. No cherry-picking, no vibes. Start from what you subscribe to.</p>

<h2>The short answer</h2>
<div class="answers">
{answers}
</div>
<p class="gap">{gap_note}</p>

<h2>The tradeoff</h2>
<p class="chart-lead">Every benchmarked model and effort level, placed by how often its parts print right the first time against how long it takes per part. Up and to the left is better.</p>
{chart}

<h2>The jobs</h2>
<div class="jobs">
{jobs}
</div>

<h2>The receipts</h2>
<p class="chart-lead">Per-model detail: the verdict, and every job's score with a tick per attempt. Click a model to open it.</p>
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


def _stats(tasks):
    """The numbers a combo is judged by, shared by every layer of the page."""
    total = sum(r["trials"] for r in tasks.values())
    firsts = sum(sum(s >= PASS for s in r["scores"]) for r in tasks.values())
    minutes = sum(r["wall_s"] for r in tasks.values()) / len(tasks) / 60
    capped = sum(r.get("capped", 0) for r in tasks.values())
    costs = [r.get("cost") for r in tasks.values()]
    dollars = sum(costs) / len(costs) if all(c is not None for c in costs) else None
    return firsts, total, minutes, capped, dollars


def _cost_note(dollars):
    """Dollars per part, or nothing when a harness never reported enough to price.
    API-equivalent at list prices: the subscription paid no invoice, this is what
    the same tokens would have cost through the API."""
    if dollars is None:
        return ""
    figure = f"${dollars:.2f}" if dollars >= 0.10 else f"${dollars:.3f}"
    return f" &middot; ~{figure}/part at API rates"


def _time_note(minutes, capped):
    # A capped trial was killed mid-session, so its duration is a floor: say so
    # instead of averaging kills in as if they were finishes.
    if capped:
        return f"~{minutes:.0f}+ min/part (hit the time limit on {capped})"
    return f"~{minutes:.0f} min/part"


def _answers(combos):
    """One card per subscription: the best combo for the plan the visitor already
    pays for, because the subscription is a constraint, not a tradeoff axis."""
    best = {}
    for key, tasks in combos:
        harness = key[0]
        firsts, total, minutes, capped, dollars = _stats(tasks)
        rank = (firsts / total if total else 0, -minutes)
        if harness not in best or rank > best[harness][0]:
            best[harness] = (rank, key, (firsts, total, minutes, capped, dollars))
    cards = []
    for harness, (label, color) in SUBSCRIPTIONS.items():
        if harness not in best:
            continue
        _, (h, model, effort), (firsts, total, minutes, capped, dollars) = best[harness]
        cards.append(
            f'<div class="answer" style="border-top-color:{color}">\n'
            f'  <div class="have">Have {html.escape(label)}?</div>\n'
            f'  <div class="pick">run {html.escape(model)} <small>at {html.escape(effort)} effort</small></div>\n'
            f'  <div class="why">{firsts}/{total} first-try prints &middot; '
            f"{_time_note(minutes, capped)}{_cost_note(dollars)}</div>\n"
            f"</div>"
        )
    return "\n".join(cards)


def _chart(combos):
    """One inline SVG: first-try rate against minutes per part, a labeled dot per
    combo, colored by subscription. Effort variants of the same model connect into
    a line as they land, so the two knobs read as geometry: pick a model's line,
    slide along it for effort. Capped combos carry a right arrow: their time is a
    floor, not a measurement."""
    width, height = 840, 380
    left, right, top, bottom = 56, 24, 26, 46
    pw, ph = width - left - right, height - top - bottom

    points = []
    for (harness, model, effort), tasks in combos:
        firsts, total, minutes, capped, dollars = _stats(tasks)
        points.append(
            {
                "harness": harness,
                "model": model,
                "effort": effort,
                "rate": firsts / total if total else 0.0,
                "minutes": minutes,
                "capped": capped,
                "dollars": dollars,
                "firsts": firsts,
                "total": total,
            }
        )
    xmax = max(12.0, max(p["minutes"] for p in points) * 1.2)
    xmax = math.ceil(xmax / 3) * 3

    def sx(minutes):
        return left + minutes / xmax * pw

    def sy(rate):
        return top + (1 - rate) * ph

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="First-try prints against minutes per part for every benchmarked model">'
    ]
    for rate in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = sy(rate)
        parts.append(
            f'<line x1="{left}" y1="{y:.0f}" x2="{width - right}" y2="{y:.0f}" stroke="var(--line)" stroke-width="1"/>'
            f'<text x="{left - 8}" y="{y + 4:.0f}" text-anchor="end" font-size="11" fill="var(--dimmer)">{rate * 100:.0f}%</text>'
        )
    tick = 3
    for m in range(tick, int(xmax) + 1, tick):
        x = sx(m)
        parts.append(
            f'<line x1="{x:.0f}" y1="{top}" x2="{x:.0f}" y2="{height - bottom}" stroke="var(--line)" stroke-width="1" stroke-dasharray="2 5"/>'
            f'<text x="{x:.0f}" y="{height - bottom + 18}" text-anchor="middle" font-size="11" fill="var(--dimmer)">{m}</text>'
        )
    parts.append(
        f'<text x="{width - right}" y="{height - 8}" text-anchor="end" font-size="11" fill="var(--dim)">minutes per part &rarr;</text>'
        f'<text x="{left - 42}" y="{top - 10}" font-size="11" fill="var(--dim)">printed right first try</text>'
    )

    # Effort variants of one model join into a line once more than one is on file.
    by_model = {}
    for p in points:
        by_model.setdefault((p["harness"], p["model"]), []).append(p)
    for (harness, _), group in by_model.items():
        if len(group) > 1:
            color = SUBSCRIPTIONS.get(harness, ("", "var(--dim)"))[1]
            path = " ".join(
                f"{'M' if i == 0 else 'L'} {sx(p['minutes']):.0f} {sy(p['rate']):.0f}"
                for i, p in enumerate(sorted(group, key=lambda p: p["minutes"]))
            )
            parts.append(
                f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" opacity=".35"/>'
            )

    for p in points:
        x, y = sx(p["minutes"]), sy(p["rate"])
        color = SUBSCRIPTIONS.get(p["harness"], ("", "var(--dim)"))[1]
        # Label side: flip left near the right edge or when a same-height neighbor
        # sits close to the right; ink color, never the series color.
        crowd = any(
            q is not p
            and abs(sy(q["rate"]) - y) < 16
            and 0 < sx(q["minutes"]) - x < 170
            for q in points
        )
        flip = crowd or x > width - right - 140
        # A capped point owns the space to its right (the floor arrow lives there),
        # so its label starts past the arrowhead.
        anchor, lx = ("end", x - 12) if flip else ("start", x + (34 if p["capped"] else 12))
        title = (
            f"{p['model']} ({p['effort']} effort): {p['firsts']}/{p['total']} first-try, "
            f"{_time_note(p['minutes'], p['capped'])}"
            f"{_cost_note(p['dollars']).replace('&middot;', '·')}"
        )
        if p["capped"]:
            parts.append(
                f'<line x1="{x + 8:.0f}" y1="{y:.0f}" x2="{x + 22:.0f}" y2="{y:.0f}" stroke="{color}" stroke-width="2"/>'
                f'<path d="M {x + 22:.0f} {y - 4:.0f} L {x + 29:.0f} {y:.0f} L {x + 22:.0f} {y + 4:.0f} Z" fill="{color}"/>'
            )
        parts.append(
            f'<circle class="dot" cx="{x:.0f}" cy="{y:.0f}" r="6" fill="{color}" stroke="var(--panel)" stroke-width="2">'
            f"<title>{html.escape(title)}</title></circle>"
            f'<text x="{lx:.0f}" y="{y + 4:.0f}" text-anchor="{anchor}" font-size="12" fill="var(--text)">'
            f'{html.escape(p["model"])} <tspan fill="var(--dimmer)">&middot; {html.escape(p["effort"])}</tspan></text>'
        )

    parts.append("</svg>")

    # The legend lives outside the plot, or its swatches read as data points; the
    # floor-arrow key lives with it, or the arrow reads as decoration.
    capped_any = any(p["capped"] for p in points)
    keys = [
        f'<span><i style="background:{color}"></i>{html.escape(label)}</span>'
        for label, color in SUBSCRIPTIONS.values()
    ]
    if capped_any:
        keys.append(
            "<span><b>&rarr;</b>hit the session time limit, so the real time is longer than shown</span>"
        )
    legend = f'<div class="chart-legend">{"".join(keys)}</div>'
    return '<div class="chart">' + "".join(parts) + legend + "</div>"


def _card(key, tasks):
    harness, model, effort = key
    runs_on, verdict = VERDICTS.get(key, (f"{harness} harness", ""))
    firsts, total, minutes, capped, dollars = _stats(tasks)
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
    return f"""<details class="card">
  <summary><div class="top">
    <span class="model">{html.escape(model)} <small>({html.escape(effort)} effort)</small></span>
    <span class="runs">{html.escape(runs_on)}</span>
    <span class="first">first-try prints <b>{firsts}/{total}</b> &middot; {_time_note(minutes, capped)}{_cost_note(dollars)}</span>
  </div></summary>
  <div class="body">{verdict_html}
  <div class="bars">
    {"".join(bars)}
  </div>
  </div>
</details>"""


def render(summary):
    jobs = "\n".join(
        f'<div class="job"><b>{html.escape(title)}</b><span>{html.escape(blurb)}</span></div>'
        for title, blurb in JOBS.values()
    )
    combos = _combos(summary)
    if combos:
        answers = _answers(combos)
        gap = html.escape(GAP_NOTE)
        chart = _chart(combos)
        cards = "\n".join(_card(key, tasks) for key, tasks in combos)
    else:
        answers = (
            '<div class="answer"><div class="have">No rows on file yet</div>'
            '<div class="pick">be the first</div>'
            '<div class="why">the one-liner below runs the benchmark on your own subscription and stages a submission</div></div>'
        )
        gap = ""
        chart = '<p class="chart-lead">The chart appears with the first submitted rows.</p>'
        cards = '<p class="chart-lead">Nothing yet.</p>'
    page = HEAD  # plain token replacement: the CSS is full of braces str.format would eat
    for token, value in (
        ("{answers}", answers),
        ("{gap_note}", gap),
        ("{chart}", chart),
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
