import { describe, it, expect, vi, afterEach } from "vitest"
import { render, screen, cleanup, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import ExportMenu from "./ExportMenu"

function deferred() {
  let resolve!: () => void
  let reject!: (reason: Error) => void
  const promise = new Promise<void>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

// The test DOM has no storage of its own; the menu only needs these three calls.
const store = new Map<string, string>()
vi.stubGlobal("localStorage", {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => void store.set(key, value),
  clear: () => store.clear(),
})

const chooser = () => screen.getByRole("button", { name: "Choose file type" })
const open = async () => userEvent.click(chooser())

describe("ExportMenu", () => {
  afterEach(() => {
    cleanup()
    localStorage.clear()
  })

  it("downloads a 3MF in one click, without asking", async () => {
    const run = vi.fn().mockResolvedValue(undefined)
    render(<ExportMenu partId="shelf" export={run} />)
    await userEvent.click(screen.getByRole("button", { name: "Download 3MF" }))
    expect(run).toHaveBeenCalledWith("3mf")
    expect(screen.queryByRole("menu")).toBeNull()
  })

  it("offers the slicer only when there is one, and hands it the file instead of downloading", async () => {
    const run = vi.fn().mockResolvedValue(undefined)
    const send = vi.fn().mockResolvedValue(undefined)
    render(<ExportMenu partId="shelf" export={run} />)
    await open()
    expect(screen.queryByRole("menuitem", { name: /open in/i })).toBeNull()

    cleanup()
    render(<ExportMenu partId="shelf" export={run} openIn={{ name: "Bambu Studio", open: send }} />)
    await open()
    await userEvent.click(screen.getByRole("menuitem", { name: /open in bambu studio/i }))
    await waitFor(() => expect(send).toHaveBeenCalledTimes(1))
    expect(run).not.toHaveBeenCalled()
    await waitFor(() => expect(screen.queryByRole("menu")).toBeNull())
  })

  it("offers every print format behind the chevron", async () => {
    render(<ExportMenu partId="shelf" export={vi.fn()} />)
    await open()
    for (const format of ["3mf", "stl", "step"]) {
      expect(screen.getByRole("menuitem", { name: new RegExp(format, "i") })).toBeInTheDocument()
    }
  })

  it("downloads a chosen type and remembers it for next time", async () => {
    const run = vi.fn().mockResolvedValue(undefined)
    render(<ExportMenu partId="shelf" export={run} />)
    await open()
    await userEvent.click(screen.getByRole("menuitem", { name: /stl/i }))
    await waitFor(() => expect(run).toHaveBeenCalledWith("stl"))
    await waitFor(() => expect(screen.queryByRole("menu")).toBeNull())

    cleanup()
    render(<ExportMenu partId="bracket" export={run} />)
    await userEvent.click(screen.getByRole("button", { name: "Download STL" }))
    expect(run).toHaveBeenLastCalledWith("stl")
  })

  it("says it is preparing until the export settles", async () => {
    const pending = deferred()
    render(<ExportMenu partId="shelf" export={() => pending.promise} />)
    await userEvent.click(screen.getByRole("button", { name: "Download 3MF" }))
    expect(screen.getByRole("button", { name: /Preparing/ })).toBeDisabled()

    pending.resolve()
    await waitFor(() => expect(screen.getByRole("button", { name: "Download 3MF" })).toBeEnabled())
  })

  it("opens the menu to show why an export failed", async () => {
    const run = vi.fn().mockRejectedValue(new Error("the slicer is not installed"))
    render(<ExportMenu partId="shelf" export={run} />)
    await userEvent.click(screen.getByRole("button", { name: "Download 3MF" }))
    await waitFor(() => expect(screen.getByText("the slicer is not installed")).toBeInTheDocument())
    expect(screen.getByRole("menu")).toBeInTheDocument()
  })

  it("ignores a failure that lands after the build changed", async () => {
    const old = deferred()
    const { rerender } = render(<ExportMenu partId="shelf" export={() => old.promise} revision={1} runId="run-1" />)
    await userEvent.click(screen.getByRole("button", { name: "Download 3MF" }))

    rerender(<ExportMenu partId="shelf" export={() => old.promise} revision={2} runId="run-2" />)
    await waitFor(() => expect(screen.getByRole("button", { name: "Download 3MF" })).toBeEnabled())
    old.reject(new Error("stale"))
    await old.promise.catch(() => {})
    expect(screen.queryByText("stale")).toBeNull()
  })

  it("marks the remembered type in the menu", async () => {
    localStorage.setItem("nurb.exportFormat", "step")
    render(<ExportMenu partId="shelf" export={vi.fn()} />)
    expect(screen.getByRole("button", { name: "Download STEP" })).toBeInTheDocument()
    await open()
    expect(screen.getByRole("menuitem", { name: /step/i })).toHaveAttribute("aria-current", "true")
  })

  it("walks the formats with the arrow keys", async () => {
    render(<ExportMenu partId="shelf" export={vi.fn()} />)
    await open()
    await userEvent.keyboard("{ArrowDown}")
    expect(screen.getByRole("menuitem", { name: /3mf/i })).toHaveFocus()
    await userEvent.keyboard("{ArrowDown}")
    expect(screen.getByRole("menuitem", { name: /stl/i })).toHaveFocus()
    await userEvent.keyboard("{ArrowUp}")
    expect(screen.getByRole("menuitem", { name: /3mf/i })).toHaveFocus()
  })

  it("reads the slicer estimate from the status prop", async () => {
    render(<ExportMenu partId="shelf" export={vi.fn()} status={{ state: "succeeded", grams: 42.4, seconds: 5400 }} revision={7} />)
    await open()
    expect(screen.getByText("Estimate · 42 g · 1.5 hr")).toBeInTheDocument()
    expect(screen.getByText("REV 07")).toBeInTheDocument()
  })

  it("hands the keyboard back to the chevron when Escape closes the menu", async () => {
    render(<ExportMenu partId="shelf" export={vi.fn()} />)
    await open()
    await userEvent.keyboard("{ArrowDown}")
    await userEvent.keyboard("{Escape}")
    expect(chooser()).toHaveFocus()
  })
})
