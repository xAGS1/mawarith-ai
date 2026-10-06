import { test, expect } from "@playwright/test";

const arabic = "لم أفهم المقصود من سؤالك. هل يمكنك توضيحه أكثر؟";
const english =
  "I couldn't determine the intended meaning. Could you clarify your question?";

for (const scenario of [
  {
    name: "Arabic duplicate",
    question: "خلا",
    language: "ar",
    clarification: arabic,
    answer: arabic,
  },
  {
    name: "Arabic empty explanation",
    question: "لفظ غامض",
    language: "ar",
    clarification: arabic,
    answer: "",
  },
  {
    name: "English duplicate",
    question: "unclear",
    language: "en",
    clarification: english,
    answer: english,
  },
  {
    name: "substantially duplicate",
    question: "لفظ غامض",
    language: "ar",
    clarification: arabic,
    answer: `توضيح: ${arabic}`,
  },
  {
    name: "English fragment isolated in Arabic card",
    question: "سؤال غامض",
    language: "ar",
    clarification: "Could you clarify the term?",
    answer: "",
  },
]) {
  test(scenario.name, async ({ page }) => {
    await page.route("**/api/ask", (route) =>
      route.fulfill({
        json: {
          mode: "learn",
          language: scenario.language,
          decision_state: "needs_clarification",
          answer: scenario.answer,
          clarification_question: scenario.clarification,
          sources: [],
          source_excerpts: [],
          key_concepts: [],
          limitations: [],
        },
      }),
    );
    await page.goto("/");
    await page.locator("#question").fill(scenario.question);
    await page.locator(".ask-submit").click();
    await expect(page.locator(".ask-clarification p")).toHaveText(
      scenario.clarification,
    );
    await expect(page.locator(".ask-clarification p")).toHaveAttribute(
      "dir",
      "auto",
    );
    await expect(page.locator(".ask-result")).toHaveAttribute(
      "dir",
      scenario.language === "ar" ? "rtl" : "ltr",
    );
    await expect(page.locator(".ask-answer")).toHaveCount(0);
    await expect(
      page.getByRole("heading", { name: "الشرح التعليمي", exact: true }),
    ).toHaveCount(0);
    if (scenario.name.includes("fragment")) {
      expect(
        await page
          .locator(".ask-clarification p")
          .evaluate((el) => getComputedStyle(el).direction),
      ).toBe("ltr");
    }
  });
}

test("distinct clarification context is retained and ready answer unchanged", async ({
  page,
}) => {
  let ready = false;
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        mode: "learn",
        language: "ar",
        decision_state: ready ? "ready" : "needs_clarification",
        evidence_status: ready ? "supported" : "insufficient",
        answer: "نحتاج إلى معرفة المصطلح الذي تريد شرحه.",
        clarification_question: ready ? null : "هل يمكنك تحديد المقصود؟",
        sources: [],
        source_excerpts: [],
        key_concepts: [],
        limitations: [],
      },
    }),
  );
  await page.goto("/");
  await page.locator("#question").fill("سؤال غامض");
  await page.locator(".ask-submit").click();
  await expect(page.locator(".ask-answer")).toContainText(
    "نحتاج إلى معرفة المصطلح",
  );
  ready = true;
  await page.locator("#question").fill("اشرح المصطلح");
  await page.locator(".ask-submit").click();
  await expect(page.locator(".ask-clarification")).toHaveCount(0);
  await expect(page.locator(".ask-answer")).toContainText(
    "نحتاج إلى معرفة المصطلح",
  );
});
