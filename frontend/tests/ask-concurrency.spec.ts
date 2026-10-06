import { test, expect } from "@playwright/test";

for (const [start, target] of [
  ["/concepts/awl", "/concepts/radd"],
  ["/concepts/awl", "/learn/paths/shares-rules"],
  ["/", "/concepts/awl"],
]) {
  test(`pending ${start} does not block ${target}`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    let count = 0;
    let release!: () => void;
    const held = new Promise<void>((resolve) => {
      release = resolve;
    });
    await page.route("**/api/ask", async (route) => {
      count++;
      if (count === 1) await held;
      await route
        .fulfill({
          json: {
            mode: "learn",
            language: "ar",
            decision_state: "ready",
            answer: count === 1 ? "old answer" : "new answer",
            sources: [],
            source_excerpts: [],
            limitations: [],
          },
        })
        .catch(() => {});
    });
    await page.goto(start);
    const input =
      start === "/"
        ? page.locator(".ask-panel textarea")
        : page.locator("#concept-question");
    await input.fill("ما معنى العول؟");
    await input.press("Enter");
    await expect.poll(() => count).toBe(1);
    // Client navigation exercises unmount, unlike a full page reload.
    // Use an existing Next Link when possible; homepage links remain available.
    if (start !== "/") await page.locator(".curriculum-back").click();
    const destination = target.includes("/learn/")
      ? page.locator(`.path-toggle[href="${target}"]`)
      : page.locator(`.concept-card[href="${target}"]`);
    await destination.click();
    await page.locator("#concept-question").fill("ما معنى الرد؟");
    await page.locator(".concept-tutor form").evaluate((form) => {
      form.dispatchEvent(
        new Event("submit", { bubbles: true, cancelable: true }),
      );
      form.dispatchEvent(
        new Event("submit", { bubbles: true, cancelable: true }),
      );
    });
    await expect.poll(() => count).toBe(2);
    await expect(page.locator(".ask-result")).toContainText("new answer");
    release();
    await expect(page.locator(".ask-result")).not.toContainText("old answer");
    expect(count).toBe(2);
    expect(errors).toEqual([]);
  });
}

test("busy response retains the existing answer and permits retry", async ({
  page,
}) => {
  let count = 0;
  await page.route("**/api/ask", (route) =>
    ++count === 2
      ? route.fulfill({ status: 429, json: { error: { code: "busy" } } })
      : route.fulfill({
          json: {
            mode: "learn",
            language: "ar",
            decision_state: "ready",
            answer: "existing answer",
            sources: [],
            source_excerpts: [],
          },
        }),
  );
  await page.goto("/concepts/awl");
  await page.locator("#concept-question").fill("سؤال");
  await page.locator(".concept-tutor > form button").click();
  await expect(page.locator(".ask-result")).toContainText("existing answer");
  await page.locator(".concept-tutor > form button").click();
  await expect(page.locator(".ask-error")).toContainText(
    "MAWARITH يعالج عدة أسئلة الآن",
  );
  await expect(page.locator(".ask-result")).toContainText("existing answer");
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.locator(".ask-error")).toHaveCount(0);
});
