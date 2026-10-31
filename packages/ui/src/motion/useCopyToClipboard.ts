import { useCallback, useEffect, useRef, useState } from "react"
import { cue } from "../sound"

export type CopyStatus = "idle" | "copied" | "error"

export interface UseCopyToClipboardOptions {
  /** How long "copied" or "error" shows before the label goes back. */
  timeout?: number
  onCopy?: (value: string) => void
  onError?: (error: unknown) => void
}

// One copy behaviour for the whole kit: the same revert delay, the same two
// cues, so a link copied in the rail sounds like a link copied anywhere else.
export function useCopyToClipboard({ timeout = 1500, onCopy, onError }: UseCopyToClipboardOptions = {}) {
  const [status, setStatus] = useState<CopyStatus>("idle")
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current)
  }, [])

  const revert = useCallback(
    (next: CopyStatus) => {
      setStatus(next)
      if (timer.current) clearTimeout(timer.current)
      timer.current = setTimeout(() => setStatus("idle"), timeout)
    },
    [timeout],
  )

  const copy = useCallback(
    async (value: string) => {
      try {
        if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(value)
        else if (!legacyCopy(value)) throw new Error("clipboard unavailable")
        cue("success")
        onCopy?.(value)
        revert("copied")
      } catch (error) {
        cue("error")
        onError?.(error)
        revert("error")
      }
    },
    [onCopy, onError, revert],
  )

  return { status, copy }
}

// Safari before the permission prompt, and any page served over plain http, have
// no navigator.clipboard at all. execCommand still works there.
function legacyCopy(value: string): boolean {
  const field = document.createElement("textarea")
  field.value = value
  field.setAttribute("readonly", "")
  field.style.position = "fixed"
  field.style.opacity = "0"
  document.body.appendChild(field)
  try {
    field.select()
    return document.execCommand("copy")
  } finally {
    field.remove()
  }
}

export default useCopyToClipboard
