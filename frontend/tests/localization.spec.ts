import { test, expect } from "@playwright/test";

test("Arabic default, in-place English switch, persistence and Arabic return", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator(".hero-assurances")).toHaveText(
    "شرح موثوق بالمصادر • تعلّم يناسب مختلف المستويات • بالعربية والإنجليزية",
  );
  await page.evaluate(() => {
    (window as Window & { localeSentinel?: string }).localeSentinel =
      "same-page";
  });
  await page.getByRole("textbox").fill("My own question");
  await page.getByRole("button", { name: "Switch to English" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  await expect(page.locator(".hero-assurances")).toHaveText(
    "Source-grounded explanations • Learning for different levels • Arabic and English",
  );
  await expect(page.locator(".mode-selector")).toHaveCount(0);
  await expect(page.locator(".hero h2")).toContainText(
    "Your journey to understanding Islamic inheritance",
  );
  await expect(page.getByRole("textbox")).toHaveValue("My own question");
  await expect(page.locator(".concept-card").first()).toContainText(
    "Fixed-share heirs",
  );
  await expect(page.locator(".example-card").first()).toContainText(
    "Wife, mother, sons and daughter",
  );
  await expect(page.locator(".source-card").first()).toContainText("The Quran");
  expect(
    await page.evaluate(
      () => (window as Window & { localeSentinel?: string }).localeSentinel,
    ),
  ).toBe("same-page");
  expect(
    await page.evaluate(() => localStorage.getItem("mawarith-locale")),
  ).toBe("en");
  expect(await page.locator("body").innerText()).not.toMatch(/[\u0600-\u06ff]/);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.locator(".concept-card").first().click();
  await expect(page.getByRole("dialog")).toContainText(
    "What are fixed-share heirs?",
  );
  await page.getByRole("button", { name: "Close preview" }).click();
  await expect(page.locator(".learning-card .path-toggle")).toHaveText([
    /Explore path/,
    /Explore path/,
    /Explore path/,
    /Explore path/,
  ]);
  await page.screenshot({
    path: `test-results/home-english-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.getByRole("button", { name: "التبديل إلى العربية" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator(".concept-card").first()).toContainText(
    "أصحاب الفروض",
  );
  expect(
    await page.evaluate(() => localStorage.getItem("mawarith-locale")),
  ).toBe("ar");
});
