import { defineConfig } from 'vitest/config';
import type { ProxyOptions } from 'vite';
import react from '@vitejs/plugin-react';

const backend = 'http://localhost:8000';
const developmentOrigins = new Set(['http://localhost:5173', 'http://127.0.0.1:5173']);
const proxyOptions: ProxyOptions = {
  target: backend,
  changeOrigin: true,
  configure(proxy: import('http-proxy').Server) {
    proxy.on('proxyReq', (proxyRequest, request) => {
      const origin = request.headers.origin;
      if (!origin) return;
      if (developmentOrigins.has(origin)) proxyRequest.setHeader('origin', backend);
    });
  },
};

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api': proxyOptions,
      '/media-protected': proxyOptions,
    },
  },
  test: {
    include: ['src/**/*.test.{ts,tsx}'],
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    globals: true,
  },
});
