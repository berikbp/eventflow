import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  return {
    plugins: [react(), tailwindcss()],
    server: {
      proxy: {
        '/api': {
          target: process.env.API_PROXY_TARGET || env.API_PROXY_TARGET || 'http://127.0.0.1:8000',
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
