import path from 'path'
import { fileURLToPath } from 'url'
import { defineConfig, devices } from '@playwright/test'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// require('dotenv').config();

/**
 * See https://playwright.dev/docs/test-configuration.
 * E2E_AUTOMATION=1 (see scripts/e2e-automation.sh): serial workers, no parallel specs — safe for DB-reset flows.
 */
const e2eAutomation = process.env.E2E_AUTOMATION === '1'
/** When E2E_AUTOMATION=1, avoid clashing with a dev server on 8848 (see scripts/e2e-automation.sh). */
const e2eFrontendOrigin =
  e2eAutomation
    ? `http://localhost:${process.env.E2E_VITE_PORT ?? process.env.VITE_PORT ?? '8858'}`
    : process.env.BASE_URL || 'http://localhost:8848'

export default defineConfig({
  testDir: './tests/e2e',
  
  /* Run tests in files in parallel */
  fullyParallel: !e2eAutomation,
  
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Opt out of parallel tests on CI or full-stack automation. */
  workers: (e2eAutomation || !!process.env.CI) ? 1 : undefined,
  
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html'],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL for `page`. Automation uses E2E_VITE_PORT (default 8858) so :8848 can stay free for manual dev. */
    baseURL: e2eFrontendOrigin,

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Video on failure */
    video: 'retain-on-failure',
    
    /* Browser context settings */
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
  },
  
  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    
    /* Test against mobile viewports. */
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
    
    /* Test against branded browsers. */
    // {
    //   name: 'Microsoft Edge',
    //   use: { channel: 'msedge' },
    // },
    // {
    //   name: 'Google Chrome',
    //   use: { channel: 'chrome' },
    // },
  ],
  
  /* Run your local dev server before starting the tests */
  webServer: {
    command: e2eAutomation
      ? `VITE_API_URL=${process.env.VITE_API_URL ?? process.env.E2E_API_URL ?? 'http://127.0.0.1:8010'} VITE_PORT=${process.env.E2E_VITE_PORT ?? process.env.VITE_PORT ?? '8858'} pnpm run dev`
      : 'pnpm run dev',
    url: e2eAutomation ? e2eFrontendOrigin : 'http://localhost:8848',
    // Automation always spawns its own Vite with matching API URL; dev reuse only for ad-hoc runs.
    reuseExistingServer: !e2eAutomation,
    timeout: 120 * 1000,
  },
  
  /* Global setup and teardown */
  globalSetup: path.join(__dirname, 'tests/e2e/global-setup.ts'),
  globalTeardown: path.join(__dirname, 'tests/e2e/global-teardown.ts'),
  
  /* Test timeout */
  timeout: 30 * 1000,
  
  /* Expect timeout */
  expect: {
    timeout: 5 * 1000,
  },
});
