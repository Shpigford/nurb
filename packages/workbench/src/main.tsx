import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { startTheme } from "@nurb/ui"
import App from "./App"
import "./app.css"

startTheme()

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>
)
