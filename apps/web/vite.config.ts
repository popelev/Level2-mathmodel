import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = process.env.VITE_PROXY_TARGET ?? "http://127.0.0.1:8090";

const proxy = {
  "/api": apiTarget,
  "/healthz": apiTarget,
  "/readyz": apiTarget,
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy,
  },
  preview: {
    port: 4173,
    proxy,
  },
});
