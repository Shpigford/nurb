import { play, setEnabled, setVolume } from "cuelume"

// The whole vocabulary. Nine cues, each tied to something that actually happened:
// a build landed, a link is on the clipboard, a toggle moved. There is no hover
// cue and there never will be: a person modelling a part sweeps the pointer over
// the rail dozens of times a minute, and a sound for that is a sound they mute.
export type Cue =
  | "ready"
  | "arrival"
  | "success"
  | "error"
  | "press"
  | "tick"
  | "toggle"
  | "scan"
  | "loading"

const ENABLED_KEY = "nurb-sound-enabled"
const VOLUME_KEY = "nurb-sound-volume"
// The desktop app's old chime switch, which only stored "off".
const LEGACY_KEY = "nurb-completion-sound"

const DEFAULT_VOLUME = 0.6

export interface SoundPrefs {
  enabled: boolean
  volume: number
}

// Private browsing and a locked-down webview both throw on plain access, so every
// read and write is wrapped rather than guarded by a feature check.
function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    // A preference that cannot be stored still applies for this session.
  }
}

function clamp(v: number): number {
  if (!Number.isFinite(v)) return DEFAULT_VOLUME
  return Math.min(1, Math.max(0, v))
}

/** Reads the stored preferences and pushes them into cuelume. */
export function readSoundPrefs(): SoundPrefs {
  const legacy = read(LEGACY_KEY)
  if (legacy !== null) {
    // One-time migration: the old key only ever meant "muted".
    if (legacy === "off" && read(ENABLED_KEY) === null) write(ENABLED_KEY, "off")
    write(LEGACY_KEY, null)
  }

  const enabled = read(ENABLED_KEY) !== "off"
  const stored = read(VOLUME_KEY)
  const volume = stored === null ? DEFAULT_VOLUME : clamp(Number(stored))

  apply(enabled, volume)
  return { enabled, volume }
}

export function setSoundEnabled(on: boolean) {
  write(ENABLED_KEY, on ? null : "off")
  apply(on, readVolume())
}

export function setSoundVolume(v: number) {
  const volume = clamp(v)
  write(VOLUME_KEY, String(volume))
  apply(read(ENABLED_KEY) !== "off", volume)
}

function readVolume(): number {
  const stored = read(VOLUME_KEY)
  return stored === null ? DEFAULT_VOLUME : clamp(Number(stored))
}

function apply(enabled: boolean, volume: number) {
  try {
    setEnabled(enabled)
    setVolume(volume)
  } catch {
    // No Web Audio is never worth an error on screen.
  }
}

/** Plays a cue. A no-op on the server, when muted, or when audio is unavailable. */
export function cue(name: Cue, opts?: { volume?: number }) {
  if (typeof window === "undefined") return
  if (read(ENABLED_KEY) === "off") return
  try {
    play(name, opts)
  } catch {
    // Same reason: a silent app beats a crashed one.
  }
}
