import { test, expect } from "@playwright/test";

test.describe("smoke", () => {
  test("login page renders", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /Kanban Retail/i })).toBeVisible();
    await expect(page.getByLabel(/Correo/i)).toBeVisible();
  });
});
