import { render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import { AppShell } from "./app-shell";

test("P1-WEB-003 research shell exposes landmarks and a working skip target", () => {
  render(<AppShell mode="research"><h1>Market Command Center</h1></AppShell>);
  expect(within(screen.getByRole("banner")).getByText("RESEARCH")).toBeDefined();
  expect(within(screen.getByRole("navigation")).getByRole("link", { name: "System health" }).getAttribute("href")).toBe("/system");
  expect(screen.getByRole("link", { name: "Skip to main content" }).getAttribute("href")).toBe("#" + screen.getByRole("main").id);
});
