import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: process.env.KLOWB_WEB_URL ?? "http://127.0.0.1:3000",
    launchOptions: { executablePath: process.env.KLOWB_DIAGNOSTIC_CHROMIUM },
  },
});
