import { expect, test } from "@playwright/test";

test("P1-E2E-001 running stack reports service health and supports keyboard navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("banner")).toContainText("RESEARCH");
  for (const name of ["API","PostgreSQL","Redis"]) {
    await expect(page.getByRole("row").filter({has:page.getByRole("rowheader", { name, exact:true })})).toContainText("Up");
  }
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", {name:"Skip to main content"})).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
});
