import { expect, test } from "@playwright/test";

test("P1-E2E-002 unreachable API displays a recoverable error", async ({ page }) => {
  await page.route("**/api/**", route => route.abort("connectionrefused"));
  await page.goto("/");
  await expect(page.getByRole("alert").filter({hasText:"API unavailable"})).toBeVisible();
  await page.unroute("**/api/**");
  await page.getByRole("button", {name:"Refresh health"}).click();
  await expect(page.getByRole("status")).toHaveText("Operational");
});
