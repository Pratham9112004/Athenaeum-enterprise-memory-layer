import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The API base URL is provided via VITE_API_URL (see .env.example). In containerized
// dev it points at the backend service; the app reads it from import.meta.env.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
  },
  preview: {
    port: 5173,
  },
});
