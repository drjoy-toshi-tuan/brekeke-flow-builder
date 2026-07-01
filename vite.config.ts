import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// Dev chạy ở root ('/') cho tiện; khi build cho GitHub Pages thì base phải khớp
// tên repo để phục vụ đúng đường dẫn: https://<user>.github.io/brekeke-flow-builder/
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/brekeke-flow-builder/' : '/',
  plugins: [react(), tailwindcss()],
}));
