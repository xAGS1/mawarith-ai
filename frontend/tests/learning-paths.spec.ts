import { test, expect } from "@playwright/test";

test("four localized paths, responsive rows and unavailable paths", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  const cards = page.locator(".learning-card");
  await expect(cards).toHaveCount(4);
  await expect(cards.locator("h3")).toHaveText([
    "المستوى المبتدئ",
    "المستوى المتوسط",
    "المستوى المتقدم",
    "للمعلمين والطلاب",
  ]);
  const unavailable = page.locator(
    '.learning-card[data-availability="coming_soon"]',
  );
  await expect(unavailable).toHaveCount(3);
  await expect(unavailable.locator(".path-coming-soon")).toHaveText([
    "قريبًا",
    "قريبًا",
    "قريبًا",
  ]);
  await expect(unavailable.locator("button, a")).toHaveCount(0);
  await expect(cards.locator(".path-meta")).toHaveCount(0);
  for (const image of await cards.locator("img").all()) {
    await image.scrollIntoViewIfNeeded();
    await expect
      .poll(() => image.evaluate((node: HTMLImageElement) => node.naturalWidth))
      .toBeGreaterThan(0);
  }
  if (testInfo.project.name === "desktop") {
    for (const [width, columns] of [
      [1440, 4],
      [900, 2],
      [390, 1],
    ]) {
      await page.setViewportSize({ width, height: 1000 });
      const boxes = await cards.evaluateAll((nodes) =>
        nodes.map((node) => ({
          x: node.getBoundingClientRect().x,
          y: node.getBoundingClientRect().y,
        })),
      );
      expect(new Set(boxes.map((box) => box.x)).size).toBe(columns);
      expect(new Set(boxes.map((box) => box.y)).size).toBe(4 / columns);
      await page
        .locator("#learning-path")
        .screenshot({ path: `test-results/learning-paths-${width}.png` });
    }
  }
  await page.getByRole("button", { name: "Switch to English" }).click();
  await expect(cards.locator("h3")).toHaveText([
    "Beginner",
    "Intermediate",
    "Advanced",
    "Teachers & Students",
  ]);
  await expect(unavailable.locator(".path-coming-soon")).toHaveText([
    "Coming soon",
    "Coming soon",
    "Coming soon",
  ]);
  await expect(cards.locator("p")).toHaveText([
    "Core concepts and foundational rules",
    "Applied concepts and combined cases",
    "Advanced cases and deeper rule interaction",
    "Educational tools and learning resources",
  ]);
});
