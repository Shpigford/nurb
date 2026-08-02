# Research: a crown() helper for variable-height rims

Status: research only, nothing implemented. Written 2026-08-02 while triaging issue #55, so a future session can pick this up cold. The branch `issue-55` shipped the small fixes from that issue; this is the one big item deliberately left out.

## The problem

Issue #55 (https://github.com/Shpigford/nurb/issues/55), section 1. A user building a 145 x 364 x 102mm aircraft-floor tray wanted one conceptually simple thing: "round the top of this variable-height wall." A closed perimeter wall whose roofline rises and falls, capped with one consistently smooth rounded rim.

Direct filleting and polish failed for them with, in their words: visible bumps where wall sections joined, missing roundovers on short corner segments, segmented or faceted transitions, spherical-looking patches at corners, thin-wall and overhang defects from a swept coping-bead experiment, and topology changes that made edge selection unreliable after booleans.

Their eventual working recipe, which is the existence proof that this can be done on OCCT, took eight manual steps: (1) build one full-height perimeter ring, (2) cut the variable-height roofline from it, (3) create a separate 3D centreline, (4) sample curved edges manually, (5) convert sections into splines, (6) trim every path edge, (7) add tangent spline blends at every junction, (8) sweep a circular profile around the resulting closed wire. That occupied a substantial part of a 689-line part file. The ask is a robust high-level operation with tangent corner handling and selection that stays stable after booleans.

## Current state of nurb (verified against 0.9.0 source)

- There is no rim, crown, coping, pipe, or sweep helper anywhere in `src/`. `polish()` (`src/nurb/polish.py:98`) is the only edge-treatment helper and it is chamfer-only; it calls build123d's `chamfer` and vetoes any chamfer that would create a face smaller than `0.8 * size**2` slivers.
- `fillet` is deliberately not wrapped; the reason is stated at `src/nurb/__init__.py:40-42`. The doctrine actively prefers chamfers: `src/nurb/doctrine.md:126-127`, "a consistent faceted look that prints reliably beats a fillet default."
- The closest existing idiom is hand-rolled in `examples/notch/parts/bin_small_parts.py:135-184`: a bin rim with a front drop and two ramps, treated with face-normal predicates and a deliberate two-pass chamfer because one junction is the four-faces/three-edges vertex OCCT cannot cap. Roughly 50 careful lines for one rim on one part, i.e. the same shape of struggle as the issue, in our own examples.
- The other relevant trick on file: `examples/notch/parts/holder_filament_spool.py:104` builds a smooth transition as `fillet(tops[0], r) & fillet(tops[-1], r)`, an intersection of two single-fillet variants, with a warning in its card (`holder_filament_spool.md:113-116`) about why `mirror` is not the way to get the second half.
- Selection stability after booleans is a solved pattern here: `new_edges(before, combined=after)` (doctrine `src/nurb/doctrine.md:209-214`, repo rule in `CLAUDE.md`). Any crown() implementation should lean on it rather than on geometric selectors.

## Known kernel constraints (hard-won, do not rediscover)

- Two chamfered/filleted edges need more than `2 * size` of face between them or OCCT fails with `BRep_API: command not done`. The trap: each edge works alone, only the batch fails. Bisect the set (`CLAUDE.md`, and `src/nurb/polish.py:26-65` turns these kernel messages into doctrine-grade errors worth imitating).
- Chamfer/fillet order changes topology, so anything resolved against pristine geometry drifts after the first operation lands.
- OCCT's corner patches are exactly where the reporter saw "spherical-looking patches": ChFi3d corner capping at junctions of unequal-height edges is the fragile spot.

## Candidate approaches, in the order I would try them

**A. Baseline: plain fillet on the top-rim edge loop.** Select the roofline edges (everything on the top after the roofline cut, via `new_edges`), one `fillet` call. Known to fail on hard cases (that is the issue), but it must be the spike's control: measure exactly where and how it fails on the test parts, because if it works for 80% of real rims, crown() may only need to be the fallback.

**B. Bead sweep along the wall centreline (the reporter's recipe, automated).** The insight that makes this tractable: for a wall of constant thickness `t`, a fully-round rim is exactly the union of the wall with a pipe of radius `t/2` swept along the wall's top centreline. If the path is G1-continuous, the pipe is inherently smooth and tangent everywhere, no corner patches involved. The entire difficulty collapses into constructing one smooth closed 3D path, which is what the reporter hand-built in steps 3-7. Automation sketch: take the top face(s) of the wall after the roofline cut, extract inner and outer top edge loops, pair points to compute the midline (or offset the outer loop inward by `t/2` in the wall's local frame), fit a periodic BSpline through sampled midline points, and `sweep` a circle of radius `t/2`. Fitting one periodic spline through samples sidesteps the trim-every-edge-and-blend-every-junction work entirely; the cost is that the bead follows the roofline approximately (within sampling tolerance) rather than exactly, which for a printed part is fine and worth saying out loud in the docstring.
Failure modes to probe: tight inner corners with plan radius < `t/2` (self-intersecting sweep), walls of varying thickness (no single centreline), rooflines with sharp steps (a G1 spline will round the step, which may actually be the wanted behavior), and the seam where the periodic spline closes.

**C. Ring-then-cut ordering.** Round the rim while the roofline is still flat (a constant-height rim is the easy case for either fillet or a torus-section sweep), then cut the variable roofline afterwards. Almost certainly wrong as stated, because the cut re-exposes sharp edges along the new roofline; noted because the reporter tried the reverse ordering and because a variant might work: cut the roofline into the *solid* wall first, then apply B.

**D. OCP variable-radius fillet laws.** OCCT's `BRepFilletAPI_MakeFillet` supports radius evolution laws along an edge, which build123d does not expose. Dropping to OCP could handle rims where the wall thins toward the top. High effort, deep OCCT dependency, and the corner-capping fragility is the same machinery that already fails; I would only look here if B dies.

## Spike plan

Test parts, in ascending difficulty: (1) the `bin_small_parts` rim (front drop + two ramps, the known two-pass case), (2) a rectangular tray with one long sine-wave roofline, (3) an issue-#55-shaped tapered tray with mixed straight/curved plan and a multi-level roofline, (4) a torture case with a plan-radius corner tighter than `t/2`.

Acceptance: one visually smooth bead with no tangency kinks at junctions; builds across a parameter sweep (the `_flex` idea in `src/nurb/cli.py`, grow counts and lengths and see what breaks); `nurb check` clean beyond declared slivers; rebuild-stable when upstream features move (the selection must be derived, not coordinate-frozen); and a doctrine-grade error, in the part's own vocabulary, when the geometry makes the bead impossible (thin wall, tight corner) rather than a raw `BRep_API` message.

API sketch, holding to the vocabulary rules: `crown(wall, radius=None)` where radius defaults to half the measured wall thickness, returning the welded solid. It should refuse loudly when the wall is not a single closed loop of near-constant thickness, because that constraint is what makes approach B sound. Whether it lives in `polish.py` or its own `crown.py` is a judgement for whoever implements it; either way it joins `__all__` and therefore `nurb api` automatically.

Doctrine consequences to settle if the spike succeeds: this would be the first sanctioned round-edge treatment, so the doctrine's chamfer-first stance needs a carve-out ("rims a hand wraps around are the fillet exception" or similar), and draft mode should skip the crown the same way it skips polish. The bead ends and seam will earn slivers that need the usual card accounting.

## If the spike fails

The honest fallback, already true today: chamfer the rim via `polish()` and say so in the issue. A crown() that works on demos and dies on real parts is worse than no crown(), because it fails at exactly the moment the doctrine promised reliability.
