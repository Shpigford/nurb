// Mono-label formatters. Every figure carries a unit.

export function rev(n: number | null | undefined): string {
  return `REV ${String(Math.max(0, n ?? 0)).padStart(2, "0")}`
}

// A stack label for a card strip: "fable-5 low", "grok-4.6 low". The
// vendor prefix says nothing the model name does not.
export function stackLabel(model: string | null | undefined, effort?: string | null): string | null {
  if (!model) return null
  const name = model.replace(/^claude-/, "")
  return effort ? `${name} ${effort}` : name
}

// A build's wall-clock, as m:ss.
export function clock(seconds: number | null | undefined): string | null {
  if (seconds == null) return null
  const s = Math.max(0, Math.round(seconds))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`
}

// A live counter's reading: one decimal under a minute, m:ss at or above one.
// The cut is 59.95 rather than 60 so the tenths never show "60.0s" on their way
// over. Never blank: a run that just started reads "0.0s".
export function elapsedLabel(seconds: number): string {
  const s = Math.max(0, seconds)
  if (s < 59.95) return `${s.toFixed(1)}s`
  return clock(s) as string
}

export function relativeTime(iso: string | null | undefined, now = Date.now()): string | null {
  if (!iso) return null
  const seconds = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000))
  if (seconds < 60) return "just now"
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  if (days < 7) return `${days}d ago`
  const weeks = Math.round(days / 7)
  if (weeks < 8) return `${weeks}w ago`
  const months = Math.round(days / 30)
  return `${months}mo ago`
}

export function formatBbox(bbox?: number[] | null): string | null {
  if (!bbox || bbox.length !== 3) return null
  return bbox.map((n) => Math.round(n * 10) / 10).join(" × ")
}

// Two letters for the avatar: first letters of a name's first two words, or
// the start of the email's local part when there is no name.
export function initials(nameOrEmail: string | null | undefined): string {
  if (!nameOrEmail) return "·"
  if (nameOrEmail.includes("@")) return nameOrEmail.split("@")[0].slice(0, 2).toUpperCase()
  const words = nameOrEmail.trim().split(/\s+/)
  const letters = words.length > 1 ? words[0][0] + words[1][0] : words[0].slice(0, 2)
  return letters.toUpperCase()
}

/** A code name as a person reads it: `case_width` is "Case width". */
export function words(name: string): string {
  const spaced = name.replace(/_+/g, " ").trim()
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}
