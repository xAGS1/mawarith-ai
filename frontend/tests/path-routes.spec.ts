import { test, expect } from "@playwright/test";

test("path shells resolve, stay bilingual and link back to homepage sections", async ({
  page,
}) => {
  for (const slug of [
    "inheritance-foundations",
    "shares-rules",
    "cases-applications",
    "special-advanced",
  ]) {
    const response = await page.goto(`/learn/paths/${slug}`);
    expect(response?.status()).toBe(200);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main")).toContainText("لم تُضف الدروس بعد");
    await expect(
      page.locator('.nav-links a[href="/#learning-path"]'),
    ).toHaveCount(1);
    await expect(
      page.locator('.footer-links a[href="/#concepts"]'),
    ).toHaveCount(1);
  }
  await page.getByRole("button", { name: "Switch to English" }).click();
  await expect(page.locator("main h1")).toHaveText("Special & Advanced Cases");
  await expect(page.locator("main")).toContainText(
    "Lessons have not been added yet.",
  );
  await page.getByRole("link", { name: "Back to Learning Paths" }).click();
  await expect(page.locator(".source-card").nth(1)).toContainText(
    "Documented Rules",
  );
  await expect(page.locator(".nav-links a")).toHaveText([
    "Home",
    "Concepts",
    "Learning Paths",
    "Examples",
    "Sources",
    "About",
  ]);
});
