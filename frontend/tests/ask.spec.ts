import { test, expect } from "@playwright/test";
import { inferMode } from "../src/lib/ask/infer-mode";

test("mode inference is deterministic and conservative", () => {
  for (const question of [
    "ما معنى العصبة؟",
    "What is a residuary heir?",
    "Explain fixed shares",
    "Hello",
  ])
    expect(inferMode(question)).toBe("learn");
  for (const question of [
    "مات وترك زوجة وأما وابنين وبنت",
    "ترك بنتًا وأخًا",
    "احسب نصيب كل وريث",
    "A man died leaving a daughter",
    "Calculate inheritance shares",
  ])
    expect(inferMode(question)).toBe("case");
});

const base = {
  mode: "learn",
  language: "en",
  answer: "A grounded explanation [E1].",
  key_concepts: [{ term: "Example term", explanation: "Example definition" }],
  source_excerpts: [
    {
      text: "Neutral source text.\n  Exact spacing preserved.",
      source_name: "Test fixture",
      reference: "Example reference",
    },
  ],
  limitations: ["Fixture limitation"],
};

test("learn request, loading, ready sources, no direct backend call and empty input", async ({
  page,
}) => {
  const calls: { mode: string; question: string }[] = [];
  const direct: string[] = [];
  page.on("request", (req) => {
    if (req.url().includes(":8000")) direct.push(req.url());
  });
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/ask", async (route) => {
    calls.push(route.request().postDataJSON());
    await held;
    await route.fulfill({ json: { ...base, decision_state: "ready" } });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Switch to English" }).click();
  const submit = page.locator(".ask-submit");
  await page.getByRole("textbox").fill("   ");
  await submit.click();
  await expect(page.locator(".ask-feedback[role=alert]")).toContainText(
    "Please enter a question",
  );
  expect(calls).toHaveLength(0);
  await page.getByRole("textbox").fill("  What is a residuary heir?  ");
  await submit.click();
  await expect(submit).toBeDisabled();
  await expect(page.getByRole("status")).toContainText("Preparing your answer");
  release();
  await expect(page.locator(".ask-answer")).toContainText(
    "A grounded explanation.",
  );
  expect(calls).toEqual([
    { mode: "learn", question: "What is a residuary heir?" },
  ]);
  expect(direct).toEqual([]);
  expect(await page.locator(".ask-excerpts blockquote").textContent()).toBe(
    base.source_excerpts[0].text,
  );
  await expect(page.getByRole("textbox")).toHaveValue(
    "  What is a residuary heir?  ",
  );
});

for (const state of [
  "ready",
  "needs_clarification",
  "specialist_referral",
  "out_of_scope",
]) {
  test(`case response: ${state}`, async ({ page }) => {
    await page.route("**/api/ask", async (route) => {
      expect(route.request().postDataJSON().mode).toBe("case");
      await route.fulfill({
        json: {
          ...base,
          mode: "case",
          decision_state: state,
          clarification_question:
            state === "needs_clarification" ? "Which brother?" : null,
          case_details: {
            result: {
              verification: { is_consistent: true, total_fraction: "1" },
              post_tasil: {
                distribution: [
                  { heir: "Son", count: 1, per_head_shares: "1/1" },
                ],
              },
            },
          },
        },
      });
    });
    await page.goto("/");
    await page.getByRole("button", { name: "Switch to English" }).click();
    await page.getByRole("textbox").fill("A man died leaving a son.");
    await page.locator(".ask-submit").click();
    await expect(page.locator(".ask-answer")).toContainText(
      "A grounded explanation.",
    );
    if (state === "ready")
      await expect(page.locator(".ask-distribution")).toContainText("1/1");
    else await expect(page.locator(".ask-distribution")).toHaveCount(0);
    if (state === "needs_clarification")
      await expect(page.locator(".ask-clarification")).toContainText(
        "Which brother?",
      );
    await expect(page.locator(".ask-result")).toContainText(
      "Fixture limitation",
    );
  });
}

for (const [code, status, message] of [
  ["backend_unavailable", 503, "unavailable"],
  ["timeout", 504, "timed out"],
  ["backend_error", 500, "could not be completed"],
] as const) {
  test(`${code} error can be retried`, async ({ page }) => {
    let count = 0;
    await page.route("**/api/ask", (route) => {
      count++;
      return route.fulfill(
        count === 1
          ? { status, json: { error: { code } } }
          : { json: { ...base, decision_state: "ready" } },
      );
    });
    await page.goto("/");
    await page.getByRole("button", { name: "Switch to English" }).click();
    await page.getByRole("textbox").fill("Explain fixed shares");
    await page.locator(".ask-submit").click();
    await expect(page.locator(".ask-feedback[role=alert]")).toContainText(
      message,
    );
    await page.getByRole("button", { name: "Retry", exact: true }).click();
    await expect(page.locator(".ask-answer")).toContainText(
      "A grounded explanation.",
    );
    expect(count).toBe(2);
  });
}

test("proxy rejects invalid JSON", async ({ request }) => {
  const response = await request.post("/api/ask", {
    data: Buffer.from("{broken"),
    headers: { "Content-Type": "application/json" },
  });
  expect(response.status()).toBe(400);
  expect((await response.json()).error.code).toBe("invalid_request");
});

test("server proxy forwards payload and preserves backend errors", async ({
  request,
}) => {
  const response = await request.post("/api/ask", {
    data: { mode: "case", question: "neutral fixture" },
  });
  expect(response.status()).toBe(200);
  expect(await response.json()).toMatchObject({
    mode: "case",
    answer: "neutral fixture",
  });
  const error = await request.post("/api/ask", {
    data: { mode: "learn", question: "fixture-error" },
  });
  expect(error.status()).toBe(422);
  expect(await error.json()).toEqual({ detail: "Fixture validation error" });
});

test("grounded presentation hides IDs, deduplicates and labels Arabic operational limitations", async ({
  page,
}) => {
  const source = {
    source_name: "Fixture source",
    section: "Fixture entry",
    publisher: "Fixture institution",
    reference: { volume: 3, page: 7 },
    source_url: "https://example.org/fixture",
  };
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        mode: "learn",
        language: "ar",
        decision_state: "ready",
        answer: "Neutral explanation [E1].",
        key_concepts: [
          { term: "Duplicate", explanation: "Neutral explanation [E2]." },
        ],
        source_excerpts: [
          {
            ...source,
            text: "Exact neutral excerpt.\n  Original whitespace.",
            provenance: source,
          },
          { ...source, text: "Exact neutral excerpt.\n  Original whitespace." },
        ],
        sources: [source, source],
        limitations: ["No matching approved fiqh evidence is available."],
      },
    }),
  );
  await page.goto("/");
  await page.getByRole("textbox").fill("سؤال تعليمي للاختبار");
  await page.locator(".ask-submit").click();
  const result = page.locator(".ask-result");
  await expect(result).toContainText("Neutral explanation.");
  await expect(result).not.toContainText(/\bE[12]\b/);
  await expect(result).not.toContainText("Duplicate");
  await expect(result.locator(".ask-source")).toHaveCount(1);
  await expect(result.locator(".ask-excerpts figure")).toHaveCount(1);
  expect(await result.locator("blockquote").textContent()).toBe(
    "Exact neutral excerpt.\n  Original whitespace.",
  );
  await expect(result).toContainText(
    "لا تتوفر أدلة فقهية معتمدة مطابقة للسؤال.",
  );
  await expect(result.locator(".ask-source dt")).toHaveText([
    "المصدر",
    "المدخل / الموضوع",
    "الناشر / المؤسسة",
    "المرجع",
    "الرابط",
  ]);
  await expect(result.locator(".ask-source dd")).toHaveText([
    "Fixture source",
    "Fixture entry",
    "Fixture institution",
    "الجزء 3 / الصفحة 7",
    "https://example.org/fixture",
  ]);
});
