import { describe, it, expect, afterEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import SpecCard from "./SpecCard"
import type { Spec } from "./types"

const spec: Spec = {
  part_name: "shelf_bracket",
  summary: "A bracket that hooks the shelf rail and carries 2 kg.",
  params: [
    { name: "wall", kind: "float", default: 2.0, description: "wall thickness" },
    { name: "hook_depth", kind: "float", default: 12.0, description: "how far the hook reaches" },
    { name: "rib_count", kind: "int", default: 3, description: "stiffening ribs" },
  ],
  dimensions: [
    { name: "rail_width", value_mm: 25.16, how: "caliper across the flat", source: "measured", provisional: false },
    { name: "shelf_depth", value_mm: 180, how: "the user said 180", source: "asked", provisional: false },
    { name: "screw_dia", value_mm: 4, how: "M4 nominal", source: "standard", provisional: false },
    { name: "wall", value_mm: 2, how: "print doctrine minimum", source: "doctrine", provisional: true },
  ],
  acceptance: [
    { criterion: "No wall under 1.2 mm", check: "min_wall" },
    { criterion: "The bounding box stays under 200 mm", check: "bbox.x < 200" },
  ],
  conventions: { expose_params: true, parameter_style: "keyword defaults" },
}

describe("SpecCard", () => {
  // vitest runs with globals off, so Testing Library never registers its own cleanup.
  afterEach(cleanup)

  it("renders the part name and summary", () => {
    render(<SpecCard spec={spec} />)
    expect(screen.getByText("The plan")).toBeInTheDocument()
    expect(screen.getByText(spec.summary)).toBeInTheDocument()
  })

  it("renders every dimension with its value in mm", () => {
    render(<SpecCard spec={spec} />)
    expect(screen.getByText("Rail width")).toBeInTheDocument()
    expect(screen.getByText("25.16 mm")).toBeInTheDocument()
    expect(screen.getByText("Shelf depth")).toBeInTheDocument()
    expect(screen.getByText("180 mm")).toBeInTheDocument()
    expect(screen.getByText("Screw dia")).toBeInTheDocument()
    expect(screen.getByText("4 mm")).toBeInTheDocument()
    // Provisional dimensions carry the tilde.
    expect(screen.getByText("~2 mm")).toBeInTheDocument()
  })

  it("labels one dimension per source", () => {
    render(<SpecCard spec={spec} />)
    for (const label of ["You measured", "You told us", "Published", "Rule of thumb"]) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })

  it("lists what done means in plain sentences, without the check names", () => {
    render(<SpecCard spec={spec} />)
    expect(screen.getByText("No wall under 1.2 mm")).toBeInTheDocument()
    expect(screen.getByText("The bounding box stays under 200 mm")).toBeInTheDocument()
    expect(screen.queryByText("min_wall")).toBeNull()
  })

  it("counts the sliders and names each param", () => {
    render(<SpecCard spec={spec} />)
    expect(screen.getByText("3 sliders to adjust")).toBeInTheDocument()
    expect(screen.getByText("Hook depth")).toBeInTheDocument()
  })
})
