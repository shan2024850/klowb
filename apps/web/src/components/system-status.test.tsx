import { render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import type { ReadinessReport } from "@klowb/types";
import { StatusReport } from "./system-status";

test("P1-WEB-005 panel renders loading, healthy, degraded, unavailable, empty and transport failure states", () => {
  const view = render(<StatusReport failed={false}/>);
  expect(screen.getByRole("status").textContent).toContain("Checking");
  const report: ReadinessReport = { checked_at: "2026-11-17T12:34:56Z", status:"ok",
    dependencies:[{ name:"redis", status:"up", required:false }] };
  view.rerender(<StatusReport report={report} failed={false}/>);
  expect(screen.getByRole("status").textContent).toBe("Operational");
  expect(within(screen.getByRole("row", {name:/Redis/})).getByText("Up")).toBeDefined();
  view.rerender(<StatusReport report={{...report,status:"degraded",dependencies:[{...report.dependencies[0],status:"down"}]}} failed={false}/>);
  expect(screen.getByRole("status").textContent).toBe("Degraded");
  expect(within(screen.getByRole("row", {name:/Redis/})).getByText("Down")).toBeDefined();
  view.rerender(<StatusReport report={{...report,status:"unavailable",dependencies:[]}} failed={false}/>);
  expect(screen.getByRole("status").textContent).toBe("Unavailable");
  expect(screen.getByText("No dependencies reported.")).toBeDefined();
  view.rerender(<StatusReport report={report} failed/>);
  expect(screen.getByRole("alert").textContent).toContain("API unavailable");
});
