import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  },
  build: {
    // Do NOT preload route-only heavy chunks (leaflet/charts) on the entry page;
    // they should only download when their lazy route is visited.
    modulePreload: {
      polyfill: false,
      resolveDependencies: (_filename, deps) =>
        deps.filter((d) => !/charts-|leaflet-/.test(d)),
    },
    // Rolldown emits every chunk's CSS as a separate render-blocking <link>.
    // Bundle into one stylesheet so the login page has a single CSS request.
    cssCodeSplit: false,
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
