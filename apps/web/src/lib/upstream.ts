// Fixed upstream paths; credentials and arbitrary request headers never cross the proxy.
export async function upstream(path: "/readyz" | "/api/v1/system/info") {
  try {
    const url = new URL(path, process.env.API_ORIGIN ?? "http://127.0.0.1:8000");
    const res = await fetch(url, { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(5000) });
    if (res.ok || (path === "/readyz" && res.status === 503)) {
      return Response.json(await res.json(), { status: res.status, headers: { "Cache-Control": "no-store" } });
    }
  } catch {
    // Both network and malformed upstream responses use the same public envelope.
  }
  return Response.json({ error: "API unavailable" }, { status: 502 });
}
