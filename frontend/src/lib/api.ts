import axios from "axios";

function computeBaseURL() {
  // Prefer explicit env config
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  // If running in browser, derive backend from current host using port 8000
  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  // Fallback for SSR / build
  return "http://localhost:8000";
}

const baseURL = computeBaseURL();

export const api = axios.create({
  baseURL,
  timeout: 120000,
});

export default api;
