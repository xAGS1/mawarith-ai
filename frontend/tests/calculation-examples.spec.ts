import { test, expect } from "@playwright/test";
import { calculationPaths } from "../src/data/calculation-paths";

test("compact calculation paths, offline lessons, source provenance and review-before-submit handoff", async ({
  page,
}, info) => {
  const errors: string[] = [],
    requests: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    if (request.url().includes("/api/ask")) requests.push(request.url());
  });
  await page.goto("/");
  const cards = page.locator(".calculation-path-card");
  await expect(cards).toHaveCount(4);
  await expect(page.locator("#examples h2")).toHaveText(
    "كيف تُبنى مسألة الميراث؟",
  );
  await expect(page.locator(".calculation-example")).toHaveCount(0);
  const height = await page
    .locator("#examples")
    .evaluate((node) => node.getBoundingClientRect().height);
  const previousHeight = info.project.name === "desktop" ? 497 : 1167;
  expect(height).toBeLessThan(previousHeight);
  console.log(
    `${info.project.name} calculation section: ${previousHeight}px → ${height}px`,
  );
  await page
    .locator("#examples")
    .screenshot({
      path: `test-results/calculation-paths-${info.project.name}.png`,
    });
  for (const [index, path] of calculationPaths.entries()) {
    await page.goto("/");
    await cards.nth(index).click();
    await expect(page).toHaveURL(`/learn/calculation/${path.slug}`);
    await expect(page.locator("main h1")).toHaveText(path.title.ar);
    await expect(page.locator(".calculation-steps li")).toHaveCount(
      path.steps.length,
    );
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const source = page.locator(".calculation-evidence details").first();
    await source.locator("summary").click();
    await expect(source.locator("blockquote")).toHaveText(path.sources[0].text);
    if (path.slug === "awl")
      await expect(page.locator(".calculation-explanation")).toContainText(
        "27",
      );
    if (path.slug === "radd") {
      await expect(page.locator(".calculation-lesson-example")).toContainText(
        "مثال مفاهيمي",
      );
      await expect(page.locator(".calculation-lesson-example")).toContainText(
        "لا مستحق له من العصبات",
      );
    }
    await page
      .getByRole("link", { name: "جرّب هذه الحالة", exact: true })
      .click();
    await expect(page.locator("#question")).toHaveValue(path.tryCase.ar);
    await expect(page.locator("#question")).toBeFocused();
    expect(requests).toEqual([]);
  }
  await page.goto("/learn/calculation/radd");
  await page.getByRole("button", { name: "Switch to English" }).click();
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  await expect(page.locator("main h1")).toHaveText("Radd");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `test-results/calculation-lesson-${info.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole("link", { name: "Try this case", exact: true }).click();
  await expect(page.locator("#question")).toHaveValue(
    calculationPaths[3].tryCase.en,
  );
  expect(requests).toEqual([]);
  expect(errors).toEqual([]);
});
