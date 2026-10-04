import { test, expect } from "@playwright/test";

test("footer navigation shares the viewport center axis", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Desktop three-zone layout");
  await page.goto("/");
  for (const width of [1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    for (const selector of [".footer-links", ".nav-links", ".hero h1"]) {
      const box = await page.locator(selector).boundingBox();
      expect(box).not.toBeNull();
      expect(Math.abs(box!.x + box!.width / 2 - width / 2)).toBeLessThan(.1);
    }
    const links = await page.locator(".footer-links").boundingBox();
    const brand = await page.locator(".footer-main > div").first().boundingBox();
    const motto = await page.locator(".footer-quote").boundingBox();
    expect(motto!.x + motto!.width).toBeLessThan(links!.x);
    expect(links!.x + links!.width).toBeLessThan(brand!.x);
    await page.locator(".footer").screenshot({ path: `test-results/footer-centered-${width}.png` });
  }
});
