import type { ExportFormat, Finding, Message, Param, Params, Spec } from "@nurb/ui"

export interface ProjectSummary {
  id: string
  name: string
  created_at: string
  parts: number
  last_built: string | null
  /** False for the invisible container that holds one part and nothing else. */
  folder: boolean
}

/** What the slicer said, or why it could not say anything. Only "slice" is a number. */
export interface SliceResult {
  kind: "slicer" | "printer" | "choose" | "profile" | "slice" | "build"
  error?: string
  profiles?: string[]
  seconds?: number
  spoken?: string
  grams?: number | null
  weight?: string | null
  profile?: string
  /** The full preset chain, worth having next to the number it produced. */
  settings?: string
  run_id?: string
}

export interface PartBuild {
  id: string
  status: "ok" | "error"
  passed: boolean
  started_at: string
  finished_at: string | null
  error: string | null
  findings: Finding[]
  stats: { bbox?: [number, number, number]; volume?: number; ms?: number; [key: string]: unknown }
  glb_url: string | null
  render_url: string | null
  // One view on a transparent ground, for a library card.
  thumbnail_url: string | null
  // The revision whose geometry the URLs point at: the run's own, or the last one that built.
  shown_revision: number | null
  stale: boolean
  slice: SliceResult | null
}

export interface Part {
  id: string
  name: string
  /** What the person calls it, exactly as typed; null until they rename it. */
  title?: string | null
  kind: string
  revision_id: string
  revision: number
  source: string
  card_md: string | null
  params: Param[]
  /** The slider values the newest run was built at; empty when it ran on the defaults. */
  overrides: Params
  build: PartBuild | null
}

export interface ProjectMeasurement {
  name: string
  value_mm: number
  unit: string | null
  how: string
  provisional: boolean
  value_changed_at: string | null
}

export interface Printer {
  name: string
  bed: number[] | null
}

/** A machine on the bench. The workshop list, not the project's one choice. */
export interface PrinterProfile {
  name: string
  label: string
  brand: string
  bed: number[]
  default: boolean
}

/** A shipped profile nobody has added yet. */
export interface PrinterCatalogueEntry {
  name: string
  label: string
  brand: string
  bed: number[]
}

/** The slicer this Mac has, which is where weight and print time come from. */
export interface Slicer {
  name: string
  path: string
}

/** Everything the printer surfaces read: the bench, the catalogue, the slicer. */
export interface Workshop {
  printers: PrinterProfile[]
  catalogue: PrinterCatalogueEntry[]
  slicer: Slicer | null
}

export interface Project {
  id: string
  name: string
  created_at: string
  /** False for the invisible container that holds one part and nothing else. */
  folder: boolean
  printer: Printer | null
  /** Every profile the project could name, whether or not it has named one. */
  printers: string[]
  spec: Spec | null
  measurements: ProjectMeasurement[]
  parts: Part[]
  /** The family's shared files (system.py and the like) and the parts that import each. */
  shared?: { name: string; used_by: string[] }[]
  messages: Message[]
}

/** One part anywhere in the library, carrying the project it sits in. */
export interface LibraryPart extends Part {
  project_id: string
  project_name: string
  /** Whether that project is a folder the person named, or a container for this part alone. */
  folder: boolean
}

export interface ApplyResult {
  revision_id: string
  revision: number
  written: string[]
  skipped: { name: string; why: string }[]
  build: PartBuild
}

let base = ""
let resolver: (() => Promise<string>) | null = null

/** Point the client at another origin. The page leaves the base empty and stays same-origin. */
export function configure(opts: { base: string; resolve?: () => Promise<string> }): void {
  base = opts.base
  resolver = opts.resolve ?? null
}

/** The origin every request carries, which the live socket builds its own url from. */
export function apiBase(): string {
  return base
}

/** A reconnect's chance to learn a new port. Null when nobody asked to be asked. */
export function resolveBase(): Promise<string> | null {
  if (!resolver) return null
  return resolver().then((next) => (base = next))
}

/** A root-relative url from the server, made reachable from wherever the page runs. */
export function absolute(url: string): string {
  return base && url.startsWith("/") ? base + url : url
}

/**
 * A refusal the server answered with. The message stays the server's own sentence,
 * and the status rides along so a caller can tell a gone project from an outage.
 */
export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

// Every refusal is a sentence the server wrote for the person reading it, so it is
// passed through rather than replaced with a status code.
async function refusal(res: Response, fallback: string): Promise<ApiError> {
  const text = (await res.text()).trim()
  try {
    const said = JSON.parse(text) as { error?: string }
    if (said.error) return new ApiError(said.error, res.status)
  } catch {
    // Not every failure gets as far as the json writer.
  }
  return new ApiError(text || fallback, res.status)
}

async function get<T>(url: string): Promise<T> {
  const res = await fetch(base + url)
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
  return (await res.json()) as T
}

async function post<T>(url: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(base + url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
  return (await res.json()) as T
}

const partUrl = (id: string, tail: string) => `/api/parts/${encodeURIComponent(id)}/${tail}`
const projectUrl = (id: string, tail: string) => `/api/projects/${encodeURIComponent(id)}/${tail}`

export function fetchProjects(): Promise<{ projects: ProjectSummary[] }> {
  return get("/api/projects")
}

/** One project. Naming a part narrows the transcript to that part's conversation. */
export function fetchProject(id: string, part?: string): Promise<Project> {
  const tail = part === undefined ? "" : `?part=${encodeURIComponent(part)}`
  return get(`/api/projects/${encodeURIComponent(id)}${tail}`)
}

/** Every part in the library, whichever project holds it. */
export function listParts(): Promise<{ parts: LibraryPart[] }> {
  return get("/api/parts")
}

export function buildWithParams(
  partId: string,
  values: Params,
  signal?: AbortSignal
): Promise<{ build: PartBuild }> {
  return post(partUrl(partId, "params"), { values }, signal)
}

export function applyParams(partId: string, values: Params): Promise<ApplyResult> {
  return post(partUrl(partId, "apply"), { values })
}

export async function exportPart(partId: string, format: ExportFormat, values: Params): Promise<Blob> {
  const res = await fetch(base + partUrl(partId, "export"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format, values }),
  })
  if (!res.ok) throw await refusal(res, "The download did not finish.")
  return res.blob()
}

export function slicePart(partId: string): Promise<SliceResult> {
  return post(partUrl(partId, "slice"), {})
}

export function fetchPrinters(): Promise<Workshop> {
  return get("/api/printers")
}

export function addPrinter(profile: string): Promise<Workshop> {
  return post("/api/printers", { profile })
}

export function setDefaultPrinter(profile: string): Promise<Workshop> {
  return post("/api/printers/default", { profile })
}

export async function removePrinter(profile: string): Promise<Workshop> {
  const url = `/api/printers/${encodeURIComponent(profile)}`
  const res = await fetch(base + url, { method: "DELETE" })
  if (!res.ok) throw await refusal(res, "That printer did not come off the list.")
  return (await res.json()) as Workshop
}

export function setPrinter(projectId: string, profile: string): Promise<{ printer: Printer }> {
  return post(`/api/projects/${encodeURIComponent(projectId)}/printer`, { profile })
}

/**
 * Put one line of the conversation in the transcript. Naming a part files the
 * line under that part; without one it belongs to the folder's own conversation.
 */
export function addMessage(
  projectId: string,
  role: "user" | "assistant",
  content: string,
  part?: string | null
): Promise<Message> {
  return post(`/api/projects/${encodeURIComponent(projectId)}/messages`, { role, content, part })
}

/** A folder is a project the person named; without one the project holds a single part. */
export function createProject(name?: string, folder = false): Promise<{ id: string; name: string }> {
  return post("/api/projects", name === undefined ? { folder } : { name, folder })
}

/** Give the part's own container a name, and it becomes a folder others can join. */
export function promoteToFolder(id: string, name: string): Promise<ProjectSummary> {
  return post(projectUrl(id, "folder"), { name })
}

/** Move one part into another project. Refused when that project has the name already. */
export function movePart(partId: string, projectId: string): Promise<{ id: string; project_id: string }> {
  return post(partUrl(partId, "project"), { project_id: projectId })
}

export function importFolder(path: string): Promise<{ id: string; name: string; parts: number }> {
  return post("/api/import", { path })
}

/** Call a project something else. The name is a label, so nothing on disk moves. */
/** A project read as a system: its shared files with their settings (the plain
 * numbers at the top of each) and pieces (the functions parts call), and its
 * measurements, each with the parts that rebuild when it changes. */
export interface ProjectSystem {
  files: {
    name: string
    used_by: string[]
    settings: { name: string; value: number; kind: "int" | "float"; note: string }[]
    pieces: { name: string; used_by: string[] }[]
  }[]
  /** What sibling parts build twice: a system waiting to be lifted. */
  repeats: { parts: string[]; statements: number; source: string }[]
  measurements: { name: string; value_mm: number; how: string; provisional: boolean; used_by: string[] }[]
}

export async function getSystem(id: string): Promise<ProjectSystem> {
  const url = `/api/projects/${encodeURIComponent(id)}/system`
  const res = await fetch(base + url)
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
  return (await res.json()) as ProjectSystem
}

/** Set one number in a shared file; every part that imports it rebuilds. */
export async function setSetting(id: string, file: string, name: string, value: number): Promise<ProjectSystem> {
  const url = `/api/projects/${encodeURIComponent(id)}/settings`
  const res = await fetch(base + url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file, name, value }),
  })
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
  return (await res.json()) as ProjectSystem
}

/** Correct a measurement's value; every part that reads it rebuilds. */
export async function setMeasurement(id: string, name: string, valueMm: number): Promise<ProjectSystem> {
  const url = `/api/projects/${encodeURIComponent(id)}/measurements/${encodeURIComponent(name)}`
  const res = await fetch(base + url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value_mm: valueMm }),
  })
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
  return (await res.json()) as ProjectSystem
}

/** Write a project out as a folder of part files (the 0.x layout) at `directory`,
 * which must be empty or not exist yet. */
export async function exportProject(id: string, directory: string): Promise<{ directory: string; parts: string[] }> {
  const url = `/api/projects/${encodeURIComponent(id)}/checkout`
  const res = await fetch(base + url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ directory }),
  })
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
  return (await res.json()) as { directory: string; parts: string[] }
}

/** Call a part something else. The engine turns what was typed into a part name
 * ("Shelf Bracket" is shelf_bracket) and says what it was before. */
export async function renamePart(
  id: string,
  name: string,
): Promise<{ id: string; name: string; title: string | null; was: string }> {
  const url = `/api/parts/${encodeURIComponent(id)}`
  const res = await fetch(base + url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
  return (await res.json()) as { id: string; name: string; title: string | null; was: string }
}

export async function renameProject(id: string, name: string): Promise<ProjectSummary> {
  const url = `/api/projects/${encodeURIComponent(id)}`
  const res = await fetch(base + url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
  return (await res.json()) as ProjectSummary
}

export async function deleteProject(id: string): Promise<void> {
  const url = `/api/projects/${encodeURIComponent(id)}`
  const res = await fetch(base + url, { method: "DELETE" })
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
}

/** Delete a part and its revisions. A part alone in its container takes the container with it. */
export async function deletePart(id: string): Promise<{ project_id: string; project_deleted: boolean }> {
  const url = `/api/parts/${encodeURIComponent(id)}`
  const res = await fetch(base + url, { method: "DELETE" })
  if (!res.ok) throw await refusal(res, `${url} answered ${res.status}`)
  return (await res.json()) as { project_id: string; project_deleted: boolean }
}
