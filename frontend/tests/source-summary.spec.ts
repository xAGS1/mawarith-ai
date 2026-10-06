import { test, expect } from "@playwright/test";
import { uniqueSummaryReferences } from "../src/lib/ask/presentation";

test("summary identity is source name plus reference, independent of rule and URL", () => {
  expect(
    uniqueSummaryReferences([
      {
        source_name: "Quran",
        reference: "4:11",
        source_url: "https://example.org/a",
      },
      { source: { source_name: "Quran", reference: "4:11" }, rule: "Rule one" },
      { source_name: "Quran", reference: "4:12" },
      { source_name: "Encyclopedia", reference: { volume: 3, page: 7 } },
      {
        provenance: { source_name: "Encyclopedia", volume: 3, page: 8 },
        rule: "Rule two",
      },
    ]),
  ).toHaveLength(3);
});

test("three summary references retain every excerpt and applied rule", async ({
  page,
}) => {
  const quran11 = {
    source_name: "القرآن الكريم",
    reference: "4:11",
    source_url: "https://example.org/11",
  };
  const quran12 = {
    source_name: "القرآن الكريم",
    reference: "4:12",
    source_url: "https://example.org/12",
  };
  const fiqh = {
    source_name: "الموسوعة الفقهية الكويتية",
    volume: 3,
    publisher: "Fixture publisher",
    section: "Fixture section",
    source_url: "https://example.org/fiqh",
  };
  const sources = [quran11, quran11, quran12, quran12, fiqh].map(
    (source, i) => ({
      source: { ...source, source_url: `${source.source_url}?rule=${i}` },
      rule_id: `fixture-${i}`,
      rule: `Distinct applied rule ${i}`,
    }),
  );
  const excerpts = [quran11, quran12, fiqh].map((source, i) => ({
    ...source,
    text: `Exact excerpt ${i}`,
  }));
  await page.route("**/api/ask", (route) =>
    route.fulfill({
      json: {
        mode: "case",
        language: "ar",
        decision_state: "ready",
        answer: "Fixture explanation.",
        sources,
        source_excerpts: excerpts,
        limitations: [],
        key_concepts: [],
      },
    }),
  );
  await page.goto("/");
  await page.locator("#question").fill("مات وترك زوجة وأم وابنين وبنت");
  await page.locator(".ask-submit").click();
  const result = page.locator(".ask-result");
  await expect(result.locator(".tutor-source-chips h4")).toHaveText(
    "المراجع المستخدمة · 3",
  );
  await expect(result.locator(".tutor-source-chips button")).toHaveText([
    "القرآن الكريم · 4:11",
    "القرآن الكريم · 4:12",
    "الموسوعة الفقهية الكويتية · الجزء 3",
  ]);
  await result
    .getByRole("button", { name: "عرض التفاصيل", exact: true })
    .click();
  await expect(
    result.getByRole("heading", { name: "مقتطفات المصادر", exact: true }),
  ).toBeVisible();
  await expect(
    result.getByRole("heading", {
      name: "القواعد المطبقة ومراجعها",
      exact: true,
    }),
  ).toBeVisible();
  await expect(result.locator(".ask-source")).toHaveCount(8);
  await expect(
    result.getByRole("button", { name: "عرض ملخص القاعدة", exact: true }),
  ).toHaveCount(5);
  for (const button of await result
    .locator(".source-text-disclosure > button")
    .all())
    await button.click();
  await expect(result.locator("blockquote")).toHaveText(
    excerpts.map((source) => source.text),
  );
  for (const button of await result
    .getByRole("button", { name: "عرض ملخص القاعدة", exact: true })
    .all())
    await button.click();
  for (let i = 0; i < sources.length; i++) {
    await expect(
      result.getByText(`Distinct applied rule ${i}`, { exact: true }),
    ).toBeVisible();
    await expect(
      result.locator(`a[href="${sources[i].source.source_url}"]`),
    ).toBeVisible();
  }
});
