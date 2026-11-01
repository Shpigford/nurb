import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // The workspace symlink can resolve a second copy of these; two Reacts break hooks.
  resolve: { dedupe: ["react", "react-dom", "three"] },
  // The page ships inside the Python package, so the bundle lands there directly.
  build: { outDir: "../../engine/src/nurb/workbench", emptyOutDir: true },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:7373",
      "/glb": "http://127.0.0.1:7373",
      "/render": "http://127.0.0.1:7373",
      "/ws": { target: "ws://127.0.0.1:7373", ws: true },
    },
  },
})
