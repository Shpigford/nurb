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

from .report import PASS, pass_at, rows_from, summarize

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
    "grok": ("Grok", "#b8bec9"),
}

# Editorial layer, keyed by (harness, model, effort). Grounded in the committed rows;
# update alongside them. Combos without an entry render numbers-only. The plan label
# always comes from SUBSCRIPTIONS, never from here, so rows stay consistent.
VERDICTS = {
    ("claude", "claude-fable-5", "high"): "Twenty-four attempts, twenty-three parts worth printing. It checked its own work in every one of them: it cuts the part open, measures what it just built, and fixes what it finds before it stops. The one miss was a D-shaft knob with a socket that did not hold the stem. The most expensive row on the board.",
    ("claude", "claude-sonnet-5", "xhigh"): "Right on all six jobs, and the slowest route there by a wide margin. One design job ran past forty minutes. Pick it when the part matters more than the wait.",
    ("claude", "claude-opus-5", "high"): "Seventeen of eighteen parts came out right, and it was honest about the unmeasured dimension every time. The one miss is the mistake this board catches most often: a knob bored a shade too tight for the shaft to go in. Around ten minutes a part, and the design jobs are where that time goes.",
    ("grok", "grok-4.6", "medium"): "Sixteen of eighteen right, and both misses are the same knob: a socket bored a shade too tight for the stem to seat, once also too narrow to grip. At about seven minutes a part it takes three times as long as low effort, which gets more right for half the money. Skip it in both directions: low is the cheap Grok row, xhigh is the accurate one.",
    ("codex", "gpt-5.6-luna", "medium"): "Eleven of eighteen right at about two minutes and a dime a part. All three knobs came out too tight for the stem, two wall clips stopped holding the bundle once its size changed, one bit block lost its chamfers when the bit grew, and once it wrote its guess at the unmeasured dimension down as though it had measured it. The same model at xhigh costs pennies more and misses less; run that.",
    ("grok", "grok-4.6", "high"): "Nineteen of twenty-one right across all six jobs, and still the wrong Grok row to pick. Low effort is on the same subscription, gets a higher share right, runs five times faster and costs a third as much, and xhigh takes about the same time as this one and misses far less. The misses here are a bit block missing its top chamfer and a knob both too tight and too narrow to turn.",
    ("claude", "claude-sonnet-5", "high"): "Twenty-five of thirty right, four of the six jobs perfect, and honest about the unmeasured dimension every time. The real failures are two knobs too tight for the shaft, one of them barely half the grip width asked for. Its other three misses are softer, wall clips that hold the bundle but spend more plastic than the job allowed. Around twelve minutes a part, and the wall clip is where that time goes: it averaged half an hour.",
    ("grok", "grok-4.6", "low"): "The cheapest good part on the board, and it is not close: seventeen of eighteen right, about two minutes each, for pennies. Both of the hard fit jobs came out right every time. Its one miss was a wall clip you could not get a screwdriver into. Run this for everyday parts and step up to xhigh when the part has to be right the first time.",
    ("claude", "claude-opus-5", "low"): "One attempt per job, so read this as a sample rather than a score. Five of six right, and the miss was the easiest job on the board: a cable clip built to the stated size that stopped tracking once the size changed.",
    ("claude", "claude-sonnet-5", "medium"): "The same result as high effort, for about the same money and no faster, down to the same cable clip that stopped tracking its own dimensions. One design job ran fifty minutes. If you want Sonnet perfect, xhigh is the row that gets there.",
    ("claude", "claude-sonnet-5", "low"): "Fast and cheap for a Claude plan, and it slips exactly where the jobs stop handing over dimensions: a wall clip with no way in for the screwdriver, a rest the pole could not drop into, a knob too narrow to turn. Fine for parts you spell out in full.",
    ("codex", "gpt-5.6-sol", "low"): "Fifteen of eighteen right at about two minutes a part, which was the best Codex row until the same model ran at high effort. It got every stated dimension and the curved rest right every time. Its misses are about reaching the part rather than shaping it, two wall clips with no clear path in for the screw and its driver, and one knob bored too tight for the shaft. High effort costs about the same and misses less, so start there.",
    ("codex", "gpt-5.6-terra", "low"): "Everything it made built, and about half were worth printing. The pattern is a part that works at the size you stated and nowhere else: all three of its wall clips stopped fitting when the cable bundle changed, and one pole rest came out flat where the job needed a curve. It never once went back to measure what it had made.",
    ("codex", "gpt-5.6-luna", "low"): "Cheap, fast, and right five times out of eighteen. It wrote the pole's size straight into the file and still built a rest the pole would not drop into, at that size or any other. Elsewhere it left a 0.3mm wall no printer will lay down, and once wrote its guess at the unmeasured dimension down as though it had measured it. The same model at xhigh is a different machine; run that instead.",
    ("codex", "gpt-5.6-sol", "high"): "Twenty-eight of thirty parts right at about four minutes each. Five of the six jobs came out right on every single attempt, the curved pole rest and the one-screw wall clip included, and both misses are the same mistake, a knob bored a shade too tight for the shaft to go in. The same model at medium effort gets the same twenty-eight right in less time for less money, so start there.",
    ("codex", "gpt-5.6-luna", "xhigh"): "Eleven cents a part, and twenty-three of thirty right where the same model at low effort managed five. Effort is what luna was missing. It still slips when a part has to keep working at other sizes: two bit blocks stopped building once the bit got bigger, and a wall clip put the screw through the only place the bundle had to sit. One knob came out with a round bore that spins on the shaft, and once it filed its guess at the unmeasured dimension without marking it as a guess.",
    ("codex", "gpt-5.6-terra", "medium"): "Thirty-four of forty-eight right across two people's runs, at about two and a half minutes a part. Every stated dimension and every missing measurement it handled right; the design jobs are where it thins out. Half its wall clips left no usable path for the screw and its driver, five of eight knobs came out too tight for the shaft, and two pole rests were too flat to cradle the pole. At about eighty cents a part it costs ten times what luna does and gets no more right.",
    ("claude", "claude-haiku-4-5-20251001", "low"): "Fine when you spell every dimension out, and cheap. Asked to design, it produced parts you would not print: it came apart on all three design jobs, with walls and sockets that break the printability rules outright. It did handle the missing measurement honestly.",
    ("grok", "grok-4.6", "xhigh"): "The most reliable row on the board that anyone can afford: thirty-five of thirty-six right, pooled from two people's runs, with five of the six jobs right on every single attempt. Its one miss was a knob bored a shade too tight for the stem and a fraction under the grip width asked for. It takes five times as long as the same model at low effort and costs four times as much, which is still under thirty cents a part.",
    ("codex", "gpt-5.6-sol", "medium"): "The ChatGPT row to pick: twenty-eight of thirty right at about three minutes a part, which is what the same model manages at high effort, sooner and for less. Four of the six jobs came out right every time, the curved pole rest among them. Its two misses were a wall clip that left the bundle nothing to sit against and a knob bored a shade too tight for the shaft.",
    ("claude", "claude-opus-5", "medium"): "Fourteen of eighteen right at about seven minutes a part, and one job it never got: all three knobs came out too tight for the shaft and too narrow to grip. The fourth miss was a leg cup whose walls did not reach the rim solid. It was honest about the unmeasured dimension every time. Opus at high effort gets seventeen of eighteen for three more minutes a part, so run that instead.",
    ("codex", "gpt-5.6-luna", "high"): "Ten cents a part, and twenty-two of thirty right. The job it never got is the bit block: every one built at the size stated and then stopped tracking once the bit grew, losing its pockets or its top chamfer. Elsewhere it slipped once each, a wall clip with no way in for the screw, a rest the pole would not sit in at another size, and a knob with a round bore that spins on the shaft. The same model at xhigh is the same machine for two cents more.",
    ("codex", "gpt-5.6-terra", "high"): "Nineteen of thirty right, and the two design jobs are where it comes apart: four of five wall clips had no usable path for the screw and its driver, and all five knobs came out too tight for the shaft. It also left one cable clip with no hole in its mounting tab. The curved rest and the missing measurement it got right every time. Terra at medium effort costs about the same and gets more right, and sol at medium is a different machine for twice the money.",
    ("claude", "claude-haiku-4-5-20251001", "high"): "The weakest row here, and the extra effort did not help. Two parts of twelve came out right. It also wrote its guess at the unmeasured dimension down as though it had measured it, which is the mistake nobody catches until the print is wrong six months later.",
}

HEAD = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>nurb &middot; which AI designs the best parts?</title>
<meta name="description" content="The popular AI models, given the same real part-design jobs, graded by machine against print physics. Pick the one that fits your subscription.">
<meta property="og:title" content="nurb &middot; which AI designs the best parts?">
<meta property="og:description" content="The popular AI models, given the same real part-design jobs, graded by machine against print physics. Pick the one that fits your subscription.">
<meta property="og:url" content="https://nurb.dev/benchmarks.html">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 18 18'%3E%3Cg stroke='%236ee7a8' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' fill='none'%3E%3Cpath d='m7.997,2.332l-4.25,2.465c-.617.358-.997,1.017-.997,1.73v4.946c0,.713.38,1.372.997,1.73l4.25,2.465c.621.36,1.386.36,2.007,0l4.25-2.465c.617-.358.997-1.017.997-1.73v-4.946c0-.713-.38-1.372-.997-1.73l-4.25-2.465c-.621-.36-1.386-.36-2.007,0Z' fill='%236ee7a8' fill-opacity='.3' stroke-width='0'/%3E%3Cpath d='m7.997,2.332l-4.25,2.465c-.617.358-.997,1.017-.997,1.73v4.946c0,.713.38,1.372.997,1.73l4.25,2.465c.621.36,1.386.36,2.007,0l4.25-2.465c.617-.358.997-1.017.997-1.73v-4.946c0-.713-.38-1.372-.997-1.73l-4.25-2.465c-.621-.36-1.386-.36-2.007,0Z'/%3E%3Cpolyline points='12.251 7.1035 9 9 5.75 7.1035'/%3E%3Cline x1='9.0005' y1='12.7817' x2='9' y2='9'/%3E%3C/g%3E%3C/svg%3E">
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
    /* Mono is the machine's voice; prose gets a human one. */
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
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
      linear-gradient(rgba(110,231,168,.022) 1px, transparent 1px),
      linear-gradient(90deg, rgba(110,231,168,.022) 1px, transparent 1px);
    background-size: 56px 56px;
  }
  body::after {
    content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background: radial-gradient(1100px 520px at 50% -80px, rgba(110,231,168,.055), transparent 70%);
  }
  .wrap { max-width: 1060px; margin: 0 auto; padding: 0 24px; }
  header { position: sticky; top: 0; z-index: 10;
           background: rgba(22,24,29,.82); backdrop-filter: blur(12px);
           border-bottom: 1px solid var(--line); }
  header .wrap { display: flex; align-items: center; gap: 8px; height: 54px; }
  header .logo { display: flex; align-items: center; gap: 8px; color: var(--text);
                 font-weight: 700; letter-spacing: .06em; }
  header .logo:hover { text-decoration: none; }
  header .logo svg { width: 17px; height: 17px; color: var(--accent); }
  header nav { margin-left: auto; display: flex; gap: 22px; font-size: 13px; }
  header nav a { color: var(--dim); }
  header nav a:hover { color: var(--text); text-decoration: none; }
  header nav a.here { color: var(--text); }
  header nav a.gh { color: var(--text); }
  header .menu-btn { display: none; margin-left: auto; padding: 8px; background: none;
                     border: 0; color: var(--text); cursor: pointer; }
  header .menu-btn svg { display: block; width: 20px; height: 20px; }
  header .menu-btn .x, header.open .menu-btn .bars { display: none; }
  header.open .menu-btn .x { display: block; }
  @media (max-width: 860px) {
    header .menu-btn { display: block; }
    header nav { display: none; position: absolute; top: 54px; left: 0; right: 0;
                 flex-direction: column; gap: 0; padding: 4px 24px 12px;
                 background: var(--bg); border-bottom: 1px solid var(--line);
                 box-shadow: 0 30px 80px rgba(0,0,0,.45); }
    header.open nav { display: flex; }
    header nav a { padding: 11px 0; font-size: 15px; }
  }
  main { max-width: 920px; margin: 0 auto; padding: 72px 24px 72px; }
  h1 { font-size: clamp(28px, 4.5vw, 42px); font-weight: 800; line-height: 1.15;
       letter-spacing: -.02em; margin-bottom: 16px; }
  .lead { color: var(--dim); margin-bottom: 8px; font: 16px/1.6 var(--sans); }
  .sec-label { color: var(--dimmer); font-size: 12px; letter-spacing: .12em;
               margin: 72px 0 8px; }
  .sec-label b { color: var(--accent); font-weight: 400; }
  h2 { font-size: clamp(20px, 2.6vw, 26px); font-weight: 700; letter-spacing: -.01em;
       margin-bottom: 14px; }
  .jobs { display: grid; grid-template-columns: 1fr 1fr; gap: .7rem; margin-bottom: .4rem; }
  @media (max-width: 640px) { .jobs { grid-template-columns: 1fr; } }
  .job { background: var(--panel2); border: 1px solid var(--line); border-radius: 8px; padding: .8rem 1rem; }
  .job b { display: block; }
  .job span { color: var(--dim); font: 13.5px/1.5 var(--sans); }
  .answers { display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; }
  @media (max-width: 640px) { .answers { grid-template-columns: 1fr; } }
  .answer { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.2rem; }
  .answer .have { font-size: .85rem; color: var(--dim); display: flex; align-items: center; gap: .5rem; }
  .answer .have i { width: 8px; height: 8px; border-radius: 50%; flex: none; }
  .answer .pick { font-size: 1.15rem; font-weight: 700; margin: .15rem 0; }
  .answer .pick small { color: var(--dim); font-weight: 400; font-size: .8em; }
  .answer .why { color: var(--dim); font-size: .88rem; }
  .chart-lead { color: var(--dim); font: 15px/1.6 var(--sans); margin-bottom: 16px; }
  .chart { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: .6rem; }
  .chart svg { display: block; width: 100%; height: auto; }
  .chart-legend { display: flex; flex-wrap: wrap; gap: .4rem 1.4rem; padding: .55rem .6rem .3rem; border-top: 1px solid var(--line); margin-top: .4rem; font-size: .8rem; color: var(--dim); }
  .chart-legend span { display: inline-flex; align-items: center; gap: .45rem; }
  .chart-legend i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .chart-legend b { font-weight: 400; color: var(--text); }
  .chart .dot { transition: r .1s; }
  .chart .dot:hover { r: 8; }
  .board { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
  /* The model column sizes to the longest pinned id, which is a dated one like
     claude-haiku-4-5-20251001; wrap its effort onto a second line and that row
     stands taller than every other. */
  .board .hd, .board summary { display: grid; grid-template-columns: 2rem minmax(0,1.7fr) minmax(6.5rem,1fr) 7.5rem 5.2rem 5.8rem; gap: 1rem; align-items: center; padding: .7rem 1.1rem; }
  .board .hd { font-size: .72rem; color: var(--dimmer); text-transform: uppercase; letter-spacing: .06em; border-bottom: 1px solid var(--line); }
  .board .hd .r { text-align: right; }
  .board details { border-bottom: 1px solid var(--line); }
  .board details:last-child { border-bottom: 0; }
  .board summary { cursor: pointer; list-style: none; }
  .board summary::-webkit-details-marker { display: none; }
  .board summary:hover { background: var(--panel2); }
  .board details.top summary { box-shadow: inset 3px 0 0 var(--accent); }
  .rank { color: var(--dimmer); font-size: .85rem; }
  .top .rank { color: var(--accent); font-weight: 700; }
  .who .model { font-weight: 700; white-space: nowrap; }
  .who .model small { color: var(--dim); font-weight: 400; font-size: .82em; }
  .who .plan { font-size: .78rem; color: var(--dim); display: flex; align-items: center; gap: .4rem; }
  .who .plan i { width: 8px; height: 8px; border-radius: 50%; flex: none; }
  .rate .rbar { display: block; height: 8px; background: var(--panel2); border: 1px solid var(--line); border-radius: 4px; margin-bottom: .3rem; }
  .rate .rbar i { display: block; height: 100%; border-radius: 3px; background: var(--accent); }
  .rate .rbar i.mid { background: var(--amber); }
  .rate .rbar i.low { background: var(--bad); }
  .rate span { font-size: .8rem; color: var(--dim); }
  .rate span b { color: var(--text); }
  .cells { display: flex; gap: 4px; }
  .cells i { width: 13px; height: 13px; border-radius: 3px; flex: none; }
  .cells i.ok { background: var(--accent); }
  .cells i.mid { background: var(--amber); }
  .cells i.low { background: var(--bad); }
  .cells i.off { background: transparent; border: 1px dashed var(--dimmer); }
  .time, .cost { font-size: .85rem; color: var(--dim); text-align: right; white-space: nowrap; }
  .board .body { padding: .2rem 1.1rem 1.2rem 4.1rem; }
  @media (max-width: 720px) {
    /* A phone fits the rank, the model, and the number the board ranks on. Pinned
       ids are long enough that keeping a fourth column here costs the model name
       two extra wrapped lines, and every verdict that turns on speed says so in
       words anyway. */
    .board .hd, .board summary { grid-template-columns: 1.6rem minmax(0,1.5fr) minmax(4.5rem,1fr); gap: .6rem; padding: .7rem .8rem; }
    /* Narrow enough that a dated model id cannot fit on one line, and holding it
       there would scroll the page sideways. A taller row is the cheaper trade. */
    .who .model { white-space: normal; }
    /* Break before the separator, never after it: a line ending in a lone middot
       reads as something the renderer dropped. */
    .who .model small { white-space: nowrap; }
    .cells, .cost, .time, .board .hd .c4, .board .hd .c5, .board .hd .c6 { display: none; }
    .board .body { padding-left: 1.1rem; }
  }
  .verdict { color: var(--dim); font: 14.5px/1.55 var(--sans); margin-bottom: .9rem; max-width: 680px; }
  .bars { display: grid; grid-template-columns: max-content 1fr max-content; gap: .35rem .8rem; align-items: center; font-size: .85rem; }
  .bars .name { color: var(--dim); white-space: nowrap; }
  .bar { position: relative; height: 8px; background: var(--panel2); border: 1px solid var(--line); border-radius: 4px; }
  .bar i { display: block; height: 100%; background: var(--accent); border-radius: 3px; }
  .bar u { position: absolute; top: -3px; width: 2px; height: 12px; background: var(--text); opacity: .55; border-radius: 1px; }
  .bar i.mid { background: var(--amber); }
  .bar i.low { background: var(--bad); }
  .pct { text-align: right; min-width: 6.5ch; }
  .pct.na { color: var(--dimmer); }
  .fine { color: var(--dimmer); font: 13px/1.55 var(--sans); max-width: 680px; margin-top: 1.1rem; }
  .fine:first-of-type { margin-top: 2.4rem; }
  .fine a { color: var(--dim); }
  .contribute { margin-top: 2.4rem; background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 1.1rem 1.3rem; }
  .contribute b { color: var(--accent); }
  .contribute span { color: var(--dim); font: 14px/1.55 var(--sans); }
  .cmd { display: flex; align-items: center; gap: 12px; margin: .7rem 0;
         background: var(--panel2); border: 1px solid var(--line); border-radius: 9px;
         padding: 11px 16px; font-size: 14px; overflow-x: auto; white-space: nowrap; }
  .cmd .d { color: var(--dimmer); user-select: none; }
  .cmd button { background: none; border: none; color: var(--dim); cursor: pointer;
                font: inherit; font-size: 12px; padding: 2px 4px; border-radius: 5px;
                margin-left: auto; }
  .cmd button:hover { color: var(--accent); }
  footer { border-top: 1px solid var(--line); padding: 34px 0 44px;
           color: var(--dimmer); font-size: 12px; }
  footer .wrap { display: flex; flex-wrap: wrap; gap: 8px 24px; align-items: baseline; }
  footer a { color: var(--dim); }
  footer .spacer { flex: 1; }
</style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
  <symbol id="i-cube" viewBox="0 0 18 18"><path d="m7.997,2.332l-4.25,2.465c-.617.358-.997,1.017-.997,1.73v4.946c0,.713.38,1.372.997,1.73l4.25,2.465c.621.36,1.386.36,2.007,0l4.25-2.465c.617-.358.997-1.017.997-1.73v-4.946c0-.713-.38-1.372-.997-1.73l-4.25-2.465c-.621-.36-1.386-.36-2.007,0Z" fill="currentColor" opacity=".3" stroke-width="0"/><path d="m7.997,2.332l-4.25,2.465c-.617.358-.997,1.017-.997,1.73v4.946c0,.713.38,1.372.997,1.73l4.25,2.465c.621.36,1.386.36,2.007,0l4.25-2.465c.617-.358.997-1.017.997-1.73v-4.946c0-.713-.38-1.372-.997-1.73l-4.25-2.465c-.621-.36-1.386-.36-2.007,0Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"/><polyline points="12.251 7.1035 9 9 5.75 7.1035" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"/><line x1="9.0005" y1="12.7817" x2="9" y2="9" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"/></symbol>
</svg>

<header>
  <div class="wrap">
    <a class="logo" href="index.html"><svg><use href="#i-cube"/></svg>nurb</a>
    <button class="menu-btn" aria-label="menu" aria-expanded="false">
      <svg class="bars" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line x1="2.5" y1="5.5" x2="17.5" y2="5.5"/><line x1="2.5" y1="10" x2="17.5" y2="10"/><line x1="2.5" y1="14.5" x2="17.5" y2="14.5"/></svg>
      <svg class="x" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line x1="4.5" y1="4.5" x2="15.5" y2="15.5"/><line x1="15.5" y1="4.5" x2="4.5" y2="15.5"/></svg>
    </button>
    <nav>
      <a href="index.html#demo">the app</a>
      <a href="index.html#how">how it works</a>
      <a href="index.html#start">get started</a>
      <a class="here" href="benchmarks.html">benchmarks</a>
      <a href="/changelog">changelog</a>
      <a class="gh" href="https://github.com/Shpigford/nurb">github &nearr;</a>
    </nav>
  </div>
</header>
<script>
  const hdr = document.querySelector('header');
  const menuBtn = hdr.querySelector('.menu-btn');
  menuBtn.addEventListener('click', () =>
    menuBtn.setAttribute('aria-expanded', hdr.classList.toggle('open')));
  hdr.querySelector('nav').addEventListener('click', () => {
    hdr.classList.remove('open');
    menuBtn.setAttribute('aria-expanded', 'false');
  });
</script>
<main>
<h1>Which AI designs the best parts?</h1>
<p class="lead">nurb works with the AI subscription you already have. Every model gets the same real part-design jobs, and a machine grades the actual geometry against what was asked and against print physics.</p>

<div class="sec-label"><b>// 01</b> &nbsp;the short answer</div>
<h2>Start from what you subscribe to.</h2>
<div class="answers">
{answers}
</div>

<div class="sec-label"><b>// 02</b> &nbsp;the leaderboard</div>
<h2>Every model, ranked.</h2>
<p class="chart-lead">Ranked by how often parts print right the first time. The six squares are the six jobs below, green to red; a dashed square is a job not yet run. Click a row for the per-attempt detail.</p>
{cards}

<div class="sec-label"><b>// 03</b> &nbsp;the tradeoff</div>
<h2>Quality against speed.</h2>
<p class="chart-lead">First-try print rate against minutes per part. Up and to the left is better.</p>
{chart}

<div class="sec-label"><b>// 04</b> &nbsp;the jobs</div>
<h2>Six jobs, graded on geometry.</h2>
<div class="jobs">
{jobs}
</div>

<div class="contribute">
  <b>Add your model to this page.</b>
  <span> One line, your own subscription, a wizard for the rest. Every run pools with everyone else's.</span>
  <span class="cmd"><span class="d">$</span><span>curl -fsSL https://nurb.dev/bench.sh | sh</span><button data-copy="curl -fsSL https://nurb.dev/bench.sh | sh" title="copy">copy</button></span>
  <span>Or paste that line to your AI and let it drive.</span>
</div>

<p class="fine">$/part is what the same tokens would cost at API list prices; on a subscription it comes out of your plan.</p>
<p class="fine">Early days: {trial_count} graded parts across {job_count} jobs so far. Each bar averages every attempt on file, and the ticks are the attempts themselves.</p>
<p class="fine">Grading is a fixed rubric measured on the part's actual geometry, so the only randomness is the model's. Raw results, full transcripts, and the grading code are <a href="https://github.com/Shpigford/nurb/blob/main/evals/REPORT.md">on GitHub</a>.</p>
</main>
<footer>
  <div class="wrap">
    <span>&copy; 2026 Ordinary Systems LLC</span>
    <a href="https://github.com/Shpigford/nurb/blob/main/LICENSE">FSL-1.1-MIT</a>
    <span class="spacer"></span>
    <a href="https://github.com/Shpigford/nurb/blob/main/evals/REPORT.md">full results</a>
    <a href="/changelog">changelog</a>
    <a href="https://github.com/Shpigford/nurb">github</a>
    <a href="https://x.com/Shpigford">@shpigford</a>
    <a href="https://github.com/Shpigford/nurb/issues/new">send feedback</a>
  </div>
</footer>
<script>
for (const b of document.querySelectorAll('[data-copy]')) {
  b.onclick = async () => {
    try { await navigator.clipboard.writeText(b.dataset.copy); } catch {}
    b.textContent = 'copied';
    setTimeout(() => { b.textContent = 'copy'; }, 1200);
  };
}
</script>
</body>
</html>
"""


def _pool(rows):
    """One model, one effort, one job, several benchmark identities: pool them.

    `summarize` separates rows on harness version and benchmark revision because the
    audit table needs that precision, and it should keep it. The card is coarser by
    design (one model, one effort, six jobs), so when the same job has been run twice
    under different identities, both belong to the same card. Keeping one and dropping
    the other would hide submitted trials from a page that shows every attempt as its
    own tick. Identity strings survive only where the pooled rows agree on them."""
    if len(rows) == 1:
        return rows[0]
    trials = sum(r["trials"] for r in rows)
    scores = [s for r in rows for s in r["scores"]]
    # lint, dims and flex are means over built trials, so they pool by built count,
    # not by trial count; everything else is a mean over every trial.
    builts = [round(r["built"] * r["trials"]) for r in rows]

    def weighted(field, weights):
        pairs = [(r[field], w) for r, w in zip(rows, weights) if r.get(field) is not None and w]
        return sum(v * w for v, w in pairs) / sum(w for _, w in pairs) if pairs else None

    counts = [r["trials"] for r in rows]
    passes = sum(s >= PASS for s in scores)
    pooled = {
        **rows[0],
        "trials": trials,
        "scores": scores,
        "score": sum(scores) / trials,
        "seeds": sorted({s for r in rows for s in r["seeds"]}),
        "built": sum(builts) / trials,
        "lint": weighted("lint", builts),
        "dims": weighted("dims", builts),
        "flex": weighted("flex", builts),
        "pass@1": pass_at(1, trials, passes),
        "pass@3": pass_at(3, trials, passes),
        "tokens": weighted("tokens", counts),
        "cost": weighted("cost", counts),
        "wall_s": weighted("wall_s", counts),
        "capped": sum(r.get("capped", 0) for r in rows),
    }
    for field in ("harness_version", "nurb_version", "benchmark_version", "benchmark_revision"):
        values = {r[field] for r in rows}
        pooled[field] = values.pop() if len(values) == 1 else None
    return pooled


def _combos(summary):
    """Fold per-task rows into one entry per harness+model+effort, best first.

    Ordered by first-try rate, because that is the number the board leads with and
    what the page tells the reader the ranking means. Mean score breaks ties, so two
    models that print the same fraction of parts first time are separated by how
    close the misses came. The resolved ids ride along in the key so two same-label
    groups (a floating alias that served different models) never silently overwrite
    each other."""
    combos = {}
    for row in summary:
        key = (row["harness"], row["model"], row["effort"],
               tuple(row.get("resolved") or ()))
        combos.setdefault(key, {}).setdefault(row["task"], []).append(row)
    combos = {
        key: {task: _pool(rows) for task, rows in tasks.items()}
        for key, tasks in combos.items()
    }
    order = []
    for key, tasks in combos.items():
        firsts, total, _, _, _ = _stats(tasks)
        mean = sum(r["score"] for r in tasks.values()) / len(tasks)
        order.append(((firsts / total if total else 0.0, mean), key, tasks))
    order.sort(key=lambda item: (-item[0][0], -item[0][1]))
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
    # A combo that has not run every job cannot be recommended over one that has:
    # a perfect score on half the board is a thinner claim than a near-perfect one
    # on all of it. Completeness sorts first, so a partial row wins only when it is
    # the sole row for that subscription.
    jobs = len(JOBS)
    best = {}
    for key, tasks in combos:
        harness = key[0]
        firsts, total, minutes, capped, dollars = _stats(tasks)
        rank = (len(tasks) >= jobs, firsts / total if total else 0, -minutes)
        if harness not in best or rank > best[harness][0]:
            best[harness] = (rank, key, (firsts, total, minutes, capped, dollars))
    cards = []
    for harness, (label, color) in SUBSCRIPTIONS.items():
        if harness not in best:
            continue
        _, key, (firsts, total, minutes, capped, dollars) = best[harness]
        model, effort = key[1], key[2]
        cards.append(
            f'<div class="answer">\n'
            f'  <div class="have"><i style="background:{color}"></i>Have {html.escape(label)}?</div>\n'
            f'  <div class="pick">run {html.escape(model)} <small>at {html.escape(effort)} effort</small></div>\n'
            f'  <div class="why">{firsts}/{total} first-try prints &middot; '
            f"{_time_note(minutes, capped)}{_cost_note(dollars)}</div>\n"
            f"</div>"
        )
    return "\n".join(cards)


# 12px JetBrains Mono is monospace, so a label's width is its character count. Close
# enough to reserve space with, which is all the placement below needs.
_LABEL_ADVANCE = 7.05
_DOT_GAP = 12
_ARROW_GAP = 34
# What actually gets drawn is the backing rect, not the glyphs: 14px tall and 3px
# wider than the text on each side. The placer tests the drawn box, or it clears a
# neighbour by a margin the renderer then spends on padding.
_LABEL_ROW = 14
_LABEL_PAD = 3
# The plot's own box, named so the suite's overlap check reads the real numbers
# instead of a copy that can drift away from them.
_CHART_BOX = (840, 740)
_CHART_MARGINS = (56, 24, 26, 46)


def _label_sides(points, sx, sy, plot_left, plot_right, plot_top, plot_bottom):
    """Which side of its dot each label sits on.

    Three things want the space beside a dot: the label, its neighbours' labels, and
    the effort line joining a model's own variants, which runs through the label's
    row when it leaves at a shallow angle. Preference first, then the plot edges get
    a veto, then one sweep resolves whatever still overlaps.

    Left and right are only two slots, and the good models bunch into the top tenth
    of this chart, so the sweep runs out of room there long before the labels do. A
    label with nowhere clean on either side steps off its dot's row instead, by up to
    three lines, keeping its edge against the dot so it still reads as that dot's
    label. A row that would leave the plot is not offered: the axis caption sits just
    above the top rule and a label over it reads as part of it. Only a label that
    cannot go anywhere at all keeps its preferred side and overlaps, because a
    collision inside the plot still beats a label hanging over the axis.
    """
    placed = {}
    boxes = []
    for p in points:
        x, y = sx(p["minutes"]), sy(p["rate"])
        width = len(f"{p['model']} \u00b7 {p['effort']}") * _LABEL_ADVANCE
        crowd = any(
            q is not p and abs(sy(q["rate"]) - y) < 16 and 0 < sx(q["minutes"]) - x < 170
            for q in points
        )
        # The crowd rule only reaches 170px, and an effort line undercuts its label
        # from any distance, so a same-model point to the right counts at any gap.
        undercut = any(
            q is not p
            and (q["harness"], q["model"]) == (p["harness"], p["model"])
            and abs(sy(q["rate"]) - y) < 20
            and sx(q["minutes"]) > x
            for q in points
        )
        boxes.append(
            {
                "point": p, "x": x, "y": y, "width": width, "dy": 0,
                "flip": crowd or undercut or x > plot_right - 140,
            }
        )

    def span(box, flip, dy=0):
        if flip:
            lo, hi = box["x"] - _DOT_GAP - box["width"], box["x"] - _DOT_GAP
            # The fast models bunch against the left edge, where a long label has no
            # room to hang left of its dot at all. Once a label has left its row it
            # already carries a leader, so it can slide along to the edge and keep
            # reading as that dot's label; the leader is what ties them together.
            if dy and lo < plot_left:
                return plot_left, plot_left + box["width"]
            return lo, hi
        start = box["x"] + (_ARROW_GAP if box["point"]["capped"] else _DOT_GAP)
        return start, start + box["width"]

    def fits(box, flip, dy=0):
        lo, hi = span(box, flip, dy)
        return lo >= plot_left and hi <= plot_right

    for box in boxes:
        if not fits(box, box["flip"]) and fits(box, not box["flip"]):
            box["flip"] = not box["flip"]

    def collides(box, flip, dy=0):
        lo, hi = span(box, flip, dy)
        row = box["y"] + dy
        for other in boxes:
            if other is box:
                continue
            # Dots never move, so a label clears one only by leaving its row.
            if abs(other["y"] - row) < _LABEL_ROW and lo - 7 < other["x"] < hi + 7:
                return True
            if abs(other["y"] + other["dy"] - row) >= _LABEL_ROW:
                continue
            olo, ohi = span(other, other["flip"], other["dy"])
            if lo - _LABEL_PAD < ohi + _LABEL_PAD and olo - _LABEL_PAD < hi + _LABEL_PAD:
                return True
        return False

    for box in boxes:
        if collides(box, box["flip"]) and fits(box, not box["flip"]) \
                and not collides(box, not box["flip"]):
            box["flip"] = not box["flip"]

    # One greedy sweep places each label against whatever its neighbours happen to
    # hold at the time, so a box that had nowhere to go can open up once a later box
    # moves. Repeat until nothing moves, which on this many points is two passes.
    for _ in range(len(boxes)):
        moved = False
        for box in boxes:
            if not collides(box, box["flip"], box["dy"]):
                continue
            moves = (
                (flip, dy)
                for dy in (0, -14, 14, -20, 20, -28, 28, -34, 34, -42, 42)
                for flip in (box["flip"], not box["flip"])
            )
            for flip, dy in moves:
                row = box["y"] + dy
                if not plot_top <= row <= plot_bottom:
                    continue
                if fits(box, flip, dy) and not collides(box, flip, dy):
                    if (box["flip"], box["dy"]) != (flip, dy):
                        box["flip"], box["dy"] = flip, dy
                        moved = True
                    break
        if not moved:
            break

    for box in boxes:
        lo, hi = span(box, box["flip"], box["dy"])
        placed[id(box["point"])] = (
            (("end", hi) if box["flip"] else ("start", lo)) + (lo, hi, box["dy"])
        )
    return placed


def _chart(combos):
    """One inline SVG: first-try rate against minutes per part, a labeled dot per
    combo, colored by subscription. Effort variants of the same model connect into
    a line as they land, so the two knobs read as geometry: pick a model's line,
    slide along it for effort. Capped combos carry a right arrow: their time is a
    floor, not a measurement.

    The box is sized for the labels, not the dots. Rate is the crowded axis, because
    every model worth running lands in the top tenth of it, and a row of labels needs
    a fixed 14px whatever the plot's height is. Every row added to the board tightens
    that band, so the height is what buys the placer room to keep labels off each
    other."""
    width, height = _CHART_BOX
    left, right, top, bottom = _CHART_MARGINS
    pw, ph = width - left - right, height - top - bottom

    points = []
    for (harness, model, effort, _), tasks in combos:
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

    sides = _label_sides(points, sx, sy, left, width - right, top, height - bottom)

    for p in points:
        x, y = sx(p["minutes"]), sy(p["rate"])
        color = SUBSCRIPTIONS.get(p["harness"], ("", "var(--dim)"))[1]
        anchor, lx, label_lo, label_hi, dy = sides[id(p)]
        ly = y + dy
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
        if dy:
            # A label pushed off its dot's row can have someone else's dot between the
            # two. A leader says whose label it is; without one the reader guesses. It
            # is drawn neutral, not in the subscription's color, so it cannot be read
            # as one more effort line.
            edge = label_hi if anchor == "end" else label_lo
            parts.append(
                f'<path d="M {x:.0f} {y:.0f} L {edge:.0f} {ly:.0f}" fill="none" '
                f'stroke="var(--dimmer)" stroke-width="1"/>'
            )
        parts.append(
            f'<circle class="dot" cx="{x:.0f}" cy="{y:.0f}" r="6" fill="{color}" stroke="var(--panel)" stroke-width="2">'
            f"<title>{html.escape(title)}</title></circle>"
            # An effort line runs between two dots of the same model and passes
            # through the row of one of their labels. A glyph-hugging halo only masks
            # it at the strokes and leaves it showing between letters, so the label
            # gets a backing rect and reads as text on the panel, not text on a rule.
            f'<rect x="{label_lo - 3:.0f}" y="{ly - 7:.0f}" width="{label_hi - label_lo + 6:.0f}"'
            f' height="14" fill="var(--panel)"/>'
            f'<text x="{lx:.0f}" y="{ly + 4:.0f}" text-anchor="{anchor}" font-size="12" fill="var(--text)">'
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


def _tone(score):
    return "ok" if score >= 0.9 else "mid" if score >= 0.6 else "low"


def _cells(tasks):
    """Six squares, one per job in a fixed order, so every row's squares line up
    into a scannable matrix; the tooltip names the job and its score."""
    cells = []
    for task, (title, _) in JOBS.items():
        row = tasks.get(task)
        if row is None:
            cells.append(f'<i class="off" title="{html.escape(title)}: not yet run"></i>')
        else:
            pct = round(row["score"] * 100)
            cells.append(
                f'<i class="{_tone(row["score"])}" title="{html.escape(title)}: {pct}%"></i>'
            )
    return "".join(cells)


def _row(rank, key, tasks):
    harness, model, effort = key[:3]
    verdict = VERDICTS.get(key[:3], "")
    firsts, total, minutes, capped, dollars = _stats(tasks)
    rate = firsts / total if total else 0.0
    plan, color = SUBSCRIPTIONS.get(harness, (harness, "var(--dim)"))
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
    tone = "" if rate >= 0.9 else ' class="mid"' if rate >= 0.6 else ' class="low"'
    if dollars is None:
        cost = "&mdash;"
    else:
        cost = f"~${dollars:.2f}" if dollars >= 0.10 else f"~${dollars:.3f}"
    return f"""<details{' class="top"' if rank == 1 else ""}>
  <summary>
    <span class="rank">{rank}</span>
    <span class="who"><span class="model">{html.escape(model)} <small>&middot; {html.escape(effort)}</small></span>
      <span class="plan"><i style="background:{color}"></i>{html.escape(plan)}</span></span>
    <span class="rate"><span class="rbar"><i{tone} style="width:{rate * 100:.0f}%"></i></span>
      <span><b>{firsts}/{total}</b> &middot; {rate * 100:.0f}%</span></span>
    <span class="cells">{_cells(tasks)}</span>
    <span class="time" title="{html.escape(_time_note(minutes, capped))}">~{minutes:.0f}{"+" if capped else ""} min</span>
    <span class="cost">{cost}</span>
  </summary>
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
        chart = _chart(combos)
        rows = "\n".join(_row(i, key, tasks) for i, (key, tasks) in enumerate(combos, 1))
        cards = (
            '<div class="board">\n'
            '<div class="hd"><span></span><span>model</span><span>first-try prints</span>'
            '<span class="c4">jobs</span><span class="r c5">time</span><span class="r c6">$/part</span></div>\n'
            f"{rows}\n</div>"
        )
    else:
        answers = (
            '<div class="answer"><div class="have">No rows on file yet</div>'
            '<div class="pick">be the first</div>'
            '<div class="why">the one-liner below runs the benchmark on your own subscription and stages a submission</div></div>'
        )
        chart = '<p class="chart-lead">The chart appears with the first submitted rows.</p>'
        cards = '<p class="chart-lead">Nothing yet.</p>'
    page = HEAD  # plain token replacement: the CSS is full of braces str.format would eat
    for token, value in (
        ("{answers}", answers),
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
