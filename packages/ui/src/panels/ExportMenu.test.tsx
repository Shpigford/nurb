import { describe, it, expect, vi, afterEach } from "vitest"
import { render, screen, cleanup, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import ExportMenu, { type ExportResult } from "./ExportMenu"

function deferred() {
  let resolve!: (value: ExportResult) => void
  let reject!: (reason: Error) => void
  const promise = new Promise<ExportResult>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

const open = async () => userEvent.click(screen.getByRole("button", { name: /Download/ }))

describe("ExportMenu", () => {
  afterEach(cleanup)

  it("offers every print format", async () => {
    render(<ExportMenu partId="shelf" export={vi.fn()} />)
    await open()
    for (const format of ["3mf", "stl", "step"]) {
      expect(screen.getByRole("menuitem", { name: new RegExp(format, "i") })).toBeInTheDocument()
    }
  })

  it("shows a pending state while the export promise is unresolved and the download state after it resolves", async () => {
    const pending = deferred()
    render(<ExportMenu partId="shelf" export={() => pending.promise} />)
    await open()
    await userEvent.click(screen.getByRole("menuitem", { name: /3mf/i }))

    expect(screen.getByText("preparing")).toBeInTheDocument()
    expect(screen.queryByRole("link")).toBeNull()

    pending.resolve({ url: "/exports/shelf_bracket.3mf", filename: "shelf_bracket.3mf" })

    await waitFor(() => expect(screen.getByRole("link", { name: /shelf_bracket.3mf/ })).toBeInTheDocument())
    expect(screen.getByRole("link", { name: /shelf_bracket.3mf/ })).toHaveAttribute(
      "href",
      "/exports/shelf_bracket.3mf"
    )
    expect(screen.queryByText("preparing")).toBeNull()
  })

  it("passes the chosen format to the host", async () => {
    const run = vi.fn().mockResolvedValue({ url: "/exports/a.stl" })
    render(<ExportMenu partId="shelf" export={run} />)
    await open()
    await userEvent.click(screen.getByRole("menuitem", { name: /stl/i }))
    await waitFor(() => expect(run).toHaveBeenCalledWith("stl"))
  })

  it("shows the reason when the export rejects", async () => {
    const run = vi.fn().mockRejectedValue(new Error("the slicer is not installed"))
    render(<ExportMenu partId="shelf" export={run} />)
    await open()
    await userEvent.click(screen.getByRole("menuitem", { name: /step/i }))
    await waitFor(() => expect(screen.getByText("the slicer is not installed")).toBeInTheDocument())
    expect(screen.queryByRole("link")).toBeNull()
  })

  it("clears a ready export when the revision changes", async () => {
    const run = vi.fn().mockResolvedValue({ url: "/exports/old.step", filename: "old.step" })
    const { rerender } = render(<ExportMenu partId="shelf" export={run} revision={1} />)
    await open()
    await userEvent.click(screen.getByRole("menuitem", { name: /step/i }))
    await waitFor(() => expect(screen.getByRole("link", { name: /old.step/ })).toBeInTheDocument())

    rerender(<ExportMenu partId="shelf" export={run} revision={2} />)

    await waitFor(() => expect(screen.queryByRole("link")).toBeNull())
  })

  it("ignores an export that finishes after the revision changes", async () => {
    const oldExport = deferred()
    const newExport = deferred()
    const run = vi.fn().mockReturnValueOnce(oldExport.promise).mockReturnValueOnce(newExport.promise)
    const { rerender } = render(<ExportMenu partId="shelf" export={run} revision={1} />)
    await open()
    await userEvent.click(screen.getByRole("menuitem", { name: /3mf/i }))

    rerender(<ExportMenu partId="shelf" export={run} revision={2} />)
    await waitFor(() => expect(screen.queryByText("preparing")).toBeNull())
    await userEvent.click(screen.getByRole("menuitem", { name: /stl/i }))
    oldExport.resolve({ url: "/exports/old.3mf", filename: "old.3mf" })
    newExport.resolve({ url: "/exports/new.stl", filename: "new.stl" })

    await waitFor(() => expect(screen.getByRole("link", { name: /new.stl/ })).toBeInTheDocument())
    expect(screen.queryByRole("link", { name: /old.3mf/ })).toBeNull()
  })

  it("ignores a late export after switching parts at the same revision", async () => {
    const shelfExport = deferred()
    const bracketExport = deferred()
    const run = vi.fn().mockReturnValueOnce(shelfExport.promise).mockReturnValueOnce(bracketExport.promise)
    const { rerender } = render(<ExportMenu partId="shelf" export={run} revision={1} />)
    await open()
    await userEvent.click(screen.getByRole("menuitem", { name: /3mf/i }))

    rerender(<ExportMenu partId="bracket" export={run} revision={1} />)
    await waitFor(() => expect(screen.queryByText("preparing")).toBeNull())
    await userEvent.click(screen.getByRole("menuitem", { name: /stl/i }))
    bracketExport.resolve({ url: "/exports/bracket.stl", filename: "bracket.stl" })
    await waitFor(() => expect(screen.getByRole("link", { name: /bracket.stl/ })).toBeInTheDocument())

    shelfExport.resolve({ url: "/exports/shelf.3mf", filename: "shelf.3mf" })
    await shelfExport.promise
    expect(screen.getByRole("link", { name: /bracket.stl/ })).toBeInTheDocument()
    expect(screen.queryByRole("link", { name: /shelf.3mf/ })).toBeNull()
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

  it("hands the keyboard back to the button when Escape closes the menu", async () => {
    render(<ExportMenu partId="shelf" export={vi.fn()} />)
    await open()
    await userEvent.keyboard("{ArrowDown}")
    await userEvent.keyboard("{Escape}")
    expect(screen.getByRole("button", { name: /Download/ })).toHaveFocus()
  })

  it("drops the prepared file when a new build lands, without closing the menu", async () => {
    const run = vi.fn().mockResolvedValue({ url: "blob:one", filename: "shelf.stl" })
    const { rerender } = render(<ExportMenu partId="shelf" export={run} revision={3} runId="run-1" />)
    await open()
    await userEvent.click(screen.getByRole("menuitem", { name: /stl/i }))
    await waitFor(() => expect(screen.getByRole("link", { name: /shelf.stl/ })).toBeInTheDocument())

    rerender(<ExportMenu partId="shelf" export={run} revision={3} runId="run-2" />)
    expect(screen.queryByRole("link", { name: /shelf.stl/ })).toBeNull()
    expect(screen.getByRole("menuitem", { name: /stl/i })).toBeInTheDocument()
  })
})
