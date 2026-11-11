import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // URL del backend FastAPI en dev; se puede pisar con API_PROXY_TARGET en frontend/.env.local
  const apiTarget = env.API_PROXY_TARGET || 'http://localhost:8000'

  return {
    plugins: [react()],
    server: {
      proxy: {
        // El front llama a /api/... y Vite lo reenvía al backend sin el prefijo
        // (/api/eventos -> http://localhost:8000/eventos), así no choca con las rutas del front.
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          // El backend setea la cookie del refresh token con path /auth, pero el navegador
          // ve esas rutas como /api/auth: sin esto la cookie nunca vuelve al backend.
          cookiePathRewrite: { '/auth': '/api/auth' },
        },
      },
    },
  }
})
