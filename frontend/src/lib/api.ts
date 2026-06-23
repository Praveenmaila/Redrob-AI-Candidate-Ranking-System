import axios from "axios";

function computeBaseURL() {
  // Always go through the Next.js rewrite proxy at /api/*. The proxy
  // (defined in next.config.js) forwards to the backend, which means
  // (1) the browser never talks to a different host:port, avoiding CORS
  // and firewall issues; (2) it works regardless of whether the user
  // accesses the frontend via localhost or a remote host like
  // http://10.74.166.38:3000; (3) the proxy target can be overridden
  // per environment with NEXT_PUBLIC_BACKEND_TARGET.
  return "/api";
}

const baseURL = computeBaseURL();

export const BASE_URL = baseURL;

export const api = axios.create({
  baseURL,
  timeout: 15 * 60 * 1000,
  maxContentLength: Infinity,
  maxBodyLength: Infinity,
});

export default api;
