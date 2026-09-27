import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// dev: vite 起 :5173，把 /api/* 代理到 backend :8082
// prod: nginx 反代（前端 :80，所有 /api/* 走 backend :8082）
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8082',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})