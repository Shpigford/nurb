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

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
