import type { BuildEvent, BuildStats, Finding, Measurement, Param, Spec, ToolStep } from "../src/types"
import type { PartCardPart } from "../src/PartCard"
import flaggedFindingsJson from "./flagged.findings.json"

// Fixture data for the gallery. Shapes come from src/types.ts, values are made
// up but plausible: a gallery that lies about the data lies about the design.

export const markdownFixture = `I measured the **shelf rail** and it is 25.16 mm across the flat.

Two things I still need:

- the wall thickness you want at the hook, default \`wall = 2.0\`
- whether the bracket carries more than 2 kg

The doctrine on this is in [the print rules](https://nurb.app/rules).

\`\`\`python
@part
def bracket(wall=2.0, hook_depth=18.0):
    return Box(40, hook_depth, wall)
\`\`\`

![a tracker pixel that must never render](https://tracker.test/pixel.gif)
`

// Card fixtures (buildFixture, specFixture, measurementFixture, stepFixtures)
// go here when the card components land.

export const specFixture: Spec = {
  part_name: "shelf_bracket",
  summary: "A bracket that hooks the shelf rail and carries 2 kg without a screw.",
  params: [
    { name: "wall", kind: "float", default: 2.0, description: "wall thickness at the hook" },
    { name: "hook_depth", kind: "float", default: 12.0, description: "how far the hook reaches over the rail" },
    { name: "rib_count", kind: "int", default: 3, description: "stiffening ribs under the shelf" },
  ],
  dimensions: [
    { name: "rail_width", value_mm: 25.16, how: "caliper across the flat", source: "measured", provisional: false },
    { name: "shelf_depth", value_mm: 180, how: "the user said 180", source: "asked", provisional: false },
    { name: "screw_dia", value_mm: 4, how: "M4 nominal", source: "standard", provisional: false },
    { name: "wall", value_mm: 2, how: "print doctrine minimum", source: "doctrine", provisional: true },
  ],
  acceptance: [
    { criterion: "No wall thinner than 1.2 mm", check: "min_wall" },
    { criterion: "The bracket fits in a 200 mm bed", check: "bbox.x < 200" },
  ],
  conventions: { expose_params: true, parameter_style: "keyword defaults" },
}

export const measurementRecorded: Measurement = {
  name: "rail_width",
  value_mm: 25.16,
  how: "caliper across the flat, three readings",
  provisional: false,
}

export const measurementChanged: Measurement = {
  name: "shelf_depth",
  value_mm: 184,
  how: "re-measured with the shelf in place",
  provisional: true,
  previous_value_mm: 180,
  stale_parts: ["bracket", "end_cap"],
}

const AGO = (seconds: number) => new Date(Date.now() - seconds * 1000).toISOString()

export const stepDone: ToolStep = {
  id: "step-done",
  verb: "build",
  object: "shelf_bracket.py",
  status: "done",
  started_at: AGO(9),
  elapsed_s: 4.2,
  input: { part: "shelf_bracket", params: { wall: 2.0, hook_depth: 12.5 } },
  output: "42 faces · 18.3 cm3 · 80.0 x 120.0 x 24.0 mm",
}

export const stepRunning: ToolStep = {
  id: "step-running",
  verb: "check",
  object: "shelf_bracket.py",
  status: "running",
  started_at: AGO(3),
}

export const stepFailed: ToolStep = {
  id: "step-failed",
  verb: "export",
  object: "shelf_bracket.3mf",
  status: "failed",
  started_at: AGO(20),
  elapsed_s: 1.8,
  input: { part: "shelf_bracket", format: "3mf", printer: "bambu-p1s" },
  output: "BRep_API: command not done\n  chamfer 1.0 on edge 14\n  two chamfered edges need 2.0 mm between them",
}

const doneStep = (id: string, verb: string, object: string, elapsed: number): ToolStep => ({
  id,
  verb,
  object,
  status: "done",
  started_at: AGO(30),
  elapsed_s: elapsed,
})

export const groupSteps: ToolStep[] = [
  doneStep("g1", "read", "parts/shelf_bracket.py", 0.4),
  doneStep("g2", "build", "shelf_bracket.py", 4.2),
  doneStep("g3", "check", "shelf_bracket.py", 1.1),
  doneStep("g4", "render", "shelf_bracket.png", 2.6),
  doneStep("g5", "export", "shelf_bracket.3mf", 3.3),
]

export const buildPassed: BuildEvent = {
  id: "build-passed",
  part_name: "shelf_bracket",
  status: "passed",
  started_at: AGO(400),
  elapsed_s: 321,
  revision: 24,
  steps: [
    doneStep("p1", "build", "shelf_bracket.py", 4.2),
    doneStep("p2", "check", "shelf_bracket.py", 1.1),
    doneStep("p3", "render", "shelf_bracket.png", 2.6),
  ],
  findings: [
    { rule: "thin_wall", label: "THIN WALL", severity: "warn", message: "0.9 mm at the hook, under the 1.2 mm nozzle floor" },
  ],
  stats: { size_mm: [80, 120, 24], volume_mm3: 18320, faces: 42, triangles: 1184, build_s: 4.2 },
}

export const buildRunning: BuildEvent = {
  id: "build-running",
  part_name: "shelf_bracket",
  status: "running",
  started_at: AGO(7),
  revision: 25,
  steps: [
    doneStep("r1", "build", "shelf_bracket.py", 4.2),
    doneStep("r2", "render", "shelf_bracket.png", 2.6),
    { id: "r3", verb: "check", object: "shelf_bracket.py", status: "running", started_at: AGO(3) },
  ],
  findings: [],
}

export const buildFailed: BuildEvent = {
  id: "build-failed",
  part_name: "shelf_bracket",
  status: "failed",
  started_at: AGO(200),
  elapsed_s: 47,
  revision: 26,
  steps: [
    doneStep("f1", "build", "shelf_bracket.py", 4.2),
    {
      id: "f2",
      verb: "check",
      object: "shelf_bracket.py",
      status: "failed",
      started_at: AGO(60),
      elapsed_s: 1.4,
      output: "2 rules failed\n  overhang: 62 deg on the shelf underside\n  sliver: 0.2 mm face at the hook",
    },
  ],
  findings: [
    { rule: "overhang", label: "OVERHANG", severity: "fail", message: "62 degrees on the shelf underside, over the 45 degree limit" },
    { rule: "sliver", label: "SLIVER", severity: "fail", message: "0.2 mm face at the hook, thinner than one extrusion" },
    { rule: "bed_contact", label: "BED CONTACT", severity: "warn", message: "18 mm2 of first layer, small for a 120 mm part" },
  ],
}

// The four findings a deliberately bad scratch part fires (a floating ledge and a paper-thin
// fin), straight out of the engine, so the glows sit on real faces of `flagged.glb`.
export const flaggedFindings = flaggedFindingsJson as unknown as Finding[]

// A part with one of every kind of parameter, so the panel shows a slider, an
// int stepper, a switch, and a pinned row at once.
export const panelParams: Param[] = [
  { name: "width", kind: "float", default: 92.5, description: "outside width at the wall" },
  { name: "wall", kind: "float", default: 2.4, description: "shell thickness" },
  { name: "bracket_count", kind: "int", default: 4, description: "hooks along the rail" },
  { name: "draft", kind: "bool", default: false, description: "skip the polish pass" },
  { name: "profile", kind: "str", default: "bambu_p1s", description: "pinned by the spec" },
]

export const panelStats: BuildStats = { size_mm: [92.5, 41.2, 18], volume_mm3: 14820, faces: 62, build_s: 3.1 }

// The library's shelf: one row per project, and twelve real-sounding parts.
export const libraryProjects: { id: string; name: string; count: number }[] = [
  { id: "bench-shelf", name: "Bench shelf", count: 12 },
  { id: "printer-mods", name: "Printer mods", count: 7 },
  { id: "garage-rail", name: "Garage rail", count: 4 },
  { id: "kitchen", name: "Kitchen odds", count: 3 },
]

const BUILT = (hours: number) => new Date(Date.now() - hours * 3600 * 1000).toISOString()

export const libraryParts: PartCardPart[] = [
  { id: "p1", name: "Rail bracket", bbox: [80, 120, 24], status: "built", revision: 27, builtAt: BUILT(0.3) },
  { id: "p2", name: "Gridfinity bin 2x1", bbox: [84, 42, 50], status: "built", revision: 12, builtAt: BUILT(1.1) },
  { id: "p3", name: "Vac hose adapter", bbox: [62, 62, 48], status: "failed", revision: 5, builtAt: BUILT(2.4) },
  { id: "p4", name: "Drill index block", bbox: [160, 60, 28], status: "built", revision: 9, builtAt: BUILT(3.8) },
  { id: "p5", name: "Shelf pin", bbox: [18, 18, 34], status: "built", revision: 4, builtAt: BUILT(5) },
  { id: "p6", name: "Wall plate", bbox: [120, 120, 6], status: "building", revision: 3, builtAt: BUILT(6) },
  { id: "p7", name: "Caliper stand", bbox: [180, 44, 40], status: "built", revision: 11, builtAt: BUILT(9) },
  { id: "p8", name: "Spool holder arm", bbox: [140, 36, 64], status: "built", revision: 18, builtAt: BUILT(26) },
  { id: "p9", name: "Hex key rack", bbox: [110, 30, 22], status: "built", revision: 6, builtAt: BUILT(30) },
  { id: "p10", name: "Filament clip", bbox: [24, 18, 12], status: "built", revision: 2, builtAt: BUILT(48) },
  { id: "p11", name: "Nozzle tray", bbox: [90, 60, 16], status: "unbuilt", revision: null, builtAt: null },
  { id: "p12", name: "Cable comb", bbox: [70, 14, 10], status: "built", revision: 8, builtAt: BUILT(72) },
]
