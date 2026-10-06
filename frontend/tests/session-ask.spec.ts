import { test, expect } from "@playwright/test";

const scopes = [
  {
    route: "/",
    key: "mawarith:ask:home",
    input: "#question",
    submit: ".ask-submit",
  },
  {
    route: "/concepts/tasib",
    key: "mawarith:ask:concept:tasib",
    input: "#concept-question",
    submit: ".concept-tutor > form button",
  },
  {
    route: "/learn/paths/shares-rules",
    key: "mawarith:ask:path:shares-rules",
    input: "#concept-question",
    submit: ".concept-tutor > form button",
  },
];
for (const scope of scopes) {
  test(`${scope.key} restores draft, complete answer and error without resubmitting`, async ({
    page,
  }) => {
    let count = 0;
    await page.route("**/api/ask", (route) => {
      count++;
      return route.fulfill({
        json: {
          mode: "learn",
          language: "ar",
          decision_state: "needs_clarification",
          answer: "جواب محفوظ",
          clarification_question: "سؤال توضيحي محفوظ",
          evidence_status: "supported",
          key_concepts: [{ term: "مصطلح", explanation: "شرح مصطلح" }],
          limitations: ["حدود محفوظة"],
          sources: [{ source_name: "مصدر محفوظ" }],
          source_excerpts: [
            { text: "نص المصدر المحفوظ", source_name: "مصدر محفوظ" },
          ],
          case_details: { result: null },
        },
      });
    });
    await page.goto(scope.route);
    await page.locator(scope.input).fill("سؤال المستخدم");
    await page.locator(scope.submit).click();
    await expect(page.locator(".ask-result")).toContainText("جواب محفوظ");
    await expect(page.locator(".ask-result")).toContainText("سؤال المستخدم");
    await page.locator(scope.input).fill("مسودة جديدة");
    // Leave through actual client navigation; the completed answer must survive unmount.
    const homeLink =
      scope.route === "/"
        ? page.locator('.concept-card[href="/concepts/awl"]')
        : page.locator(".curriculum-back");
    await homeLink.click();
    if (scope.route === "/") await page.locator(".curriculum-back").click();
    else await page.locator(`a[href="${scope.route}"]`).first().click();
    await expect(page.locator(scope.input)).toHaveValue("مسودة جديدة");
    await expect(page.locator(".ask-result")).toContainText("جواب محفوظ");
    await expect(page.locator(".ask-result")).toContainText(
      "سؤال توضيحي محفوظ",
    );
    await page.reload();
    await expect(page.locator(scope.input)).toHaveValue("مسودة جديدة");
    await expect(page.locator(".ask-result")).toContainText("حدود محفوظة");
    expect(count).toBe(1);
    const saved = await page.evaluate(
      (key) => JSON.parse(sessionStorage.getItem(key)!),
      scope.key,
    );
    expect(saved.version).toBe(1);
    expect(saved.result.source_excerpts[0].text).toBe("نص المصدر المحفوظ");
    expect(saved.result.case_details).toEqual({ result: null });
    expect(saved.pending).toBeUndefined();
    await page.evaluate(() =>
      sessionStorage.setItem("mawarith:ask:concept:awl", "other state"),
    );
    await page.getByRole("button", { name: "مسح", exact: true }).click();
    await expect(page.locator(scope.input)).toHaveValue("");
    await expect(page.locator(".ask-result")).toHaveCount(0);
    expect(
      await page.evaluate((key) => sessionStorage.getItem(key), scope.key),
    ).toBeNull();
    expect(
      await page.evaluate(() =>
        sessionStorage.getItem("mawarith:ask:concept:awl"),
      ),
    ).toBe("other state");
  });
}

test("concept and path slugs stay isolated, explicit case prefill wins", async ({
  page,
}) => {
  await page.goto("/concepts/tasib");
  await page.locator("#concept-question").fill("تعصيب فقط");
  await page.locator(".curriculum-back").click();
  await page.locator('a[href="/concepts/awl"]').first().click();
  await expect(page.locator("#concept-question")).toHaveValue("");
  await page.locator("#concept-question").fill("awl draft");
  await page.locator(".curriculum-back").click();
  await page.locator('a[href="/concepts/tasib"]').first().click();
  await expect(page.locator("#concept-question")).toHaveValue("تعصيب فقط");
  await page.goto("/learn/paths/shares-rules");
  await page.locator("#concept-question").fill("المسار الأول");
  await page.goto("/learn/paths/special-advanced");
  await expect(page.locator("#concept-question")).toHaveValue("");
  await page.goto("/learn/paths/shares-rules");
  await expect(page.locator("#concept-question")).toHaveValue("المسار الأول");
  await page.goto("/concepts/tasib");
  await expect(page.locator("#concept-question")).toHaveValue("تعصيب فقط");
  await page.goto("/");
  await page.locator("#question").fill("old home draft");
  await page.goto("/learn/calculation/shares-and-tasib");
  await page
    .getByRole("link", { name: "جرّب هذه الحالة", exact: true })
    .click();
  await expect(page.locator("#question")).toHaveValue(
    "توفي رجل وترك زوجة وأمًا وابنين وبنتًا.",
  );
  await page.reload();
  await expect(page.locator("#question")).toHaveValue(
    "توفي رجل وترك زوجة وأمًا وابنين وبنتًا.",
  );
});

test("departed requests never restore loading or stale responses", async ({
  page,
}) => {
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/ask", async (route) => {
    await held;
    await route
      .fulfill({
        json: {
          mode: "learn",
          language: "ar",
          decision_state: "ready",
          answer: "stale answer",
        },
      })
      .catch(() => {});
  });
  await page.goto("/concepts/tasib");
  await page.locator("#concept-question").fill("question");
  await page.locator(".concept-tutor > form button").click();
  await expect(page.locator(".concept-tutor > form button")).toBeDisabled();
  await page.locator(".curriculum-back").click();
  await expect(page.locator(".concept-tutor")).toHaveCount(0);
  release();
  await page.goto("/concepts/tasib");
  await expect(page.locator("#concept-question")).toHaveValue("question");
  await expect(page.locator(".concept-tutor > form button")).toBeEnabled();
  await expect(page.locator(".ask-result")).toHaveCount(0);
});

test("invalid version and malformed result are ignored", async ({ page }) => {
  for (const data of [
    "{broken",
    JSON.stringify({ version: 99 }),
    JSON.stringify({
      version: 1,
      question: "bad",
      submitted: "bad",
      error: null,
      result: { mode: ["learn"], answer: "bad" },
    }),
  ]) {
    await page.goto("/");
    await page.evaluate(
      (data) => sessionStorage.setItem("mawarith:ask:home", data),
      data,
    );
    await page.reload();
    await expect(page.locator("#question")).toHaveValue("");
    await expect(page.locator(".ask-submit")).toBeEnabled();
  }
});

test("meaningful errors restore, transient busy does not", async ({ page }) => {
  let busy = false;
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      status: busy ? 429 : 503,
      json: { error: { code: busy ? "busy" : "backend_unavailable" } },
    }),
  );
  await page.goto("/concepts/tasib");
  await page.locator("#concept-question").fill("سؤال");
  await page.locator(".concept-tutor > form button").click();
  await expect(page.locator(".ask-error")).toBeVisible();
  await page.reload();
  await expect(page.locator(".ask-error")).toBeVisible();
  await expect(page.locator(".concept-tutor > form button")).toBeEnabled();
  busy = true;
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.locator(".ask-error")).toContainText("MAWARITH يعالج");
  await page.reload();
  await expect(page.locator(".ask-error")).toHaveCount(0);
});
