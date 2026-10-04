import { test, expect } from "@playwright/test";

test("four localized navigation paths, responsive rows and focus effects", async ({
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
  const links = cards.locator(".path-toggle");
  await expect(links).toHaveCount(4);
  for (const [index, slug] of [
    "beginner",
    "intermediate",
    "advanced",
    "teachers-students",
  ].entries()) {
    await expect(links.nth(index)).toHaveAttribute(
      "href",
      `/learn/paths/${slug}`,
    );
    await expect(links.nth(index)).not.toHaveAttribute("aria-expanded");
    await links.nth(index).focus();
    await expect(cards.nth(index)).toHaveCSS(
      "transform",
      "matrix(1, 0, 0, 1, 0, -4)",
    );
  }
  await expect(
    cards.locator(".path-coming-soon, .path-expansion, button"),
  ).toHaveCount(0);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await links.first().focus();
  await expect(cards.first()).toHaveCSS("transform", "none");
  await expect(cards.first().locator("img")).toHaveCSS("transform", "none");
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await links.first().blur();
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
  await expect(cards.locator("p")).toHaveText([
    "Core concepts and foundational rules",
    "Applied concepts and combined cases",
    "Advanced cases and rule interaction",
    "Educational tools and learning resources",
  ]);
});

test("English card text stays separated and equal height; Arabic styles stay intact", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  const cards = page.locator(".learning-card");
  const arabicStyles = () =>
    cards.evaluateAll((nodes) =>
      nodes.map((node) => {
        const content = getComputedStyle(node.querySelector(".path-content")!);
        const title = getComputedStyle(node.querySelector("h3")!);
        return {
          padding: content.padding,
          display: content.display,
          font: title.fontSize,
          height: node.clientHeight,
        };
      }),
    );
  const original = await arabicStyles();
  await page.getByRole("button", { name: "Switch to English" }).click();
  const initialViewport = page.viewportSize()!;
  const widths =
    testInfo.project.name === "desktop" ? [1366, 1440, 1920, 900, 390] : [390];
  for (const width of widths) {
    await page.setViewportSize({ width, height: 1000 });
    const measurements = await cards.evaluateAll((nodes) =>
      nodes.map((node) => {
        const title = node.querySelector("h3")!.getBoundingClientRect();
        const subtitle = node.querySelector("p")!.getBoundingClientRect();
        const action = node
          .querySelector(".path-toggle, .path-coming-soon")!
          .getBoundingClientRect();
        const content = node
          .querySelector(".path-content")!
          .getBoundingClientRect();
        return {
          height: node.clientHeight,
          titleEnd: title.bottom,
          subtitleStart: subtitle.top,
          subtitleEnd: subtitle.bottom,
          actionStart: action.top,
          actionEnd: action.bottom,
          contentEnd: content.bottom,
        };
      }),
    );
    expect(new Set(measurements.map((item) => item.height)).size).toBe(1);
    for (const item of measurements) {
      expect(item.subtitleStart - item.titleEnd).toBeGreaterThanOrEqual(5);
      expect(item.actionStart - item.subtitleEnd).toBeGreaterThanOrEqual(5);
      expect(item.actionEnd).toBeLessThan(item.contentEnd - 12);
    }
    await page.locator("#learning-path").screenshot({
      path: `test-results/learning-paths-english-${width}-${testInfo.project.name}.png`,
    });
  }
  await page.setViewportSize(initialViewport);
  await page.getByRole("button", { name: "التبديل إلى العربية" }).click();
  expect(await arabicStyles()).toEqual(original);
});
