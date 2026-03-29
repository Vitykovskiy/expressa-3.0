import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react-swc';

export default defineConfig({
  base: '/backoffice/',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 4174,
  },
  preview: {
    host: '0.0.0.0',
    port: 4174,
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
