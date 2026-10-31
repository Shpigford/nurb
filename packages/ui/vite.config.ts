import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import dts from "vite-plugin-dts"

export default defineConfig({
  // Relative, so an asset URL resolves against dist/index.js instead of the
  // consuming site's root. Vite emits `new URL(..., import.meta.url)` for it,
  // which a downstream bundler re-emits as its own asset.
  base: "./",
  plugins: [react(), dts({ include: ["src"], exclude: ["src/**/*.test.*", "src/test-setup.ts"] })],
  build: {
    // Zero so every SVG lands in dist as a real file a consumer can serve,
    // instead of being inlined as a data URI in the bundle.
    assetsInlineLimit: 0,
    lib: {
      entry: "src/index.ts",
      formats: ["es"],
      fileName: () => "index.js",
    },
    rollupOptions: {
      // three/addons/* must stay external too, or rollup inlines OrbitControls into the bundle.
      external: (id) => /^(react|react-dom|react\/jsx-runtime|three|clsx|react-markdown)($|\/)/.test(id),
    },
  },
})
