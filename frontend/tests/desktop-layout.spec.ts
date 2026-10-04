import { test, expect } from "@playwright/test";

test("bounded desktop layout and reduced-zoom effective viewports", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Desktop layout checks");
  const sizes = [
    [1366, 768],
    [1440, 900],
    [1920, 1080],
    [2560, 1440],
    [3200, 1800],
    [3840, 2160],
  ];
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  for (const [screenWidth, screenHeight] of sizes) {
    // Browser zoom-out increases the CSS viewport. This exercises that layout
    // behavior without misusing CSS zoom or mobile pinch-zoom as browser zoom.
    for (const zoom of [1, 0.8, 0.67, 0.5, 0.25]) {
      const width = Math.round(screenWidth / zoom);
      await page.setViewportSize({
        width,
        height: Math.round(screenHeight / zoom),
      });
      const metrics = await page.evaluate(() => {
        const box = (selector: string) =>
          document.querySelector(selector)!.getBoundingClientRect();
        return {
          overflow: document.documentElement.scrollWidth > innerWidth,
          centers: [".hero h1", ".hero h2", ".ask-panel", ".mode-selector"].map(
            (s) => {
              const b = box(s);
              return b.x + b.width / 2;
            },
          ),
          panel: box(".ask-panel").width,
          modes: box(".mode-selector").width,
          section: box(".concepts-section .container").width,
          hero: box(".hero").height,
          inputSize: parseFloat(
            getComputedStyle(document.querySelector("#question")!).fontSize,
          ),
        };
      });
      expect(metrics.overflow).toBe(false);
      for (const center of metrics.centers)
        expect(Math.abs(center - width / 2)).toBeLessThan(0.1);
      expect(metrics.panel).toBeCloseTo(metrics.modes, 1);
      expect(metrics.panel).toBeLessThanOrEqual(width < 2200 ? 1064 : 2432);
      expect(metrics.section).toBeLessThanOrEqual(width < 2200 ? 1640 : 3600);
      expect(metrics.hero).toBeLessThan(width < 2200 ? 850 : 1900);
      expect(metrics.inputSize).toBeGreaterThanOrEqual(16);
      if (width >= 3840) {
        expect(metrics.panel).toBeGreaterThan(2000);
        expect(metrics.section).toBeGreaterThan(2800);
        expect(metrics.inputSize).toBeGreaterThan(40);
      }
      if (zoom === 1 || screenWidth === 1440) {
        await page.screenshot({
          path: `test-results/layout-${screenWidth}-${Math.round(zoom * 100)}.png`,
          fullPage: true,
        });
      }
    }
  }
});
