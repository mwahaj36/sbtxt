const base_url = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();
// Strip ALL trailing slashes. If the result is just "/", make it empty string.
export const API_URL = base_url.replace(/\/+$/, "") === "/" ? "" : base_url.replace(/\/+$/, "");
// Deployment Trigger: 2026-05-15 22:05
