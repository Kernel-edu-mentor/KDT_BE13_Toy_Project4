import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 4000,
    strictPort: true,
    proxy: {
      "/api": {
        //target: "http://localhost:8080",
        target: "http://spring-backend:8080", // Docker 환경용
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: "::",
    port: 4000,
    strictPort: true,
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
