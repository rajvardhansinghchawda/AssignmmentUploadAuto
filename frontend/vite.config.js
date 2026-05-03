import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    define: {
      // Makes VITE_API_URL available as import.meta.env.VITE_API_URL
      // Falls back to empty string (same-origin) when deployed on HuggingFace
      __API_URL__: JSON.stringify(env.VITE_API_URL || ''),
    },
  }
})
