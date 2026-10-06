import { test, expect } from "@playwright/test";

test("RTL homepage, question selection and previews", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        mode: "learn",
        decision_state: "ready",
        language: "ar",
        answer: "Mock answer",
        source_excerpts: [],
      },
    }),
  );
  await page.goto("/");
  await expect(page.locator(".hero-background")).toHaveCount(1);
  await expect(page.locator(".hero-background")).toHaveJSProperty(
    "complete",
    true,
  );
  expect(
    await page
      .locator(".hero-background")
      .evaluate((image: HTMLImageElement) => image.naturalWidth),
  ).toBeGreaterThan(0);
  if (testInfo.project.name === "desktop") {
    for (const width of [1440, 1920]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.evaluate(() => document.fonts.ready);
      for (const selector of [
        ".navbar .nav-links",
        ".hero h1",
        ".hero h2",
        ".hero-description",
        ".ask-panel",
      ]) {
        const box = await page.locator(selector).boundingBox();
        expect(box).not.toBeNull();
        expect(box!.x + box!.width / 2, selector).toBe(width / 2);
      }
      const navigation = await page.locator(".navbar .nav-links").boundingBox();
      const brand = await page.locator(".navbar .brand").boundingBox();
      const utility = await page.locator(".navbar .nav-actions").boundingBox();
      expect(utility!.x + utility!.width).toBeLessThan(navigation!.x);
      expect(navigation!.x + navigation!.width).toBeLessThan(brand!.x);
    }
    for (const width of [320, 768, 1024]) {
      await page.setViewportSize({ width, height: 900 });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBeTruthy();
      const panel = await page.locator(".ask-panel").boundingBox();
      const hero = await page.locator(".hero-experience").boundingBox();
      expect(panel).not.toBeNull();
      expect(hero).not.toBeNull();
      expect(panel!.x).toBeGreaterThanOrEqual(0);
      expect(panel!.x + panel!.width).toBeLessThanOrEqual(width);
      expect(panel!.y + panel!.height).toBeLessThanOrEqual(
        hero!.y + hero!.height,
      );
    }
    await page.setViewportSize({ width: 1440, height: 1000 });
  }
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator(".concept-card")).toHaveCount(7);
  await expect(page.locator(".example-card")).toHaveCount(4);
  await expect(page.locator(".source-card")).toHaveCount(4);
  await expect(page.locator(".learning-card")).toHaveCount(4);
  await expect(page.locator(".path-meta")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "أساسيات الوارث" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page
    .getByRole("button", { name: "ما معنى العصبة؟", exact: true })
    .click();
  await expect(page.getByRole("textbox")).toHaveValue("ما معنى العصبة؟");
  await expect(page.locator(".ask-result")).toContainText("ما معنى العصبة؟");
  await expect(page.locator(".mode-selector")).toHaveCount(0);
  await page.locator(".concept-card").first().click();
  await expect(page).toHaveURL(/\/concepts\/fixed-share-heirs$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "أصحاب الفروض",
  );
  await page
    .getByRole("link", { name: "العودة إلى جميع المفاهيم", exact: true })
    .click();
  await page.locator(".example-card").first().click();
  await expect(page).toHaveURL("/learn/calculation/fixed-shares");
  await page
    .getByRole("link", { name: "جميع مسارات الحساب", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.locator(".learning-card .path-toggle")).toHaveCount(4);
  await expect(page.locator(".path-expansion")).toHaveCount(0);
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
  expect(errors).toEqual([]);
});
