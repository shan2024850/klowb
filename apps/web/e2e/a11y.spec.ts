import { AxeBuilder } from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("P1-E2E-003 shell has no serious or critical axe violations", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("Operational");
  await expect(page.getByText("Unofficial", {exact:true})).toBeVisible();
  const result = await new AxeBuilder({page}).analyze();
  expect(result.violations.filter(v => v.impact === "serious" || v.impact === "critical")).toEqual([]);
});
