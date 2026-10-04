import { test, expect } from "@playwright/test";
import { PENDING_REQUEST_KEY } from "../src/lib/ask/pending-request";

const response = {
  mode: "learn",
  language: "en",
  decision_state: "ready",
  answer: "Neutral completed fixture",
  source_excerpts: [],
};
const marker = (page: import("@playwright/test").Page) =>
  page.evaluate((key) => sessionStorage.getItem(key), PENDING_REQUEST_KEY);

test("refresh during pending restores question and blocks duplicate submissions", async ({
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
    await route.fulfill({ json: response }).catch(() => {});
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Switch to English" }).click();
  await page.getByRole("textbox").fill("What is a fixed share?");
  await page.locator(".ask-submit").click();
  await expect.poll(() => calls).toBe(1);
  const stored = JSON.parse((await marker(page))!);
  expect(stored).toMatchObject({
    status: "pending",
    mode: "learn",
    question: "What is a fixed share?",
  });
  expect(typeof stored.startedAt).toBe("number");
  // Exercise the form handler directly as well as keyboard repeat, bypassing disabled controls.
  await page.locator(".ask-panel").evaluate((form) => {
    for (let i = 0; i < 3; i++)
      form.dispatchEvent(
        new Event("submit", { bubbles: true, cancelable: true }),
      );
  });
  await page.keyboard.press("Enter");
  expect(calls).toBe(1);
  await page.reload();
  await expect(page.getByRole("textbox")).toHaveValue(stored.question);
  await expect(page.locator(".ask-feedback")).toContainText(
    "Your request is still being processed",
  );
  await expect(page.locator(".ask-feedback")).toContainText(
    "Please wait before submitting another question.",
  );
  await expect(page.locator(".ask-submit")).toBeDisabled();
  await page
    .locator(".ask-panel")
    .evaluate((form) =>
      form.dispatchEvent(
        new Event("submit", { bubbles: true, cancelable: true }),
      ),
    );
  expect(calls).toBe(1);
  release();
  await page.getByRole("button", { name: "التبديل إلى العربية" }).click();
  await expect(page.locator(".ask-feedback")).toContainText(
    "طلبك ما زال تحت المعالجة",
  );
  await expect(page.locator(".ask-feedback")).toContainText(
    "يرجى الانتظار قبل إرسال سؤال جديد.",
  );
  expect(await marker(page)).not.toBeNull();
});

test("stale pending marker restores question but permits retry", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator(".ask-submit")).toBeEnabled();
  await page.evaluate(
    (key) =>
      sessionStorage.setItem(
        key,
        JSON.stringify({
          status: "pending",
          question: "Neutral old question",
          mode: "learn",
          startedAt: Date.now() - 180_001,
        }),
      ),
    PENDING_REQUEST_KEY,
  );
  await page.reload();
  await expect(page.getByRole("textbox")).toHaveValue("Neutral old question");
  await expect(page.locator(".ask-submit")).toBeEnabled();
  await expect(page.locator(".ask-feedback")).toContainText(
    "قد تكون مهلة الطلب السابق قد انتهت",
  );
  expect(await marker(page)).toBeNull();
});

test("restored pending automatically becomes stale at three minutes", async ({
  page,
}) => {
  await page.clock.install();
  await page.goto("/");
  await expect(page.locator(".ask-submit")).toBeEnabled();
  await page.evaluate(
    (key) =>
      sessionStorage.setItem(
        key,
        JSON.stringify({
          status: "pending",
          question: "Neutral question",
          mode: "case",
          startedAt: Date.now() - 179_000,
        }),
      ),
    PENDING_REQUEST_KEY,
  );
  await page.reload();
  await expect(page.locator(".ask-submit")).toBeDisabled();
  await page.clock.fastForward(1001);
  await expect(page.locator(".ask-submit")).toBeEnabled();
  expect(await marker(page)).toBeNull();
});

for (const successful of [true, false]) {
  test(`${successful ? "successful" : "failed"} request clears pending storage`, async ({
    page,
  }) => {
    let release!: () => void;
    const held = new Promise<void>((resolve) => {
      release = resolve;
    });
    await page.route("**/api/ask", async (route) => {
      await held;
      await route.fulfill(
        successful
          ? { json: response }
          : { status: 503, json: { error: { code: "backend_unavailable" } } },
      );
    });
    await page.goto("/");
    await page.getByRole("textbox").fill("Neutral question");
    await page.locator(".ask-submit").click();
    await expect.poll(() => marker(page)).not.toBeNull();
    release();
    await expect(page.locator(".ask-submit")).toBeEnabled();
    expect(await marker(page)).toBeNull();
    if (successful)
      await expect(page.locator(".ask-answer")).toContainText(response.answer);
    else await expect(page.locator(".ask-feedback[role=alert]")).toBeVisible();
  });
}
