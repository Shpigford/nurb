import { describe, expect, it } from "vitest"
import { activity, type Activity } from "./activity"

describe("activity", () => {
  it("says the work on the window, start and answer under one id", () => {
    const heard: Activity[] = []
    const listen = (event: Event) => heard.push((event as CustomEvent<Activity>).detail)
    window.addEventListener("nurb:activity", listen)

    activity({ id: "export-1", title: "Exporting lid.3mf", tone: "working" })
    activity({ id: "export-1", title: "Exporting lid.3mf", detail: "Saved", tone: "done" })
    window.removeEventListener("nurb:activity", listen)

    expect(heard).toEqual([
      { id: "export-1", title: "Exporting lid.3mf", tone: "working" },
      { id: "export-1", title: "Exporting lid.3mf", detail: "Saved", tone: "done" },
    ])
  })
})
