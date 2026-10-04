import { test, expect } from "@playwright/test";

test("scroll spy, Arabic reading size and optimized hero", async ({ page }) => {
  // A short desktop viewport lets each compact final section reach the top
  // independently, instead of scrollIntoView clamping at the page bottom.
  const viewport = page.viewportSize();
  if (viewport && viewport.width > 1100) {
    await page.setViewportSize({ width: viewport.width, height: 400 });
  }
  await page.goto("/");
  const active = page.locator(".nav-links [aria-current='location']");
  await expect(active).toHaveAttribute("href", "#home");
  for (const [section, href] of [
    ["concepts", "#concepts"],
    ["learning-path", "#learning-path"],
    ["examples", "#examples"],
    ["sources", "#sources"],
  ]) {
    await page
      .locator(`#${section}`)
      .evaluate((element) =>
        element.scrollIntoView({ behavior: "instant", block: "start" }),
      );
    await expect(active).toHaveAttribute("href", href);
  }
  await page.evaluate(() =>
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: "instant",
    }),
  );
  await expect(active).toHaveAttribute("href", "#about");
  const arabicSize = await page
    .locator(".concept-card p")
    .first()
    .evaluate((element) => parseFloat(getComputedStyle(element).fontSize));
  expect(arabicSize).toBe(16);
  const imageUrl = await page
    .locator(".hero-background")
    .evaluate((element: HTMLImageElement) => element.currentSrc);
  expect(imageUrl).toContain("/_next/image?");
  const response = await page.request.get(imageUrl);
  expect(response.ok()).toBe(true);
  expect(response.headers()["content-type"]).toMatch(/^image\//);
  await page.getByRole("button", { name: "Switch to English" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  const englishSize = await page
    .locator(".concept-card p")
    .first()
    .evaluate((element) => parseFloat(getComputedStyle(element).fontSize));
  expect(englishSize).toBe(11);
});
