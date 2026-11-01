import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({
  root: "gallery",
  plugins: [react(), tailwindcss()],
  build: { outDir: "../gallery-dist", emptyOutDir: true },
})
