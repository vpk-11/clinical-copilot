import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  // Backend/frontend ports come from the repo-root .env, not client/.env —
  // this is a single shared config, not a Vite-only one.
  const env = loadEnv(mode, "..", "");
  const clientPort = Number(env.CLIENT_PORT) || 5173;
  const backendTarget = `http://localhost:${Number(env.PORT) || 8000}`;

  return {
    plugins: [react(), tailwindcss()],
    build: {
      outDir: "dist",
    },
    server: {
      port: clientPort,
      proxy: {
        "/upload": backendTarget,
        "/normalize": backendTarget,
        "/analyze": backendTarget,
        "/health": backendTarget,
        "/samples": backendTarget,
      },
    },
  };
});
