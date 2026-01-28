export function validateGitHubUrl(
  url: string
): { valid: true } | { valid: false; error: string } {
  const s = (url ?? "").trim();
  if (!s) return { valid: false, error: "URL is required" };
  try {
    const u = new URL(s);
    if (u.protocol !== "http:" && u.protocol !== "https:")
      return { valid: false, error: "URL must use http or https" };
    if (u.hostname.toLowerCase() !== "github.com")
      return { valid: false, error: "URL must point to github.com" };
    const path = u.pathname.replace(/\/$/, "").replace(/\.git$/i, "");
    const segments = path.split("/").filter(Boolean);
    if (segments.length < 2)
      return {
        valid: false,
        error: "URL must contain owner and repo (e.g. github.com/owner/name)",
      };
    if (!segments[0] || !segments[1])
      return { valid: false, error: "Invalid owner or repo name" };
    return { valid: true };
  } catch {
    return { valid: false, error: "Invalid URL" };
  }
}
