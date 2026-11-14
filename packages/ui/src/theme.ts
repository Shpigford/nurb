import { useSyncExternalStore } from "react"

// Light or dark. The choice is stored per webview; "system" follows the OS and keeps
// following it while the app is open. The resolved theme lands on <html data-theme>,
// which is what tokens.css and the viewer both read, so there is one switch.
export type ThemeChoice = "system" | "light" | "dark"

const KEY = "nurb-theme"
const media = typeof matchMedia === "function" ? matchMedia("(prefers-color-scheme: dark)") : null

export function readThemeChoice(): ThemeChoice {
  let stored: string | null = null
  try {
    stored = localStorage.getItem(KEY)
  } catch {
    // A locked-down webview throws on access; fall through to the system.
  }
  return stored === "light" || stored === "dark" ? stored : "system"
}

function apply() {
  const choice = readThemeChoice()
  const dark = choice === "dark" || (choice === "system" && !!media?.matches)
  document.documentElement.dataset.theme = dark ? "dark" : "light"
}

export function setThemeChoice(choice: ThemeChoice) {
  try {
    if (choice === "system") localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, choice)
  } catch {
    // Still applies for this session.
  }
  apply()
}

/** Call once at startup, before the first render, so the page never paints in the wrong theme. */
export function startTheme() {
  apply()
  media?.addEventListener("change", apply)
}

export const isDark = () => document.documentElement.dataset.theme === "dark"

const watch = (onChange: () => void) => {
  const observer = new MutationObserver(onChange)
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] })
  return () => observer.disconnect()
}

/** For what CSS cannot reach, like a picture the engine renders for one ground or the other. */
export const useIsDark = () => useSyncExternalStore(watch, isDark, () => false)
