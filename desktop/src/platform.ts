// Which OS the shell is dressed for. The user agent is enough: the webview is
// Tauri's own (WKWebView or WebView2), never a spoofed browser, and asking the
// Rust side would make every caller async for a fact that never changes.
export const isWindows = navigator.userAgent.includes("Windows");

/// The OS name for debug info and bug reports, beside the version number the
/// backend measured.
export const osLabel = isWindows ? "Windows" : "macOS";
