import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5556',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:5556',
        ws: true,
      }
    }
  }
})
