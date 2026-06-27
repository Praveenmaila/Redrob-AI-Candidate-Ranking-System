import axios from "axios";

const baseURL =
  process.env.NEXT_PUBLIC_BACKEND_TARGET ||
  "http://localhost:8000";

export const BASE_URL = baseURL;

export const api = axios.create({
  baseURL,
  timeout: 15 * 60 * 1000, // 15 minutes
  maxContentLength: Infinity,
  maxBodyLength: Infinity,
});

export default api;
