import { defineConfig, devices } from "@playwright/test";
const dev = process.env.PLAYWRIGHT_DEV === "1";
const port = dev ? 3000 : 3100;
const serverUrl = `http://${dev ? "localhost" : "127.0.0.1"}:${port}`;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: serverUrl,
    channel:
      process.env.PLAYWRIGHT_CHANNEL ||
      (process.platform === "win32" ? "msedge" : undefined),
  },
  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command: "node tests/fixtures/ask-backend.cjs",
      url: "http://127.0.0.1:3101",
      reuseExistingServer: false,
    },
    {
      command: `npm run ${dev ? "dev" : "start"} -- --port ${port}`,
      url: serverUrl,
      reuseExistingServer: !process.env.CI,
      env: { BACKEND_API_URL: "http://127.0.0.1:3101" },
    },
  ],
});
