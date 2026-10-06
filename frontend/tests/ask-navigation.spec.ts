import { test, expect } from "@playwright/test";

const answer = (text: string) => ({
  mode: "learn",
  language: "ar",
  decision_state: "ready",
  answer: text,
  sources: [],
  source_excerpts: [],
});

test.beforeEach(async ({ page }) => {
  // Observe only Ask fetch signals; Next may cancel its own navigation fetches.
  await page.addInitScript(() => {
    const original = window.fetch;
    (window as unknown as { askAborts: number }).askAborts = 0;
    window.fetch = function (input, init) {
      if (String(input).includes("/api/ask")) {
        init?.signal?.addEventListener("abort", () => {
          (window as unknown as { askAborts: number }).askAborts++;
        });
      }
      return original.call(this, input, init);
    };
  });
});

for (const completeAway of [true, false]) {
  test(`home request survives navigation; completed away=${completeAway}`, async ({
    page,
  }) => {
    let calls = 0;
    let release!: () => void;
    const held = new Promise<void>((resolve) => {
      release = resolve;
    });
    await page.route("**/api/ask", async (route) => {
      calls++;
      await held;
      await route.fulfill({ json: answer("Home completed answer") });
    });
    await page.goto("/");
    await page.locator("#question").fill("Home question");
    await page.locator("#question").press("Enter");
    await expect.poll(() => calls).toBe(1);
    await page.locator('.concept-card[href="/concepts/tasib"]').click();
    await expect(page).toHaveURL(/concepts\/tasib$/);
    await expect(page.locator("#concept-question")).toHaveValue("");
    await expect(page.locator(".concept-tutor .ask-loading")).toHaveCount(0);
    expect(
      await page.evaluate(
        () => (window as unknown as { askAborts: number }).askAborts,
      ),
    ).toBe(0);
    if (completeAway) {
      release();
      await expect
        .poll(() =>
          page.evaluate(
            () =>
              JSON.parse(sessionStorage.getItem("mawarith:ask:home") || "{}")
                .result?.answer,
          ),
        )
        .toBe("Home completed answer");
    }
    await page.evaluate(() => {
      (window as unknown as { returnCLS: number }).returnCLS = 0;
      new PerformanceObserver((list) => {
        for (const item of list.getEntries()) {
          const shift = item as PerformanceEntry & {
            hadRecentInput: boolean;
            value: number;
          };
          if (!shift.hadRecentInput)
            (window as unknown as { returnCLS: number }).returnCLS +=
              shift.value;
        }
      }).observe({ type: "layout-shift", buffered: false });
    });
    await page.locator(".curriculum-back").click();
    await expect(page.locator("#question")).toHaveValue("Home question");
    await expect(page.locator(".hero-experience")).toHaveAttribute(
      "data-restoring",
      "true",
    );
    expect(
      await page
        .locator(".hero-intro-collapse")
        .evaluate((node) => getComputedStyle(node).transitionDuration),
    ).toBe("0s");
    if (!completeAway) {
      await expect(page.locator(".answer-skeleton")).toBeVisible();
      await page.locator(".ask-panel").dispatchEvent("submit");
      expect(calls).toBe(1);
      release();
    }
    await expect(page.locator(".ask-answer")).toContainText(
      "Home completed answer",
    );
    await page.waitForTimeout(650);
    expect(
      await page.evaluate(
        () => (window as unknown as { returnCLS: number }).returnCLS,
      ),
    ).toBeLessThan(0.05);
    // A second return reads the completed session snapshot without a request.
    await page.locator('.concept-card[href="/concepts/tasib"]').click();
    await page.locator(".curriculum-back").click();
    await expect(page.locator(".ask-answer")).toContainText(
      "Home completed answer",
    );
    expect(calls).toBe(1);
    expect(
      await page.evaluate(
        () => (window as unknown as { askAborts: number }).askAborts,
      ),
    ).toBe(0);
  });
}

test("Cancel after returning aborts only the original surface request", async ({
  page,
}) => {
  let calls = 0;
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/ask", async (route) => {
    calls++;
    await held;
    await route.fulfill({ json: answer("Cancelled response") }).catch(() => {});
  });
  await page.goto("/");
  await page.locator("#question").fill("Cancel question");
  await page.locator("#question").press("Enter");
  await page.locator('.concept-card[href="/concepts/tasib"]').click();
  await page.locator(".curriculum-back").click();
  await expect(page.locator(".answer-skeleton")).toBeVisible();
  await page.getByRole("button", { name: "إلغاء الطلب" }).click();
  await expect(page.locator(".ask-feedback")).toContainText("تم إلغاء الطلب");
  await expect(page.locator(".ask-submit")).toBeEnabled();
  expect(
    await page.evaluate(
      () => (window as unknown as { askAborts: number }).askAborts,
    ),
  ).toBe(1);
  release();
  await expect(page.locator(".ask-result")).toHaveCount(0);
  expect(calls).toBe(1);
});

test("home and concept requests remain independent while both are pending", async ({
  page,
}) => {
  let calls = 0;
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/ask", async (route) => {
    calls++;
    const home = route.request().postDataJSON().question === "Home question";
    if (home) await held;
    await route.fulfill({
      json: answer(home ? "Home answer" : "Concept answer"),
    });
  });
  await page.goto("/");
  await page.locator("#question").fill("Home question");
  await page.locator("#question").press("Enter");
  await page.locator('.concept-card[href="/concepts/tasib"]').click();
  await page.locator("#concept-question").fill("Concept question");
  await page.locator("#concept-question").press("Enter");
  await expect(page.locator(".ask-answer")).toContainText("Concept answer");
  release();
  await expect(page.locator(".ask-answer")).not.toContainText("Home answer");
  await page.locator(".curriculum-back").click();
  await expect(page.locator(".ask-answer")).toContainText("Home answer");
  expect(calls).toBe(2);
});

test("an error received away is restored with Retry on the original surface", async ({
  page,
}) => {
  let calls = 0;
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/ask", async (route) => {
    calls++;
    if (calls === 1) {
      await held;
      await route.fulfill({
        status: 503,
        json: { error: { code: "backend_unavailable" } },
      });
    } else await route.fulfill({ json: answer("Retried answer") });
  });
  await page.goto("/");
  await page.locator("#question").fill("Error question");
  await page.locator("#question").press("Enter");
  await page.locator('.concept-card[href="/concepts/tasib"]').click();
  release();
  await expect
    .poll(() =>
      page.evaluate(
        () =>
          JSON.parse(sessionStorage.getItem("mawarith:ask:home") || "{}").error,
      ),
    )
    .toBe("backend_unavailable");
  await expect(page.locator(".concept-tutor .ask-error")).toHaveCount(0);
  await page.locator(".curriculum-back").click();
  await expect(page.locator(".ask-feedback[role=alert]")).toBeVisible();
  await page.getByRole("button", { name: "حاول مجددًا" }).click();
  await expect(page.locator(".ask-answer")).toContainText("Retried answer");
  expect(calls).toBe(2);
});
