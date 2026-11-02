import React from "react";
import ReactDOM from "react-dom/client";
import { readSoundPrefs } from "@nurb/ui";
import App from "./App";
import "./tailwind.css";

// Reading the prefs is what pushes them into the sound layer, and Settings may
// never open, so the first cue of the session has to find the saved volume here.
readSoundPrefs();

// For whoever opens the inspector. The mark keeps its dash; it is the wordmark.
console.log("%cnurb — parts that fit.", "color:#ff5230;font-weight:700");
console.log("Don't print this in PLA if it's going in a car.");

// The webview's own menu offers only Reload, which throws away the session. Keep
// it where it does something: text you can edit, and text you have selected.
document.addEventListener("contextmenu", (e) => {
  const target = e.target as HTMLElement;
  if (target.closest("input, textarea, [contenteditable='true']")) return;
  if (window.getSelection()?.toString()) return;
  e.preventDefault();
});

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
