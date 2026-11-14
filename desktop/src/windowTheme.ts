import { getCurrentWindow } from "@tauri-apps/api/window";
import { readThemeChoice } from "@nurb/ui";

// The native window keeps its own appearance: the traffic lights, and what the
// webview reports as prefers-color-scheme. Pin it to an explicit choice, or hand
// it back to macOS for "system", so the chrome and the page never disagree.
export function syncWindowTheme() {
  const choice = readThemeChoice();
  getCurrentWindow()
    .setTheme(choice === "system" ? null : choice)
    .catch(() => {});
}
