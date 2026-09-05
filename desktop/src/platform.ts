// Two things in the shell differ by platform: macOS overlays its titlebar over the
// rail and keeps the Gemini key in the Keychain, while Linux draws normal window
// decorations and keeps the key in a file. The webview knows which one it is.
export const isMac = navigator.userAgent.includes("Mac");

// On Linux a .deb update runs through the system package manager, which asks
// for the user's password; the update copy warns them so the prompt is expected.
export const isLinux = navigator.userAgent.includes("Linux");
