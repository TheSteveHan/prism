/* eslint-disable */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server:{
    proxy:{
      '/accounts':{
        target: process.env.AUTH_SERVER || 'http://127.0.0.1:8000/',
        changeOrigin: true
      },
      '/api/user':{
        target: process.env.AUTH_SERVER || 'http://127.0.0.1:8000/',
        changeOrigin: true
      },
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
  }, 
  resolve: {
    alias: [
      {
        find: "components", replacement: path.resolve(`${__dirname  }/src/components/`),
      },
      {
        find: "hooks", replacement: path.resolve(`${__dirname  }/src/hooks/`),
      },
      {
        find: "api", replacement: path.resolve(`${__dirname  }/src/api/`),
      },
      {
        find: "screens", replacement: path.resolve(`${__dirname  }/src/screens/`),
      },
      {
        find: "utils", replacement: path.resolve(`${__dirname  }/src/utils/`),
      },
      {
        find: "assets", replacement: path.resolve(`${__dirname  }/src/assets/`),
      },
    ]
  }
})
