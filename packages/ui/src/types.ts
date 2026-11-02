// The transport-agnostic shapes every component in this package takes. They mirror
// what `nurb serve` stores and what its tools return (build_runs.findings, the pinned
// spec, the measurements table, the messages table), never a wire protocol.

export type Severity = "fail" | "warn"

export interface Finding {
  rule: string
  label?: string
  severity: Severity
  message: string
  /** Flat triangle soup of the guilty face in part coordinates, when the rule names one. */
  face?: number[] | null
  /** A point on the guilty geometry, for the pin. */
  where?: [number, number, number] | null
}

export type ParamKind = "float" | "int" | "bool" | "str"

export interface Param {
  name: string
  kind: ParamKind
  default: number | boolean | string
  min?: number
  max?: number
  step?: number
  description?: string
}

/** Current slider values keyed by parameter name. */
export type Params = Record<string, number | boolean | string>

export interface SpecDimension {
  name: string
  value_mm: number
  how: string
  source?: "standard" | "measured" | "asked" | "doctrine"
  provisional: boolean
}

export interface Spec {
  part_name: string
  summary: string
  params: { name: string; kind: string; default: number | boolean | string; description: string }[]
  dimensions: SpecDimension[]
  acceptance: { criterion: string; check: string }[]
  conventions: { expose_params: boolean; parameter_style: string; notes?: string[] }
}

export type StepStatus = "running" | "done" | "failed"

/** One tool call as the transcript shows it: a verb, an object, and how long it took. */
export interface ToolStep {
  id: string
  /** Closed vocabulary, upper-cased by the card: build, check, measure, export, ... */
  verb: string
  object: string
  status: StepStatus
  /** ISO timestamp; a running step counts up from it. */
  started_at: string
  /** Set once the step lands; a running step has none. */
  elapsed_s?: number
  input?: unknown
  output?: string
}

export type BuildStatus = "running" | "passed" | "failed" | "error"

export interface BuildStats {
  size_mm?: [number, number, number]
  volume_mm3?: number
  faces?: number
  triangles?: number
  build_s?: number
  render_error?: string
}

export interface BuildEvent {
  id: string
  part_name: string
  status: BuildStatus
  started_at: string
  elapsed_s?: number
  revision?: number
  steps: ToolStep[]
  findings: Finding[]
  stats?: BuildStats
  /** The trimmed traceback when status is "error". */
  error?: string
  render_url?: string
  glb_url?: string
}

export interface Measurement {
  name: string
  value_mm: number
  unit?: string
  how: string
  provisional: boolean
  previous_value_mm?: number | null
  /** Parts that read this measurement and were built before it changed. */
  stale_parts?: string[]
}

export interface MessageAttachment {
  id: string
  url: string
  width: number
  height: number
}

// `tool` names the tool call that wrote the row, so a transcript can match a
// live step to the row that replaces it.
export type MessagePayload =
  | { type: "build"; build: BuildEvent; tool?: string }
  | { type: "spec"; spec: Spec; model?: string; effort?: string; tool?: string }
  | { type: "measurement"; measurement: Measurement; tool?: string }
  | { type: "step"; step: ToolStep; tool?: string }

export interface Message {
  id: string
  role: "user" | "assistant" | "event"
  content: string | null
  payload?: MessagePayload
  attachments?: MessageAttachment[]
  /** The names of the files sent with this turn. */
  files?: string[]
  sequence_number?: number
  created_at: string
  /** The part this line belongs to. Null is a folder's project-wide conversation. */
  part?: string | null
}
