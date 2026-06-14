/**
 * Centralised API configuration.
 * Uses an environment variable so the correct backend URL is used in
 * production (Render) while keeping "/api" for local development.
 */
import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

/**
 * Attach the JWT (if present in localStorage) to every request.
 */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("mlss_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Normalise API error responses for the UI.
 */
export const getErrorMessage = (error, fallback = "Something went wrong") => {
  if (error?.response?.data?.message) return error.response.data.message;
  if (error?.message) return error.message;
  return fallback;
};

export default api;
