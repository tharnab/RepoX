const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getCurrentUser() {
  const res = await fetch(`${API_URL}/auth/me`, {
    credentials: "include",
  });
  return res.json();
}