import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    strictPort: true, // plante si le port est déjà pris (évite le basculement silencieux)
    host: true,       // expose sur le réseau local (accès depuis téléphone/tablette)
    proxy: {
      '/api':     'http://localhost:8001',
      '/outputs': 'http://localhost:8001',
    },
  },
})
