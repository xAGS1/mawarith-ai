import { test, expect } from "@playwright/test";
import { learningPathCurriculum } from "../src/data/learning-paths";

test("all curricula render without API requests and fit both languages", async ({
  page,
}, info) => {
  const errors: string[] = [],
    requests: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    if (request.url().includes("/api/ask")) requests.push(request.url());
  });
  for (const path of learningPathCurriculum) {
    await page.goto(`/learn/paths/${path.slug}`);
    await expect(page.locator("main h1")).toHaveText(path.title.ar);
    await expect(page.locator(".path-stations > li")).toHaveCount(
      path.stations.length,
    );
    await expect(page.locator(".path-outcomes > li")).toHaveCount(
      path.outcomes.length,
    );
    await expect(page.locator('a[href="#path-stations"]')).toBeVisible();
    await expect(page.locator('a[href="#path-tutor"]')).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    for (const link of await page.locator(".path-related-concepts a").all()) {
      expect(await link.getAttribute("href")).toMatch(
        /^\/concepts\/(fixed-share-heirs|fixed-share|asabah|tasib|blocking|awl|radd)$/,
      );
    }
  }
  await page.getByRole("button", { name: "Switch to English" }).click();
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  await expect(page.locator("main h1")).toHaveText("Special & Advanced Cases");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `test-results/path-curriculum-${info.project.name}.png`,
    fullPage: true,
  });
  expect(requests).toEqual([]);
  expect(errors).toEqual([]);
});

test("path tutor sends original question and optional context through existing Ask flow", async ({
  page,
}) => {
  let body: unknown;
  await page.route("**/api/ask", async (route) => {
    body = route.request().postDataJSON();
    await route.fulfill({
      json: {
        mode: "learn",
        language: "ar",
        decision_state: "ready",
        answer: "شرح تعليمي من الأدلة المتاحة.",
        source_excerpts: [],
        sources: [],
        limitations: [],
      },
    });
  });
  await page.goto("/learn/paths/shares-rules");
  await page.locator("#concept-question").fill("وش الفرق بينهما؟");
  await page.locator(".concept-tutor form button").click();
  await expect(page.locator(".ask-result")).toContainText(
    "شرح تعليمي من الأدلة المتاحة.",
  );
  expect(body).toEqual({
    mode: "learn",
    question: "وش الفرق بينهما؟",
    concept_context: { slug: "shares-rules", title: "الأنصبة والقواعد" },
  });
  await expect(page).toHaveURL(/\/learn\/paths\/shares-rules$/);
});
