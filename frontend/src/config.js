const base_url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// Strip all trailing slashes to ensure we don't get double slashes
export const API_URL = base_url.replace(/\/+$/, "");

console.log("🌐 SBTXT API URL:", API_URL);
