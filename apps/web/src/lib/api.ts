import { zReadinessReport, zSystemInfo } from "@klowb/types/validators";
import { useQuery } from "@tanstack/react-query";

async function payload(path: string, signal: AbortSignal, allowUnavailable = false): Promise<unknown> {
  const response = await fetch(path, { signal, cache: "no-store" });
  if (!response.ok && !(allowUnavailable && response.status === 503)) {
    throw new Error("API unavailable");
  }
  return response.json();
}

export function useSystemInfo() {
  return useQuery({ queryKey: ["system-info"], queryFn: async ({ signal }) =>
    zSystemInfo.parse(await payload("/api/v1/system/info", signal)) });
}

export function useReadiness() {
  return useQuery({ queryKey: ["readiness"], queryFn: async ({ signal }) =>
    zReadinessReport.parse(await payload("/api/readyz", signal, true)) });
}
