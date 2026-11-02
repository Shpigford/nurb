import { act, fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import App from "./App"
import { part, project, summaries } from "./fixtures"
import type { Part, Project } from "./api"
import { FakeSocket, installSocket } from "./socket-stub"

// The real island needs WebGL; the stage's data attribute is what the tests read.
const heard = vi.hoisted(() => [] as string[])
vi.mock("@nurb/ui", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@nurb/ui")>()
  return {
    ...actual,
    ViewerIsland: () => <div data-testid="viewer" />,
    cue: (name: string) => heard.push(name),
  }
})

interface Call {
  url: string
  method: string
  body: Record<string, unknown> | null
}

let calls: Call[] = []
let state: Project

const base = part("lid", "/glb/p2/lid.glb?run=1")

function withPart(over: Partial<Part>): Project {
  return project("p2", "Second", [{ ...base, ...over }])
}

function sent(tail: string) {
  return calls.filter((c) => c.url.endsWith(tail) && c.method === "POST")
}

function install(routes: Record<string, (body: Record<string, unknown> | null) => unknown> = {}) {
  vi.stubGlobal("fetch", async (url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET"
    const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null
    calls.push({ url, method, body })
    if (url === "/api/projects") return new Response(JSON.stringify({ projects: summaries }))
    if (url === "/api/projects/p2" && method === "GET") return new Response(JSON.stringify(state))
    const handler = routes[`${method} ${url}`]
    if (!handler) return new Response("nothing here", { status: 404 })
    const answer = handler(body)
    return answer instanceof Response ? answer : new Response(JSON.stringify(answer))
  })
}

beforeEach(() => {
  calls = []
  heard.length = 0
  state = withPart({})
  installSocket()
  URL.createObjectURL = vi.fn(() => "blob:lid") as never
  URL.revokeObjectURL = vi.fn() as never
  history.replaceState(null, "", "/?project=p2&part=lid")
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe("sliders", () => {
  it("posts the whole value map once, after the debounce", async () => {
    state = withPart({
      params: [
        { name: "wall", kind: "float", default: 2 },
        { name: "ribs", kind: "int", default: 4 },
      ],
      overrides: { ribs: 6 },
    })
    install({ "POST /api/parts/part-lid/params": () => ({ build: base.build }) })
    render(<App />)

    // The panel opens on the declared defaults and takes the run's overrides a
    // moment later; a drag before that would be measuring the wrong start.
    await waitFor(() => expect(screen.getByLabelText("ribs value")).toHaveValue("6"))
    const wall = screen.getByLabelText("wall")
    vi.useFakeTimers()
    fireEvent.change(wall, { target: { value: "3" } })
    act(() => void vi.advanceTimersByTime(100))
    expect(sent("/params")).toHaveLength(0)

    act(() => void vi.advanceTimersByTime(200))
    vi.useRealTimers()
    await waitFor(() => expect(sent("/params")).toHaveLength(1))
    expect(sent("/params")[0].body).toEqual({ values: { ribs: 6, wall: 3 } })
  })

  it("builds nothing when a number field is clicked and left unchanged", async () => {
    // Issue #304: the rebuild also started a slice and turned the view.
    state = withPart({ params: [{ name: "wall", kind: "float", default: 2 }], overrides: { wall: 3 } })
    install({ "POST /api/parts/part-lid/params": () => ({ build: base.build }) })
    render(<App />)

    await waitFor(() => expect(screen.getByLabelText("wall value")).toHaveValue("3"))
    const field = screen.getByLabelText("wall value")
    vi.useFakeTimers()
    fireEvent.focus(field)
    fireEvent.blur(field)
    act(() => void vi.advanceTimersByTime(1000))
    vi.useRealTimers()
    expect(sent("/params")).toHaveLength(0)
  })

  it("cues once when a rebuild the user watched comes back passing", async () => {
    state = withPart({ params: [{ name: "wall", kind: "float", default: 2 }] })
    install({ "POST /api/parts/part-lid/params": () => ({ build: base.build }) })
    render(<App />)

    await waitFor(() => expect(screen.getByLabelText("wall")).toBeInTheDocument())
    // Opening a part that was already built is not news, so nothing has sounded yet.
    expect(heard).not.toContain("ready")

    vi.useFakeTimers()
    fireEvent.change(screen.getByLabelText("wall"), { target: { value: "3" } })
    act(() => void vi.advanceTimersByTime(300))
    vi.useRealTimers()
    // One cue per build, not one per frame of the drag.
    await waitFor(() => expect(heard.filter((c) => c === "ready")).toHaveLength(1))
  })

  it("locks a dimension the spec pinned instead of offering it as a slider", async () => {
    state = {
      ...withPart({
        params: [
          { name: "wall", kind: "float", default: 2 },
          { name: "rail_width", kind: "float", default: 25.16 },
        ],
      }),
      spec: {
        part_name: "lid",
        summary: "A lid",
        params: [],
        dimensions: [{ name: "rail_width", value_mm: 25.16, how: "calipers", provisional: false }],
        acceptance: [],
        conventions: { expose_params: true, parameter_style: "keyword" },
      },
    }
    install()
    render(<App />)

    await screen.findByLabelText("wall")
    expect(screen.getByText("Set by the plan")).toBeInTheDocument()
    expect(screen.getByText("25.16 mm")).toBeInTheDocument()
    expect(screen.queryByLabelText("rail_width")).toBeNull()
  })

  it("drops a queued rebuild when the view goes away", async () => {
    install({ "POST /api/parts/part-lid/params": () => ({ build: base.build }) })
    const view = render(<App />)

    const wall = await screen.findByLabelText("wall")
    vi.useFakeTimers()
    fireEvent.change(wall, { target: { value: "3" } })
    act(() => void vi.advanceTimersByTime(100))
    view.unmount()
    act(() => void vi.advanceTimersByTime(400))
    vi.useRealTimers()

    expect(sent("/params")).toHaveLength(0)
  })

  it("shows the server's sentence when a rebuild is refused, and keeps the sliders", async () => {
    install({
      "POST /api/parts/part-lid/params": () =>
        new Response(JSON.stringify({ error: "build lid once before changing its parameters" }), {
          status: 400,
        }),
    })
    render(<App />)

    const wall = await screen.findByLabelText("wall")
    vi.useFakeTimers()
    fireEvent.change(wall, { target: { value: "3" } })
    act(() => void vi.advanceTimersByTime(300))
    vi.useRealTimers()

    // The refusal renders after the response body is read; a loaded CI runner has
    // missed the default one-second window for both the request and the sentence.
    await waitFor(() => expect(sent("/params")).toHaveLength(1), { timeout: 5000 })
    expect(
      await screen.findByText("build lid once before changing its parameters", {}, { timeout: 5000 })
    ).toBeInTheDocument()
    expect(screen.getByLabelText("wall")).toBeInTheDocument()
  })

  it("swaps the stage geometry when the rebuild lands", async () => {
    install()
    render(<App />)
    await waitFor(() =>
      expect(screen.getByTestId("stage")).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=1")
    )

    state = withPart({ build: { ...base.build!, id: "b2", glb_url: "/glb/p2/lid.glb?run=b2" } })
    FakeSocket.instances[0].emit({ kind: "build", id: "b2", project_id: "p2" })
    await waitFor(() =>
      expect(screen.getByTestId("stage")).toHaveAttribute("data-glb-url", "/glb/p2/lid.glb?run=b2")
    )
  })
})

describe("first build", () => {
  it("builds a part that has never built, from the stage", async () => {
    state = withPart({ build: null, params: [] })
    install({ "POST /api/parts/part-lid/params": () => ({ build: base.build }) })
    render(<App />)

    await userEvent.click(await screen.findByRole("button", { name: "Build lid" }))
    await waitFor(() => expect(sent("/params")).toHaveLength(1))
    expect(sent("/params")[0].body).toEqual({ values: {} })
  })
})

describe("apply", () => {
  it("sends only what moved and names the revision it saved", async () => {
    state = withPart({ overrides: { wall: 3 } })
    install({
      "POST /api/parts/part-lid/apply": () => ({
        revision_id: "r2",
        revision: 4,
        written: ["wall"],
        skipped: [],
        build: base.build,
      }),
    })
    render(<App />)

    await userEvent.click(await screen.findByRole("button", { name: "Save as default" }))
    await waitFor(() => expect(sent("/apply")).toHaveLength(1))
    expect(sent("/apply")[0].body).toEqual({ values: { wall: 3 } })
    expect(await screen.findByText("Saved as rev 4. wall 2 → 3")).toBeInTheDocument()
  })
})

const BENCH = {
  printers: [
    { name: "bambu_x1c", label: "Bambu Lab X1 Carbon", brand: "Bambu Lab", bed: [256, 256, 256], default: true },
    { name: "prusa_mk4", label: "Prusa MK4", brand: "Prusa", bed: [250, 210, 220], default: false },
  ],
  catalogue: [
    { name: "bambu_x1c", label: "Bambu Lab X1 Carbon", brand: "Bambu Lab", bed: [256, 256, 256] },
    { name: "prusa_mk4", label: "Prusa MK4", brand: "Prusa", bed: [250, 210, 220] },
    { name: "ender_3", label: "Creality Ender 3", brand: "Creality", bed: [220, 220, 250] },
  ],
  slicers: [{ name: "OrcaSlicer", path: "/Applications/OrcaSlicer.app" }],
  opener: { name: "OrcaSlicer", path: "/Applications/OrcaSlicer.app" },
}

describe("print time", () => {
  it("asks which printer, then names one and slices again", async () => {
    state = withPart({
      build: { ...base.build!, slice: { kind: "choose", profiles: ["bambu_x1c", "prusa_mk4"] } },
    })
    install({
      "GET /api/printers": () => BENCH,
      "POST /api/projects/p2/printer": () => ({ printer: { name: "prusa_mk4", bed: [250, 210, 220] } }),
    })
    render(<App />)

    expect(await screen.findByText("Which printer is this part for?")).toBeInTheDocument()
    await userEvent.click(await screen.findByRole("button", { name: "choose a printer" }))
    await userEvent.click(await screen.findByRole("menuitemradio", { name: /Prusa MK4/ }))

    await waitFor(() => expect(sent("/printer")).toHaveLength(1))
    expect(sent("/printer")[0].body).toEqual({ profile: "prusa_mk4" })
    expect(sent("/api/parts/part-lid/slice")).toHaveLength(1)
  })

  it("offers the catalogue when the bench is empty, and adds the one picked", async () => {
    state = { ...withPart({ build: { ...base.build!, slice: null } }), printer: null, printers: [] }
    install({
      "GET /api/printers": () => ({ ...BENCH, printers: [] }),
      "POST /api/printers": () => BENCH,
      "POST /api/projects/p2/printer": () => ({ printer: { name: "prusa_mk4", bed: [250, 210, 220] } }),
      "POST /api/parts/part-lid/slice": () => ({ kind: "slice", profile: "prusa_mk4", grams: 42 }),
    })
    render(<App />)

    // The closed row says NO PRINTER; the answer to it is inside.
    await userEvent.click(await screen.findByRole("button", { name: /SLICE/ }))
    expect(await screen.findByText(/No printer yet/)).toBeInTheDocument()
    await userEvent.click(await screen.findByRole("button", { name: "Add a printer" }))
    await userEvent.click(await screen.findByRole("button", { name: /Prusa MK4/ }))
    await userEvent.click(screen.getByRole("button", { name: "Add printer" }))

    await waitFor(() => expect(sent("/api/printers")).toHaveLength(1))
    expect(sent("/api/printers")[0].body).toEqual({ profile: "prusa_mk4" })
    await waitFor(() => expect(sent("/printer")).toHaveLength(1))
  })

  it("shuts the picker on a second press of CHANGE", async () => {
    state = {
      ...withPart({
        build: { ...base.build!, slice: { kind: "slice", profile: "prusa_mk4", grams: 42, seconds: 4320 } },
      }),
      printer: { name: "prusa_mk4", bed: [250, 210, 220] },
      printers: ["prusa_mk4"],
    }
    install({ "GET /api/printers": () => BENCH })
    render(<App />)

    const change = await screen.findByRole("button", { name: "change" })
    await userEvent.click(change)
    expect(await screen.findByRole("menu", { name: "Print on" })).toBeInTheDocument()

    // The outside-click listener must not eat the press that the trigger toggles on.
    await userEvent.click(change)
    await waitFor(() => expect(screen.queryByRole("menu", { name: "Print on" })).toBeNull())
  })

  it("puts a failure after the add in the row, not in a dialog that has gone", async () => {
    state = { ...withPart({ build: { ...base.build!, slice: null } }), printer: null, printers: [] }
    install({
      "GET /api/printers": () => ({ ...BENCH, printers: [] }),
      "POST /api/printers": () => BENCH,
      "POST /api/projects/p2/printer": () =>
        new Response(JSON.stringify({ error: "prusa_mk4 is not on your bench" }), { status: 400 }),
    })
    render(<App />)

    await userEvent.click(await screen.findByRole("button", { name: /SLICE/ }))
    await userEvent.click(await screen.findByRole("button", { name: "Add a printer" }))
    await userEvent.click(await screen.findByRole("button", { name: /Prusa MK4/ }))
    await userEvent.click(screen.getByRole("button", { name: "Add printer" }))

    expect(await screen.findByText("prusa_mk4 is not on your bench")).toBeInTheDocument()
    expect(screen.queryByRole("dialog")).toBeNull()
  })

  it("keeps the part's own printer out of the empty-bench state", async () => {
    state = {
      ...withPart({ build: { ...base.build!, slice: { kind: "slicer" } } }),
      printer: { name: "prusa_mk4", bed: [250, 210, 220] },
      printers: ["prusa_mk4"],
    }
    install({ "GET /api/printers": () => ({ ...BENCH, printers: [] }) })
    render(<App />)

    expect(await screen.findByText("no slicer found")).toBeInTheDocument()
    expect(screen.queryByText(/No printer yet/)).toBeNull()
  })

  it("leaves a way back to another printer when the slicer refuses this one", async () => {
    state = {
      ...withPart({
        build: {
          ...base.build!,
          slice: { kind: "profile", error: "OrcaSlicer has no profile for prusa_mk4." },
        },
      }),
      printer: { name: "prusa_mk4", bed: [250, 210, 220] },
      printers: ["prusa_mk4"],
    }
    install({ "GET /api/printers": () => BENCH })
    render(<App />)

    expect(await screen.findByText("OrcaSlicer has no profile for prusa_mk4.")).toBeInTheDocument()
    expect(await screen.findByText("Prusa MK4")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "change" })).toBeInTheDocument()
  })

  it("refetches the bench when a printer changes in Settings", async () => {
    state = {
      ...withPart({
        build: { ...base.build!, slice: { kind: "slice", profile: "prusa_mk4", grams: 42, seconds: 4320 } },
      }),
      printer: { name: "prusa_mk4", bed: [250, 210, 220] },
      printers: ["prusa_mk4"],
    }
    install({ "GET /api/printers": () => BENCH })
    render(<App />)

    await waitFor(() => expect(calls.filter((c) => c.url === "/api/printers")).toHaveLength(1))
    FakeSocket.instances[0].emit({ kind: "workshop", id: "prusa_mk4", project_id: "" })
    await waitFor(() => expect(calls.filter((c) => c.url === "/api/printers").length).toBeGreaterThan(1))
  })
})

describe("download", () => {
  it("downloads the remembered type in one click", async () => {
    install({ "POST /api/parts/part-lid/export": () => new Response("3mf bytes") })
    const clicked: HTMLAnchorElement[] = []
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      clicked.push(this)
    })
    render(<App />)

    await userEvent.click(await screen.findByRole("button", { name: "Download 3MF" }))

    await waitFor(() => expect(clicked).toHaveLength(1))
    expect(clicked[0].download).toBe("lid.3mf")
    expect(sent("/export")[0].body).toEqual({ format: "3mf", values: {} })
    click.mockRestore()
  })

  it("downloads the values the newest build used, after someone else rebuilt the part", async () => {
    state = withPart({ params: [{ name: "wall", kind: "float", default: 2 }], overrides: { wall: 3 } })
    install({ "POST /api/parts/part-lid/export": () => new Response("3mf bytes") })
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {})
    render(<App />)
    await waitFor(() => expect(screen.getByLabelText("wall value")).toHaveValue("3"))

    // The chat edit removed the parameter and rebuilt at the source defaults.
    state = withPart({ params: [], overrides: {}, build: { ...base.build!, id: "b2" } })
    FakeSocket.instances[0].emit({ kind: "build", id: "b2", project_id: "p2" })
    await waitFor(() => expect(screen.queryByLabelText("wall value")).not.toBeInTheDocument())

    await userEvent.click(await screen.findByRole("button", { name: "Download 3MF" }))
    await waitFor(() => expect(sent("/export")).toHaveLength(1))
    expect(sent("/export")[0].body).toEqual({ format: "3mf", values: {} })
    click.mockRestore()
  })

  it("tells the shell the export started and landed, under one id", async () => {
    install({ "POST /api/parts/part-lid/export": () => new Response("3mf bytes") })
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {})
    const said: { id: string; title: string; detail?: string; tone: string }[] = []
    const listen = (event: Event) => said.push((event as CustomEvent<(typeof said)[number]>).detail)
    window.addEventListener("nurb:activity", listen)
    render(<App />)

    await userEvent.click(await screen.findByRole("button", { name: "Download 3MF" }))
    await waitFor(() => expect(said).toHaveLength(2))
    window.removeEventListener("nurb:activity", listen)
    click.mockRestore()

    expect(said.map((a) => a.tone)).toEqual(["working", "done"])
    expect(said[0].title).toBe("Exporting lid.3mf")
    expect(said[1]).toMatchObject({ id: said[0].id, detail: "Saved" })
  })
})

describe("rail rows", () => {
  it("opens the row that has something to say and leaves the others closed", async () => {
    state = withPart({
      build: {
        ...base.build!,
        findings: [{ rule: "overhang", severity: "warn", message: "chamfer to 45° for support-free" }],
      },
    })
    install()
    render(<App />)

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /CHECKS/ })).toHaveAttribute("aria-expanded", "true")
    )
  })

  it("keeps CHECKS closed on a clean build, and opens SLICE on a seeded price", async () => {
    state = withPart({
      build: { ...base.build!, slice: { kind: "slice", seconds: 4320, grams: 42, run_id: "b1" } },
    })
    install()
    render(<App />)

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /SLICE/ })).toHaveAttribute("aria-expanded", "true")
    )
    expect(screen.getByRole("button", { name: /CHECKS/ })).toHaveAttribute("aria-expanded", "false")
  })
})
