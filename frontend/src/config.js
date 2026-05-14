const base_url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const API_URL = base_url.endsWith('/') ? base_url.slice(0, -1) : base_url;
