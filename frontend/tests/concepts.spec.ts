import { test, expect } from "@playwright/test";

const slugs = [
  "fixed-share-heirs",
  "fixed-share",
  "tasib",
  "asabah",
  "blocking",
  "awl",
  "radd",
];
test("all seven static concept routes work offline, RTL and without generation", async ({
  page,
}, info) => {
  let requests = 0;
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/api/ask", (route) => {
    requests++;
    return route.abort();
  });
  for (const slug of slugs) {
    await page.goto(`/concepts/${slug}`);
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator(".curriculum-provenance strong")).not.toBeEmpty();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await expect(
      page.locator(".curriculum-provenance blockquote"),
    ).toBeHidden();
  }
  expect(requests).toBe(0);
  expect(errors).toEqual([]);
  await page.goto("/concepts/fixed-share-heirs");
  await expect(page.locator(".curriculum-definition")).toContainText(
    "لم يتوفر",
  );
  await page.goto("/concepts/awl");
  await expect(page.locator(".curriculum-example")).toContainText("24");
  await expect(page.locator(".curriculum-example")).toContainText("27");
  await page.screenshot({
    path: `test-results/concept-awl-${info.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole("link", { name: "المفهوم التالي الرد" }).click();
  await expect(page).toHaveURL(/\/concepts\/radd$/);
});

test("contextual tutor uses existing proxy only on submit, inline sources and duplicate protection", async ({
  page,
}) => {
  let requests = 0;
  let finish!: () => void;
  const release = new Promise<void>((resolve) => {
    finish = resolve;
  });
  await page.route("**/api/ask", async (route) => {
    requests++;
    expect(route.request().postDataJSON()).toEqual({
      mode: "learn",
      question: "ليش يصير كذا؟",
      concept_context: { slug: "awl", title: "العول" },
    });
    await release;
    await route.fulfill({
      json: {
        mode: "learn",
        decision_state: "ready",
        evidence_status: "supported",
        language: "ar",
        answer: "إجابة اختبار محايدة.",
        sources: [{ source_name: "مصدر اختبار" }],
        source_excerpts: [
          { text: "مقتطف اختبار أصلي", source_name: "مصدر اختبار" },
        ],
      },
    });
  });
  await page.goto("/concepts/awl");
  await page
    .getByRole("button", { name: "اسأل MAWARITH", exact: true })
    .click();
  await expect(page.locator(".concept-tutor").getByRole("alert")).toContainText(
    "اكتب سؤالًا",
  );
  expect(requests).toBe(0);
  await page
    .getByRole("textbox", { name: "سؤالك", exact: true })
    .fill("ليش يصير كذا؟");
  await page.getByRole("textbox").press("Enter");
  await expect(
    page.getByRole("button", { name: "جارٍ البحث والشرح…" }),
  ).toBeDisabled();
  expect(requests).toBe(1);
  finish();
  await expect(page.locator(".ask-result")).toContainText(
    "إجابة اختبار محايدة",
  );
  await expect(page.locator(".ask-result blockquote")).toBeHidden();
  await page.locator(".tutor-source-disclosure > button").click();
  await page
    .locator(".ask-result")
    .getByRole("button", { name: "عرض النص من المصدر" })
    .click();
  await expect(page.locator(".ask-result blockquote")).toHaveText(
    "مقتطف اختبار أصلي",
  );
  await expect(page).toHaveURL(/\/concepts\/awl$/);
});

test("tutor failure can retry and insufficient evidence stays clear", async ({
  page,
}) => {
  let calls = 0;
  await page.route("**/api/ask", (route) => {
    calls++;
    return calls === 1
      ? route.fulfill({
          status: 503,
          json: { error: { code: "backend_unavailable" } },
        })
      : route.fulfill({
          json: {
            mode: "learn",
            language: "ar",
            decision_state: "out_of_scope",
            evidence_status: "insufficient",
            answer: "لا تكفي الأدلة المتاحة.",
          },
        });
  });
  await page.goto("/concepts/radd");
  await page.getByRole("textbox").fill("وش يعني الرد؟");
  await page.getByRole("textbox").press("Enter");
  await expect(page.locator(".concept-tutor").getByRole("alert")).toContainText(
    "الخدمة غير متاحة",
  );
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.locator(".ask-result")).toContainText(
    "تعذر تقديم شرح موثق",
  );
  expect(calls).toBe(2);
});

test("English curriculum keeps LTR layout and original source separate", async ({
  page,
}) => {
  await page.addInitScript(() => localStorage.setItem("mawarith-locale", "en"));
  await page.goto("/concepts/asabah");
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Residuary heirs",
  );
  await expect(page.locator(".curriculum-definition")).toContainText(
    "fixed shares exhaust",
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
