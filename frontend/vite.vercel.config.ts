import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// Vercel captures the `static/` directory as the deployment output.
// Keep the existing /static/ base so the same bundle remains compatible with
// the FastAPI server; vercel.mjs rewrites /static/* back to the deployment root.
export default defineConfig({
  plugins: [vue()],
  base: '/static/',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    outDir: '../static',
    emptyOutDir: false,
    assetsDir: 'assets',
    sourcemap: false,
  },
})
