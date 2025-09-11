import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react' // or react, etc.
import path from 'path'

export default defineConfig({
  plugins: [react()], // or your framework plugin
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/most_streamed': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})