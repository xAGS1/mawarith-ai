import { test, expect } from "@playwright/test";

const explanation =
  "Neutral educational explanation with no additional claims. ".repeat(70);
const excerpt = "Exact original fixture text.\n  Whitespace retained. ".repeat(
  250,
);
const source = {
  source_name: "Fixture source",
  section: "Fixture topic",
  page: 12,
  institution: "Fixture institution",
  source_url: "https://example.org/source",
};
const base = {
  mode: "learn",
  language: "ar",
  decision_state: "ready",
  evidence_status: "supported",
  answer: explanation,
  source_excerpts: [{ ...source, text: excerpt }],
  sources: [source, { source_name: "Second source", section: "Second topic" }],
  limitations: [
    "Arithmetic consistency does not establish legal completeness or correctness.",
    "Page numbers may be unavailable.",
  ],
};

test("long answer previews, nested source disclosure, warnings, navigation and follow-up", async ({
  page,
}, info) => {
  let calls = 0;
  await page.route("**/api/ask", (route) => {
    calls++;
    return route.fulfill({
      json:
        calls === 1
          ? base
          : {
              ...base,
              answer: "Short follow-up answer.",
              source_excerpts: [],
              sources: [],
              limitations: [],
            },
    });
  });
  await page.goto("/");
  await page.locator("#question").fill("Neutral educational question");
  await page.locator(".ask-submit").click();
  const result = page.locator(".ask-result");
  await expect(result.locator(".ask-answer p")).toHaveText(/…$/);
  expect(
    (await result.locator(".ask-answer p").textContent())!.length,
  ).toBeLessThanOrEqual(551);
  await expect(
    result.getByRole("button", { name: "عرض المزيد" }),
  ).toHaveAttribute("aria-expanded", "false");
  await expect(result.locator(".answer-safety-notes")).toBeVisible();
  await expect(result.locator(".answer-safety-notes")).toContainText(
    "الاتساق الحسابي",
  );
  await expect(result.locator("blockquote")).toBeHidden();
  await expect(page.locator(".answer-follow-up")).toHaveCount(0);
  await expect(
    result.getByRole("button", { name: "عرض المصادر (2)" }),
  ).toHaveAttribute("aria-expanded", "false");
  await result.getByRole("button", { name: "عرض المصادر (2)" }).click();
  await expect(result.locator(".ask-source-meta").first()).toContainText(
    "الصفحة 12",
  );
  await expect(result.locator(".ask-source-meta").first()).toContainText(
    "Fixture institution",
  );
  await expect(result.locator("blockquote")).toBeHidden();
  await result.getByRole("button", { name: "عرض النص من المصدر" }).click();
  expect(await result.locator("blockquote").textContent()).toBe(excerpt);
  expect(
    await result
      .locator(".source-excerpt-scroll")
      .evaluate((node) => getComputedStyle(node).overflowY),
  ).toBe("visible");
  await result.getByRole("button", { name: "إخفاء النص" }).click();
  await expect(result.locator("blockquote")).toBeHidden();
  await result.getByRole("button", { name: "عرض المزيد" }).click();
  await expect(result.locator(".ask-answer p")).toHaveText(explanation.trim());
  await expect(result.locator(".answer-navigation")).toBeVisible();
  await result.getByRole("button", { name: "عرض أقل" }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await result.getByRole("button", { name: "تفاصيل الإجابة" }).click();
  await expect(result).toContainText("Page numbers may be unavailable.");
  await page.locator("#question").fill("Neutral follow-up");
  await page.locator("#question").press("Enter");
  await expect(page.locator(".ask-answer")).toContainText(
    "Short follow-up answer.",
  );
  expect(calls).toBe(2);
  await expect(
    page.locator(".ask-result").getByRole("button", { name: "عرض المزيد" }),
  ).toHaveCount(0);
  await expect(page.locator(".answer-navigation")).toHaveCount(0);
});

test("insufficiency is compact and clarification text is never truncated", async ({
  page,
}) => {
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        ...base,
        decision_state: "needs_clarification",
        mode: "case",
        evidence_status: null,
        answer: explanation,
        clarification_question: "Critical clarification fixture?",
        source_excerpts: [],
        sources: [],
      },
    }),
  );
  await page.goto("/");
  await page.locator("#question").fill("Case fixture");
  await page.locator(".ask-submit").click();
  await expect(page.locator(".ask-answer p")).toHaveText(explanation.trim());
  await expect(page.locator(".ask-clarification")).toBeVisible();
  await expect(
    page.locator(".ask-result").getByRole("button", { name: "عرض المزيد" }),
  ).toHaveCount(0);
  await page.unroute("**/api/ask");
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        ...base,
        decision_state: "out_of_scope",
        evidence_status: "insufficient",
        answer: "الأدلة المتاحة لا تكفي للإجابة بثقة.",
        source_excerpts: [],
        sources: [],
        limitations: [],
      },
    }),
  );
  await page.reload();
  await page.locator("#question").fill("Unsupported fixture");
  await page.locator(".ask-submit").click();
  await expect(page.locator(".ask-result h3")).toHaveText(
    "تعذر تقديم شرح موثق",
  );
  await expect(page.locator(".answer-source-disclosure")).toHaveCount(0);
  await expect(page.locator(".source-excerpt-scroll")).toHaveCount(0);
});

test("long calculation explanation never collapses verified distribution rows", async ({
  page,
}) => {
  const distribution = Array.from({ length: 12 }, (_, i) => ({
    heir: `Fixture ${i + 1}`,
    count: 1,
    per_head_shares: "1/12",
  }));
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        ...base,
        mode: "case",
        source_excerpts: [],
        sources: [],
        case_details: {
          result: {
            verification: { is_consistent: true, total_fraction: "1" },
            post_tasil: { distribution },
          },
        },
      },
    }),
  );
  await page.goto("/");
  await page.locator("#question").fill("Calculation fixture");
  await page.locator(".ask-submit").click();
  await expect(page.locator(".ask-distribution")).toBeVisible();
  await expect(page.locator(".ask-distribution tbody tr")).toHaveCount(12);
  await expect(page.locator(".ask-distribution tbody tr").last()).toBeVisible();
  await expect(
    page.locator(".ask-result").getByRole("button", { name: "عرض المزيد" }),
  ).toBeVisible();
  await expect(page.locator(".answer-safety-notes")).toBeVisible();
});
