// ── Global Configuration ──────────────────────────────────────────
// The central configuration file for the ArthVest frontend.
// The entire application routes all traffic using this single URL.

const DEFAULT_API_BASE_URL = "https://openai-hack-arthvest-backend.onrender.com";
const rawUrl =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_BASE_URL ||
  DEFAULT_API_BASE_URL;

export const config = {
  API_BASE_URL: rawUrl.endsWith("/") ? rawUrl.slice(0, -1) : rawUrl,
};
