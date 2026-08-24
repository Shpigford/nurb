import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { isWindows } from "./platform";

// CSS keys off this: macOS reserves a strip for the traffic lights under its
// overlay titlebar, Windows has a real titlebar and no strip.
document.body.dataset.platform = isWindows ? "windows" : "macos";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
