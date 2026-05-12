import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/health': 'http://127.0.0.1:8081',
      '/sources': 'http://127.0.0.1:8081',
      '/documents': 'http://127.0.0.1:8081',
      '/ingest': 'http://127.0.0.1:8081',
      '/ask': 'http://127.0.0.1:8081',
    },
  },
})
