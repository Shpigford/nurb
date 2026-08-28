// Two things in the shell differ by platform: macOS overlays its titlebar over the
// rail and keeps the Gemini key in the Keychain, while Linux draws normal window
// decorations and keeps the key in a file. The webview knows which one it is.
export const isMac = navigator.userAgent.includes("Mac");
