"use client";
import type { ReadinessReport } from "@klowb/types";
import { useReadiness } from "../lib/api";

export function StatusReport({ report, failed }: { report?: ReadinessReport; failed: boolean }) {
  if (failed) return <p role="alert">API unavailable. Could not load system health.</p>;
  if (!report) return <p role="status">Checking system health…</p>;
  const labels = { ok: "Operational", degraded: "Degraded", unavailable: "Unavailable" };
  return <>
    <p className="summary" role="status">{labels[report.status]}</p>
    <table><caption className="sr-only">Service health</caption>
      <thead><tr><th scope="col">Service</th><th scope="col">Status</th><th scope="col">Latency</th></tr></thead>
      <tbody><tr><th scope="row">API</th><td>Up</td><td>—</td></tr>
        {report.dependencies.map(d => <tr key={d.name}><th scope="row">{({ postgres: "PostgreSQL", redis: "Redis" })[d.name] ?? d.name}</th>
          <td>{d.status === "up" ? "Up" : "Down"}</td><td>{d.latency_ms == null ? "—" : d.latency_ms.toFixed(1) + " ms"}</td></tr>)}
      </tbody></table>
    {!report.dependencies.length && <p>No dependencies reported.</p>}
    <p className="checked">Checked <time dateTime={report.checked_at}>{new Date(report.checked_at).toISOString().slice(11,19)} UTC</time></p>
  </>;
}
export function SystemStatus() {
  const health = useReadiness();
  return <section aria-labelledby="health-title"><h2 id="health-title">System health</h2>
    <StatusReport report={health.data} failed={health.isError}/>
    <button onClick={() => void health.refetch()} disabled={health.isFetching}>Refresh health</button>
  </section>;
}
