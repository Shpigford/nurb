import type { Message } from "@nurb/ui"
import type { Part, Project, ProjectSummary } from "./api"

export const summaries: ProjectSummary[] = [
  { id: "p1", name: "First", created_at: "2026-09-01T00:00:00Z", parts: 1, last_built: null, folder: true },
  { id: "p2", name: "Second", created_at: "2026-09-02T00:00:00Z", parts: 1, last_built: null, folder: true },
]

export function part(name: string, glb: string): Part {
  return {
    id: `part-${name}`,
    name,
    kind: "part",
    revision_id: "r1",
    revision: 3,
    source: "",
    card_md: null,
    params: [{ name: "wall", kind: "float", default: 2 }],
    overrides: {},
    build: {
      id: "b1",
      status: "ok",
      passed: true,
      started_at: "2026-09-01T00:00:00Z",
      finished_at: "2026-09-01T00:00:05Z",
      error: null,
      findings: [],
      stats: {},
      glb_url: glb,
      render_url: null,
      thumbnail_url: null,
    shown_revision: 1,
      stale: false,
      slice: null,
    },
  }
}

export const messages: Message[] = [
  {
    id: "m1",
    role: "assistant",
    content: "Built the bracket.",
    created_at: "2026-09-01T00:00:00Z",
    payload: {
      type: "build",
      build: {
        id: "b1",
        part_name: "bracket",
        status: "passed",
        started_at: "2026-09-01T00:00:00Z",
        elapsed_s: 4,
        steps: [],
        findings: [],
      },
    },
  },
  {
    id: "m2",
    role: "event",
    content: null,
    created_at: "2026-09-01T00:00:01Z",
    payload: {
      type: "spec",
      spec: {
        part_name: "bracket",
        summary: "A bracket",
        params: [],
        dimensions: [],
        acceptance: [],
        conventions: { expose_params: true, parameter_style: "keyword" },
      },
    },
  },
  {
    id: "m3",
    role: "event",
    content: null,
    created_at: "2026-09-01T00:00:02Z",
    payload: {
      type: "measurement",
      measurement: { name: "rail_width", value_mm: 25.16, how: "calipers", provisional: false },
    },
  },
  {
    id: "m4",
    role: "event",
    content: null,
    created_at: "2026-09-01T00:00:03Z",
    payload: {
      type: "step",
      step: { id: "s1", verb: "build", object: "bracket", status: "done", started_at: "2026-09-01T00:00:03Z", elapsed_s: 1 },
    },
  },
]

export function project(id: string, name: string, parts: Part[], msgs: Message[] = []): Project {
  return {
    id,
    name,
    created_at: "2026-09-01T00:00:00Z",
    folder: true,
    printer: { name: "bambu_x1c", bed: [256, 256, 256] },
    printers: ["bambu_x1c", "prusa_mk4"],
    spec: null,
    measurements: [{ name: "rail_width", value_mm: 25.16, unit: "mm", how: "calipers", provisional: true, value_changed_at: null }],
    parts,
    messages: msgs,
  }
}
