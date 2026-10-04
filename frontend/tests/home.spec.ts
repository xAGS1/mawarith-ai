import { test, expect } from "@playwright/test";

test("RTL homepage, question selection and previews", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  if (testInfo.project.name === "desktop") {
    for (const width of [1440, 1920]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(() => document.fonts.ready);
      for (const selector of [
        ".hero h1",
        ".hero h2",
        ".hero-description",
        ".ask-panel",
        ".mode-selector",
      ]) {
        const box = await page.locator(selector).boundingBox();
        expect(box).not.toBeNull();
        expect(box!.x + box!.width / 2, selector).toBe(width / 2);
      }
      const panel = await page.locator(".ask-panel").boundingBox();
      const modes = await page.locator(".mode-selector").boundingBox();
      expect(panel!.width).toBe(modes!.width);
      await page.locator(".hero").screenshot({
        path: `test-results/hero-centered-${width}.png`,
      });
    }
    for (const width of [320, 768, 1024]) {
      await page.setViewportSize({ width, height: 900 });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBeTruthy();
      const panel = await page.locator(".ask-panel").boundingBox();
      const hero = await page.locator(".hero").boundingBox();
      expect(panel).not.toBeNull();
      expect(hero).not.toBeNull();
      expect(panel!.x).toBeGreaterThanOrEqual(0);
      expect(panel!.x + panel!.width).toBeLessThanOrEqual(width);
      expect(panel!.y + panel!.height).toBeLessThanOrEqual(
        hero!.y + hero!.height,
      );
      const modes = await page.locator(".mode-selector").boundingBox();
      expect(modes).not.toBeNull();
      expect(modes!.x).toBeGreaterThanOrEqual(0);
      expect(modes!.x + modes!.width).toBeLessThanOrEqual(width);
      expect(modes!.y).toBeGreaterThanOrEqual(panel!.y + panel!.height);
      expect(modes!.y + modes!.height).toBeLessThanOrEqual(
        hero!.y + hero!.height,
      );
    }
    await page.setViewportSize({ width: 1440, height: 1000 });
  }
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator(".concept-card")).toHaveCount(7);
  await expect(page.locator(".example-card")).toHaveCount(3);
  await expect(page.locator(".source-card")).toHaveCount(4);
  await expect(
    page.getByRole("heading", { name: "فهم نظام المواريث في الإسلام" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: `test-results/home-initial-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "ما معنى العصبة؟", exact: true })
    .click();
  await expect(page.getByRole("textbox")).toHaveValue("ما معنى العصبة؟");
  await page.getByRole("button", { name: "استكشف السؤال" }).click();
  await expect(page.locator(".question-preview")).toContainText(
    "ما معنى العصبة؟",
  );
  await page.getByRole("button", { name: "وضع المسائل", exact: false }).click();
  await expect(
    page.getByRole("button", { name: "وضع المسائل", exact: false }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.locator(".concept-card").first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.locator(".example-card").first().click();
  await expect(page.getByRole("dialog")).toContainText("مات وترك زوجة");
  await page.getByRole("button", { name: "إغلاق المعاينة" }).click();
  await page.locator(".path-details summary").click();
  await expect(page.locator(".path-details li")).toHaveCount(5);
  if (testInfo.project.name === "mobile") {
    await page.getByRole("button", { name: "فتح القائمة" }).click();
    await expect(page.getByRole("navigation")).toBeVisible();
    await page
      .getByRole("navigation")
      .getByRole("link", { name: "المصادر" })
      .click();
    await expect(page.getByRole("navigation")).not.toBeVisible();
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `test-results/home-${testInfo.project.name}.png`,
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
