import { describe, it, expect, vi, afterEach } from "vitest"
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { useState } from "react"
import ParamsPanel from "./ParamsPanel"
import type { Param, Params } from "../types"

const params: Param[] = [
  { name: "width", kind: "float", default: 40.0, description: "outside width" },
  { name: "bracket_count", kind: "int", default: 4 },
  { name: "draft", kind: "bool", default: false },
  { name: "finish", kind: "str", default: "matte" },
]

// jsdom has no PointerEvent, so a fired one carries no clientX. A MouseEvent of
// the same type does, and React reads the coordinates straight off it.
function pointer(type: string, clientX: number) {
  return new MouseEvent(type, { bubbles: true, cancelable: true, clientX, button: 0 })
}

// The host owns the values, so the panel only reads them back through props.
function Host({ onApply }: { onApply: (values: Params) => void }) {
  const [values, setValues] = useState<Params>({})
  return <ParamsPanel params={params} values={values} onChange={setValues} onApply={onApply} />
}

describe("ParamsPanel", () => {
  // vitest runs with globals off, so Testing Library never registers its own cleanup.
  afterEach(cleanup)

  it("keeps control ids unique across two panels on one page", () => {
    render(
      <>
        <ParamsPanel params={params} values={{}} onChange={vi.fn()} onApply={vi.fn()} />
        <ParamsPanel params={params} values={{}} onChange={vi.fn()} onApply={vi.fn()} />
      </>
    )
    const ids = Array.from(document.querySelectorAll("[id]")).map((el) => el.id)
    expect(new Set(ids).size).toBe(ids.length)
    // Each label still reaches its own control, not the first one in the document.
    const sliders = screen.getAllByRole("slider", { name: "width" })
    expect(sliders).toHaveLength(2)
    const labels = screen.getAllByText("width")
    expect(labels.map((l) => (l as HTMLLabelElement).htmlFor)).toEqual(sliders.map((s) => s.id))
  })

  it("gives a dirty bool the same reset dot as a number, and announces the note", async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<ParamsPanel params={params} values={{ draft: true }} onChange={onChange} onApply={vi.fn()} note="Saved draft." />)
    expect(screen.getByText("Saved draft.")).toHaveAttribute("role", "status")
    await user.click(screen.getByRole("button", { name: "Reset draft to default" }))
    expect(onChange).toHaveBeenCalledWith({ draft: false })
  })

  it("gives every adjustable param a control and pins the rest", () => {
    render(<ParamsPanel params={params} values={{}} onChange={vi.fn()} onApply={vi.fn()} />)
    expect(screen.getByLabelText("width value")).toHaveValue("40")
    expect(screen.getByLabelText("bracket_count value")).toHaveValue("4")
    expect(screen.getByRole("switch", { name: "draft" })).toHaveAttribute("aria-checked", "false")
    expect(screen.getByText("Set by the plan")).toBeInTheDocument()
    expect(screen.queryByLabelText("finish value")).toBeNull()
  })

  it("calls onApply with the edited values when Save as default is clicked", async () => {
    const onApply = vi.fn()
    render(<Host onApply={onApply} />)

    const field = screen.getByLabelText("width value")
    await userEvent.clear(field)
    await userEvent.type(field, "55")
    await userEvent.tab()

    await userEvent.click(screen.getByRole("switch", { name: "draft" }))

    expect(screen.getByText("2 changes")).toBeInTheDocument()
    await userEvent.click(screen.getByRole("button", { name: "Save as default" }))
    expect(onApply).toHaveBeenCalledWith({ width: 55, draft: true })
  })

  it("commits a typed value when the field loses focus, and reverts it on Escape", () => {
    const onChange = vi.fn()
    render(<ParamsPanel params={params} values={{}} onChange={onChange} onApply={vi.fn()} />)
    const field = screen.getByLabelText("width value")

    // Clicking away is as much a commit as pressing Enter; the typed number is
    // what the user meant either way.
    fireEvent.change(field, { target: { value: "9" } })
    fireEvent.blur(field)
    expect(onChange).toHaveBeenCalledWith({ width: 9 })

    onChange.mockClear()
    fireEvent.change(field, { target: { value: "12" } })
    fireEvent.keyDown(field, { key: "Escape" })
    expect(onChange).not.toHaveBeenCalled()
    expect(field).toHaveValue("40")
  })

  it("hides the change strip until a value moves off its default", async () => {
    const onChange = vi.fn()
    const { rerender } = render(
      <ParamsPanel params={params} values={{ width: 40 }} onChange={onChange} onApply={vi.fn()} />
    )
    expect(screen.queryByRole("button", { name: "Save as default" })).toBeNull()

    rerender(<ParamsPanel params={params} values={{ width: 52 }} onChange={onChange} onApply={vi.fn()} />)
    expect(screen.getByText("1 change")).toBeInTheDocument()
  })

  it("resets every value with the Reset button", async () => {
    const onChange = vi.fn()
    render(<ParamsPanel params={params} values={{ width: 52 }} onChange={onChange} onApply={vi.fn()} />)
    await userEvent.click(screen.getByRole("button", { name: "Reset" }))
    expect(onChange).toHaveBeenCalledWith({})
  })

  it("moves a slider in whole steps for an int and tidied steps for a float", async () => {
    const onChange = vi.fn()
    render(<ParamsPanel params={params} values={{}} onChange={onChange} onApply={vi.fn()} />)
    expect(screen.getByRole("slider", { name: "bracket count" })).toHaveAttribute("step", "1")
    expect(screen.getByRole("slider", { name: "width" })).toHaveAttribute("step", "1")
  })

  it("keeps showing the controls when a build failed at these values", () => {
    render(
      <ParamsPanel
        params={params}
        values={{ width: 52 }}
        onChange={vi.fn()}
        onApply={vi.fn()}
        error="BRep_API: command not done"
      />
    )
    expect(screen.getByText("Build failed at these values")).toBeInTheDocument()
    expect(screen.getByLabelText("width value")).toHaveValue("52")
  })

  it("marks the default and every measurement that lands on the slider", () => {
    render(
      <ParamsPanel
        params={[{ name: "wall", kind: "float", default: 2.0 }]}
        values={{}}
        onChange={vi.fn()}
        onApply={vi.fn()}
        measurements={[{ value_mm: 1.6 }, { value_mm: 900 }]}
      />
    )
    // Parked on the default, so the readout names the stop it is sitting on.
    expect(screen.getByText("default")).toBeInTheDocument()
    expect(screen.getAllByTitle("measured")).toHaveLength(1)
    expect(screen.getAllByTitle("3 lines")).toHaveLength(1)
  })

  it("gives an int slider no stops at all", () => {
    render(<ParamsPanel params={params} values={{}} onChange={vi.fn()} onApply={vi.fn()} />)
    // Only the float row is marked; bracket_count carries nothing.
    expect(screen.getAllByTitle("default")).toHaveLength(1)
  })

  it("says how far the slider goes when a push lands on the end of the track", () => {
    const { rerender } = render(
      <ParamsPanel params={params} values={{ width: 80 }} onChange={vi.fn()} onApply={vi.fn()} />
    )
    fireEvent.keyDown(screen.getByRole("slider", { name: "width" }), { key: "ArrowRight" })
    expect(screen.getByText("80 mm · widest this will go")).toBeInTheDocument()

    rerender(<ParamsPanel params={params} values={{ width: 20 }} onChange={vi.fn()} onApply={vi.fn()} />)
    fireEvent.keyDown(screen.getByRole("slider", { name: "width" }), { key: "ArrowLeft" })
    expect(screen.getByText("20 mm · thinnest this will go")).toBeInTheDocument()
  })

  it("says the same thing when a drag keeps pushing past the end of the track", () => {
    render(<ParamsPanel params={params} values={{ width: 80 }} onChange={vi.fn()} onApply={vi.fn()} />)
    const slider = screen.getByRole("slider", { name: "width" })
    // jsdom lays nothing out, so the track has to be told where it is.
    slider.getBoundingClientRect = () =>
      ({ x: 0, y: 0, left: 0, right: 200, top: 0, bottom: 20, width: 200, height: 20, toJSON: () => ({}) }) as DOMRect

    fireEvent(slider, pointer("pointerdown", 195))
    fireEvent(slider, pointer("pointermove", 260))
    expect(screen.getByText("80 mm · widest this will go")).toBeInTheDocument()

    // Still one line: an excursion speaks once, not once per pixel.
    fireEvent(slider, pointer("pointermove", 300))
    expect(screen.getAllByText("80 mm · widest this will go")).toHaveLength(1)
  })

  it("stays quiet while the pointer is still over the track", () => {
    render(<ParamsPanel params={params} values={{ width: 80 }} onChange={vi.fn()} onApply={vi.fn()} />)
    const slider = screen.getByRole("slider", { name: "width" })
    slider.getBoundingClientRect = () =>
      ({ x: 0, y: 0, left: 0, right: 200, top: 0, bottom: 20, width: 200, height: 20, toJSON: () => ({}) }) as DOMRect

    fireEvent(slider, pointer("pointerdown", 100))
    fireEvent(slider, pointer("pointermove", 203))
    expect(screen.queryByText(/widest this will go/)).toBeNull()
  })

  it("says nothing while there is still track left", () => {
    render(<ParamsPanel params={params} values={{ width: 50 }} onChange={vi.fn()} onApply={vi.fn()} />)
    fireEvent.keyDown(screen.getByRole("slider", { name: "width" }), { key: "ArrowRight" })
    expect(screen.queryByText(/widest this will go/)).toBeNull()
  })

  it("scrubs the number field by one step every four pixels", () => {
    render(<Host onApply={vi.fn()} />)
    const field = screen.getByLabelText("width value")

    fireEvent(field, pointer("pointerdown", 100))
    fireEvent(field, pointer("pointermove", 120))
    expect(field).toHaveValue("45")
    fireEvent(field, pointer("pointerup", 120))
  })

  it("keeps the step it started the scrub with across a decimal boundary", () => {
    // Default 9.5 puts the slider on a grid of 0.1; a typed 9.25 refines it to 0.01.
    // Crossing back to one decimal mid-drag must not put the coarse grid back.
    const fine: Param[] = [{ name: "wall", kind: "float", default: 9.5 }]
    function FineHost() {
      const [values, setValues] = useState<Params>({ wall: 9.25 })
      return <ParamsPanel params={fine} values={values} onChange={setValues} onApply={vi.fn()} />
    }
    render(<FineHost />)
    const field = screen.getByLabelText("wall value")
    expect(field).toHaveValue("9.25")

    fireEvent(field, pointer("pointerdown", 100))
    fireEvent(field, pointer("pointermove", 120))
    expect(field).toHaveValue("9.3")
    fireEvent(field, pointer("pointermove", 124))
    expect(field).toHaveValue("9.31")
    fireEvent(field, pointer("pointermove", 128))
    expect(field).toHaveValue("9.32")
    fireEvent(field, pointer("pointerup", 128))
  })

  it("commits nothing when the field leaves with the number it already had", () => {
    // Issue #304: a click in and out rebuilt the part, and with a printer set, sliced it.
    const onChange = vi.fn()
    render(<ParamsPanel params={params} values={{}} onChange={onChange} onApply={vi.fn()} />)
    const field = screen.getByLabelText("width value")

    fireEvent.focus(field)
    fireEvent.blur(field)
    fireEvent.change(field, { target: { value: "40.0" } })
    fireEvent.keyDown(field, { key: "Enter" })
    expect(onChange).not.toHaveBeenCalled()
    expect(field).toHaveValue("40")
  })

  it("does not scrub on a plain click or a caret nudge", () => {
    render(<Host onApply={vi.fn()} />)
    const field = screen.getByLabelText("width value")

    fireEvent(field, pointer("pointerdown", 100))
    fireEvent(field, pointer("pointermove", 102))
    fireEvent(field, pointer("pointerup", 102))
    expect(field).toHaveValue("40")

    // And typing still commits exactly as it did before the drag existed.
    fireEvent.change(field, { target: { value: "9" } })
    fireEvent.blur(field)
    expect(field).toHaveValue("9")
  })

  it("puts back the number the drag started from when Escape lands mid-scrub", () => {
    render(<Host onApply={vi.fn()} />)
    const field = screen.getByLabelText("width value")

    fireEvent(field, pointer("pointerdown", 100))
    fireEvent(field, pointer("pointermove", 140))
    expect(field).toHaveValue("50")
    fireEvent.keyDown(field, { key: "Escape" })
    expect(field).toHaveValue("40")

    // The drag is over: more travel moves nothing.
    fireEvent(field, pointer("pointermove", 200))
    expect(field).toHaveValue("40")
  })

  it("steps the field with up and down, ten at a time with shift", () => {
    render(<Host onApply={vi.fn()} />)
    const field = screen.getByLabelText("width value")

    fireEvent.keyDown(field, { key: "ArrowUp" })
    expect(field).toHaveValue("41")
    fireEvent.keyDown(field, { key: "ArrowUp", shiftKey: true })
    expect(field).toHaveValue("51")
    fireEvent.keyDown(field, { key: "ArrowDown" })
    expect(field).toHaveValue("50")
  })

  it("carries the result on the Apply button itself", async () => {
    render(<Host onApply={vi.fn()} />)
    fireEvent.change(screen.getByLabelText("width value"), { target: { value: "55" } })
    fireEvent.blur(screen.getByLabelText("width value"))

    fireEvent.click(screen.getByRole("button", { name: "Save as default" }))
    await waitFor(() => expect(screen.getByRole("button", { name: "Saved" })).toBeInTheDocument())
  })

  it("renders nothing when no param is adjustable", () => {
    const { container } = render(
      <ParamsPanel params={[params[3]]} values={{}} onChange={vi.fn()} onApply={vi.fn()} />
    )
    expect(container).toBeEmptyDOMElement()
  })
})
