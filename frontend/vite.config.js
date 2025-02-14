import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server:{
    proxy:{
      '/api':{
        target: process.env.API_SERVER || 'http://127.0.0.1:8008/',
        changeOrigin: true
      },
      '/http':{
        target: 'http://127.0.0.1:30080/',
        changeOrigin: true,
        headers: {
          origin: "www.google.com" // an origin header is requried by cros anywhere, can be anything
        }
      },
    }
  }
})
