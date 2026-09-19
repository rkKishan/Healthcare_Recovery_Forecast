import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API_TARGET = process.env.VITE_API_TARGET || 'http://localhost:2800'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 9000,
    // Fail loudly if 9000 is taken rather than drifting to 9001, which would
    // silently fall outside the backend's CORS allowlist.
    strictPort: true,
    // Proxy keeps the browser on one origin in development, so no CORS
    // preflight and no absolute API URLs baked into the client.
    //
    // Every backend route lives under /api precisely so that this rule cannot
    // shadow a client-side route: /dashboard is a page, /api/dashboard is data.
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: true },
    },
  },
})
