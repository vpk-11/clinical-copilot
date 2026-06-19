import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "dist",
  },
  server: {
    port: 5173,
    proxy: {
      "/upload": "http://localhost:8000",
      "/normalize": "http://localhost:8000",
      "/analyze": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
