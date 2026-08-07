import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;
          // Heavy, route-only libs: keep OUT of the eagerly-loaded entry chunk.
          if (id.includes('recharts') || id.includes('victory')) return 'charts';
          if (id.includes('leaflet')) return 'leaflet';
          // Core framework (eager — needed by the entry/login page).
          if (id.includes('react-router') || id.includes('/react/') || id.includes('react-dom') || id.includes('scheduler')) {
            return 'react-vendor';
          }
          if (id.includes('@tanstack') || id.includes('zustand')) return 'query-state';
          if (id.includes('lucide-react')) return 'icons';
          return 'misc-vendor';
        }
      }
    }
  }
})
