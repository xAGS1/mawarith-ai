import { test, expect } from "@playwright/test";
import { visualShare } from "../src/components/ask/ready-result";
import { exampleQuestions } from "../src/data/home";
const ready = {
  mode: "learn",
  language: "ar",
  decision_state: "ready",
  answer: "شرح تعليمي موثق وموجز.",
  sources: [],
  source_excerpts: [],
};

test("example questions have unique Arabic and English identities", () => {
  for (const language of ["ar", "en"] as const) {
    expect(
      new Set(exampleQuestions.map((question) => question[language])).size,
    ).toBe(exampleQuestions.length);
  }
});

test("comparison chip renders once and submits once without duplicate-key errors", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  let calls = 0;
  await page.route("**/api/ask", async (route) => {
    calls++;
    await route.fulfill({ json: ready });
  });
  await page.goto("/");
  const comparison = page
    .locator(".question-chips button")
    .filter({ hasText: "ما الفرق بين الفرض والتعصيب؟" });
  await expect(comparison).toHaveCount(1);
  await comparison.click();
  await expect(page.locator(".ask-result-question")).toHaveText(
    "ما الفرق بين الفرض والتعصيب؟",
  );
  expect(calls).toBe(1);
  expect(errors.filter((error) => /same key|unique.*key/i.test(error))).toEqual(
    [],
  );
});

test("rational decoration never replaces exact fractions", () => {
  expect(visualShare("1/3", 2)).toBe(66.66);
  for (const value of ["0.5", "1/0", "2/1", "unknown"])
    expect(visualShare(value, 1)).toBeNull();
});

test("Enter, Shift+Enter, immediate examples, local cancel and result focus", async ({
  page,
}) => {
  let calls = 0;
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/ask", async (route) => {
    calls++;
    if (calls === 1) await held;
    await route.fulfill({ json: ready }).catch(() => {});
  });
  await page.goto("/");
  const composer = page.locator("#question");
  await expect(composer).toHaveJSProperty("tagName", "TEXTAREA");
  await composer.fill("سؤال");
  await composer.press("Shift+Enter");
  await expect(composer).toHaveValue("سؤال\n");
  expect(calls).toBe(0);
  await composer.press("Enter");
  await expect(page.locator(".hero")).toHaveAttribute("data-mode", "active");
  await expect(page.locator(".home-answer-workspace")).toBeVisible();
  await expect(page.locator(".answer-skeleton")).toBeVisible();
  await expect(page.locator(".ask-submit")).toBeDisabled();
  await page.locator(".ask-panel").dispatchEvent("submit");
  expect(calls).toBe(1);
  await page.getByRole("button", { name: "إلغاء الطلب" }).click();
  await expect(
    page.getByText("تم إلغاء الطلب.", { exact: false }),
  ).toBeVisible();
  await expect(page.locator(".ask-feedback[role=alert]")).toHaveCount(0);
  release();
  await page.getByRole("button", { name: "مسح", exact: true }).click();
  const chip = page.locator(".question-chips button").first();
  await expect(chip).toBeVisible();
  const example = await chip.innerText();
  await chip.click();
  await expect(page.locator(".ask-result-question")).toHaveText(example);
  await expect(page.locator(".ask-result > h3")).toBeFocused();
  await expect(composer).toHaveValue(example);
  expect(calls).toBe(2);
  await expect(page.locator(".answer-follow-up")).toHaveCount(0);
});

test("response replaces reserved workspace without unexpected layout shift", async ({
  page,
}) => {
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/ask", async (route) => {
    await held;
    await route.fulfill({ json: ready });
  });
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  await page.locator("#question").fill("ما معنى الفرض؟");
  await page.locator(".ask-submit").click();
  await expect(page.locator(".answer-skeleton")).toBeVisible();
  await page.waitForTimeout(500);
  const before = await page.locator(".home-answer-workspace").boundingBox();
  const composer = await page.locator(".ask-panel").boundingBox();
  await page.waitForTimeout(650);
  await page.evaluate(() => {
    (window as unknown as { askShift: number }).askShift = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const shift = entry as PerformanceEntry & {
          hadRecentInput: boolean;
          value: number;
        };
        if (!shift.hadRecentInput)
          (window as unknown as { askShift: number }).askShift += shift.value;
      }
    }).observe({ type: "layout-shift", buffered: false });
  });
  release();
  await expect(page.locator(".ask-answer")).toContainText(ready.answer);
  await page.waitForTimeout(150);
  const after = await page.locator(".home-answer-workspace").boundingBox();
  expect(Math.abs(after!.y - before!.y)).toBeLessThan(3);
  expect(Math.abs(after!.height - before!.height)).toBeLessThan(3);
  expect(
    Math.abs((await page.locator(".ask-panel").boundingBox())!.y - composer!.y),
  ).toBeLessThan(3);
  expect(
    await page.evaluate(
      () => (window as unknown as { askShift: number }).askShift,
    ),
  ).toBeLessThan(0.05);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("verified case hierarchy and clickable source panel", async ({ page }) => {
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        ...ready,
        mode: "case",
        case_details: {
          parsed_relations: {
            mentioned_relatives: [{ relation: "ابن", count: 2 }],
          },
          result: {
            verification: { is_consistent: true, total_fraction: "1" },
            post_tasil: {
              distribution: [{ heir: "ابن", count: 2, per_head_shares: "1/2" }],
            },
          },
        },
        source_excerpts: [
          {
            source_name: "مصدر الاختبار",
            page: 3,
            text: "النص الأصلي كما ورد.",
          },
        ],
      },
    }),
  );
  await page.goto("/");
  await page.locator("#question").fill("مات وترك ابنين");
  await page.locator(".ask-submit").click();
  await expect(page.locator(".case-relation-chips")).toHaveText("ابن ×2");
  await expect(page.locator(".verification-summary")).toContainText("1");
  await expect(page.locator(".distribution-bar")).toBeVisible();
  await expect(page.locator(".ask-distribution strong")).toHaveText("1/2");
  await page.locator(".tutor-source-chips button").click();
  await expect(page.locator(".ask-source-meta")).toBeVisible();
  await page.getByRole("button", { name: "عرض النص من المصدر" }).click();
  await expect(page.locator("blockquote")).toHaveText("النص الأصلي كما ورد.");
});

test("English composer cancellation stays distinct from errors", async ({
  page,
}) => {
  await page.route("**/api/ask", () => new Promise<void>(() => {}));
  await page.goto("/");
  await page.getByRole("button", { name: "Switch to English" }).click();
  await page.locator("#question").fill("Explain fixed shares");
  await page.locator("#question").press("Enter");
  await expect(page.locator(".ask-loading")).toHaveText(
    "Preparing your answer...",
  );
  await page.getByRole("button", { name: "Cancel request" }).click();
  await expect(
    page.getByText("Request cancelled.", { exact: false }),
  ).toBeVisible();
  await expect(page.locator(".ask-submit")).toBeEnabled();
  await expect(page.locator(".ask-feedback[role=alert]")).toHaveCount(0);
});

test("non-verified data never gets a verified badge or distribution", async ({
  page,
}) => {
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        ...ready,
        mode: "case",
        case_details: {
          result: {
            verification: { is_consistent: false, total_fraction: "1" },
            post_tasil: {
              distribution: [
                { heir: "Fixture", count: 1, per_head_shares: "1/1" },
              ],
            },
          },
        },
      },
    }),
  );
  await page.goto("/");
  await page.locator("#question").fill("Case fixture");
  await page.locator(".ask-submit").click();
  await expect(page.locator(".ask-answer")).toBeVisible();
  await expect(page.locator(".verification-summary")).toHaveCount(0);
  await expect(page.locator(".ask-distribution")).toHaveCount(0);
});

test("premium hero and long answers keep document scrolling only", async ({
  page,
}) => {
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        ...ready,
        mode: "case",
        case_details: {
          result: {
            verification: { is_consistent: true, total_fraction: "1" },
            post_tasil: {
              distribution: Array.from({ length: 12 }, (_, i) => ({
                heir: `Heir ${i + 1}`,
                count: 1,
                per_head_shares: "1/12",
              })),
            },
          },
        },
      },
    }),
  );
  await page.goto("/");
  await expect(page.locator(".question-chips button")).toHaveCount(5);
  await expect(page.locator("#hero-title")).toContainText("MAWARITH");
  await page.locator("#question").fill("Case fixture");
  await page.locator("#question").press("Enter");
  await expect(page.locator(".ask-distribution tbody tr")).toHaveCount(12);
  await page.waitForTimeout(500);
  const metrics = await page.evaluate(() => {
    const selectors = [
      "#main",
      ".hero",
      ".hero-inner",
      ".home-answer-workspace",
      ".ask-result",
      ".ready-result",
    ];
    return {
      scrollOwner: document.scrollingElement?.tagName,
      nested: selectors.filter((selector) => {
        const node = document.querySelector(selector)!;
        const style = getComputedStyle(node);
        return (
          ["auto", "scroll"].includes(style.overflowY) &&
          node.scrollHeight > node.clientHeight + 1
        );
      }),
      workspace: getComputedStyle(
        document.querySelector(".home-answer-workspace")!,
      ).overflowY,
      hero:
        document
          .querySelector(".home-answer-workspace")!
          .getBoundingClientRect().top -
        document.querySelector(".hero-experience")!.getBoundingClientRect().top,
    };
  });
  expect(metrics.scrollOwner).toBe("HTML");
  expect(metrics.nested).toEqual([]);
  expect(metrics.workspace).toBe("visible");
  expect(metrics.hero).toBeGreaterThanOrEqual(150);
  expect(metrics.hero).toBeLessThan(400);
  await page
    .locator(".ask-distribution tbody tr")
    .last()
    .scrollIntoViewIfNeeded();
  await expect(page.locator(".ask-distribution tbody tr").last()).toBeVisible();
  expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(0);
  expect(
    await page
      .locator(".home-answer-workspace")
      .evaluate((node) => node.scrollTop),
  ).toBe(0);
  const sticky = await page.locator(".ask-area").boundingBox();
  expect(sticky!.y).toBeGreaterThanOrEqual(77);
  expect(sticky!.y).toBeLessThan(110);
});

test("same composer morphs while intro and examples collapse", async ({
  page,
}) => {
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/ask", async (route) => {
    await held;
    await route.fulfill({ json: ready });
  });
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  const input = await page.locator("#question").elementHandle();
  const idle = await page.locator(".ask-panel").boundingBox();
  const idleHeight = await page
    .locator(".hero-experience")
    .evaluate((node) => node.getBoundingClientRect().height);
  await page.locator("#question").fill("Transition fixture");
  await page.locator("#question").press("Enter");
  await expect(page.locator(".hero-experience")).toHaveAttribute(
    "data-mode",
    "active",
  );
  await expect(page.locator(".answer-skeleton")).toBeVisible();
  await page.waitForTimeout(500);
  expect(
    await input!.evaluate(
      (node) => node === document.querySelector("#question"),
    ),
  ).toBe(true);
  expect(
    await page
      .locator(".hero-intro-collapse")
      .evaluate((node) => node.getBoundingClientRect().height),
  ).toBeLessThan(1);
  expect(
    await page
      .locator(".hero-examples-collapse")
      .evaluate((node) => node.getBoundingClientRect().height),
  ).toBeLessThan(1);
  const active = await page.locator(".ask-panel").boundingBox();
  expect(Math.abs(active!.x - idle!.x)).toBeLessThan(1);
  expect(active!.height).toBeLessThan(idle!.height);
  const workspace = await page.locator(".home-answer-workspace").boundingBox();
  expect(workspace!.y).toBeLessThan(idleHeight / 2);
  release();
  await expect(page.locator(".ask-answer")).toContainText(ready.answer);
  await page.waitForTimeout(350);
  expect(
    Math.abs(
      (await page.locator(".home-answer-workspace").boundingBox())!.y -
        workspace!.y,
    ),
  ).toBeLessThan(3);
});

test("reduced motion keeps the same functional sticky composer without animation", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.route("**/api/ask", (route) => route.fulfill({ json: ready }));
  await page.goto("/");
  await page.locator("#question").fill("Reduced motion fixture");
  await page.locator("#question").press("Enter");
  await expect(page.locator(".ask-answer")).toContainText(ready.answer);
  expect(
    await page
      .locator(".hero-intro-collapse")
      .evaluate((node) => getComputedStyle(node).transitionDuration),
  ).toBe("0s");
  expect(
    await page
      .locator(".ask-area")
      .evaluate((node) => getComputedStyle(node).position),
  ).toBe("sticky");
  await expect(page.locator("#question")).toHaveCount(1);
});
