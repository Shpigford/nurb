import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("cuelume", () => ({
  play: vi.fn(),
  setEnabled: vi.fn(),
  setVolume: vi.fn(),
}))

import { play, setEnabled, setVolume } from "cuelume"
import { cue, readSoundPrefs, setSoundEnabled, setSoundVolume } from "./sound"

// This jsdom build ships no localStorage, so the preferences need somewhere to live.
const store = new Map<string, string>()
vi.stubGlobal("localStorage", {
  getItem: (k: string) => store.get(k) ?? null,
  setItem: (k: string, v: string) => void store.set(k, v),
  removeItem: (k: string) => void store.delete(k),
  clear: () => store.clear(),
})

describe("sound preferences", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it("is on at 0.6 when nothing has been chosen", () => {
    expect(readSoundPrefs()).toEqual({ enabled: true, volume: 0.6 })
    expect(setEnabled).toHaveBeenCalledWith(true)
    expect(setVolume).toHaveBeenCalledWith(0.6)
  })

  it("carries the old chime switch over and drops the old key", () => {
    localStorage.setItem("nurb-completion-sound", "off")
    expect(readSoundPrefs().enabled).toBe(false)
    expect(localStorage.getItem("nurb-completion-sound")).toBeNull()
    expect(localStorage.getItem("nurb-sound-enabled")).toBe("off")
  })

  it("clamps the volume to 0 through 1", () => {
    setSoundVolume(4)
    expect(readSoundPrefs().volume).toBe(1)
    setSoundVolume(-2)
    expect(readSoundPrefs().volume).toBe(0)
    setSoundVolume(0.35)
    expect(readSoundPrefs().volume).toBe(0.35)
  })

  it("plays nothing once it is muted", () => {
    setSoundEnabled(false)
    cue("ready")
    expect(play).not.toHaveBeenCalled()

    setSoundEnabled(true)
    cue("ready")
    expect(play).toHaveBeenCalledWith("ready", undefined)
  })
})
