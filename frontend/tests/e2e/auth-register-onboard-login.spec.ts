import { test, expect } from '@playwright/test'

/**
 * Playwright E2E: initial setup wizard (first admin), register policy, login.
 *
 * - Uses `request` against `E2E_API_URL` and `page` against the Vite `baseURL` (hash router).
 * - Fresh-install path: empty `users` → app redirects to `/#/setup` → Complete setup → Dashboard.
 * - `/#/register` is configured to redirect to `/#/login` (no self-serve register UI); we still
 *   assert `POST /auth/register` via API (403 when disabled, 201 when enabled).
 * - After clearing `localStorage`, call `reload()` so Pinia auth state resets (hash-only `goto`
 *   does not remount the SPA).
 *
 * Full stack: `./scripts/e2e-automation.sh` (truncates users, workers=1).
 */
const API_BASE = (process.env.E2E_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const API_V1 = `${API_BASE}/api/v1`

const setupPassword = 'E2E_Auth#2026_Secure'

/** Match playwright.config.ts / e2e-automation.sh so extra contexts use the same origin as `page`. */
function frontendBaseURL(): string {
  const e2eAutomation = process.env.E2E_AUTOMATION === '1'
  if (e2eAutomation) {
    return `http://localhost:${process.env.E2E_VITE_PORT ?? process.env.VITE_PORT ?? '8858'}`
  }
  return process.env.BASE_URL || 'http://localhost:8848'
}

/** Set when the browser initial-setup test completes (serial suite). */
let wizardAdminEmail: string | null = null

test.describe.configure({ mode: 'serial' })

test.describe('Register, onboarding (initial setup), login', () => {
  test('initial setup wizard in browser then sign in again reaches dashboard', async ({ page, request }) => {
    let needsSetup = false
    try {
      const setupRes = await request.get(`${API_V1}/auth/setup-required`, { timeout: 15_000 })
      if (!setupRes.ok()) {
        test.skip(
          true,
          `Backend not healthy at ${API_BASE} (HTTP ${setupRes.status()}). Start the API; set E2E_API_URL to match VITE_API_URL.`,
        )
        return
      }
      const body = (await setupRes.json()) as { setup_required?: boolean }
      needsSetup = body.setup_required === true
    } catch {
      test.skip(true, `Backend not reachable at ${API_BASE}. Start the API server.`)
      return
    }

    test.skip(
      !needsSetup,
      `Requires empty users: GET ${API_V1}/auth/setup-required must return setup_required: true.`,
    )

    const email = `e2e.setup.${Date.now()}@example.com`
    const fullName = 'E2E Setup Admin'

    await page.goto('/#/')
    await expect(page.getByRole('heading', { name: 'Initial setup' })).toBeVisible({ timeout: 20_000 })

    // Substring match would also hit the org field placeholder ("… your name plus …").
    await page.getByPlaceholder('Your name', { exact: true }).fill(fullName)
    await page.getByPlaceholder('admin@example.com').fill(email)
    await page.getByPlaceholder('At least 8 characters', { exact: true }).fill(setupPassword)
    await page.getByPlaceholder('Repeat password', { exact: true }).fill(setupPassword)

    await page.getByRole('button', { name: 'Complete setup' }).click()

    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 30_000 })

    wizardAdminEmail = email

    await page.evaluate(() => localStorage.removeItem('opspilot-auth'))
    await page.reload({ waitUntil: 'domcontentloaded' })
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible({ timeout: 20_000 })
    await page.getByPlaceholder('Email address').fill(email)
    await page.getByPlaceholder('Password').fill(setupPassword)
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 25_000 })
  })

  test('register route redirects to login; API register matches server policy', async ({ browser, request }) => {
    let needsSetup = false
    try {
      const setupRes = await request.get(`${API_V1}/auth/setup-required`, { timeout: 15_000 })
      if (!setupRes.ok()) {
        test.skip(true, `Backend not healthy (HTTP ${setupRes.status()}).`)
        return
      }
      const body = (await setupRes.json()) as { setup_required?: boolean }
      needsSetup = body.setup_required === true
    } catch {
      test.skip(true, 'Backend not reachable.')
      return
    }

    test.skip(needsSetup, 'Requires an existing installation (setup wizard finished).')

    const base = frontendBaseURL()
    const ctx = await browser.newContext({ baseURL: base })
    const page = await ctx.newPage()
    try {
      await page.goto('/#/register')
      await expect(page).toHaveURL(/#\/login/)
      await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible({ timeout: 15_000 })
    } finally {
      await ctx.close()
    }

    const email = `e2e.reg.${Date.now()}@example.com`
    const reg = await request.post(`${API_V1}/auth/register`, {
      data: {
        email,
        password: setupPassword,
        confirm_password: setupPassword,
        full_name: 'E2E API Register',
      },
    })

    if (reg.status() === 403) {
      const text = await reg.text()
      expect(text.toLowerCase()).toContain('disabled')
      return
    }

    if (reg.status() === 201) {
      expect(reg.ok()).toBeTruthy()
      return
    }

    throw new Error(`Unexpected POST /auth/register status: ${reg.status()} ${await reg.text()}`)
  })

  test('login rejects wrong password for known user', async ({ browser, request }) => {
    let needsSetup = false
    try {
      const setupRes = await request.get(`${API_V1}/auth/setup-required`, { timeout: 15_000 })
      if (setupRes.ok()) {
        const body = (await setupRes.json()) as { setup_required?: boolean }
        needsSetup = body.setup_required === true
      }
    } catch {
      test.skip(true, 'Backend not reachable.')
      return
    }

    test.skip(needsSetup, 'Requires setup to be complete.')

    const email = wizardAdminEmail || process.env.E2E_LOGIN_EMAIL || ''
    test.skip(!email, 'No user email: run the initial-setup test first or set E2E_LOGIN_EMAIL.')

    const base = frontendBaseURL()
    const ctx = await browser.newContext({ baseURL: base })
    const page = await ctx.newPage()
    try {
      await page.goto('/#/login')
      await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible({ timeout: 20_000 })

      await page.getByPlaceholder('Email address').fill(email)

      const [loginResp] = await Promise.all([
        page.waitForResponse(
          (r) => r.url().includes('/auth/login') && r.request().method() === 'POST',
          { timeout: 20_000 },
        ),
        (async () => {
          await page.getByPlaceholder('Password').fill('DefinitelyWrongPassword!99')
          await page.getByRole('button', { name: 'Sign in' }).click()
        })(),
      ])

      expect(loginResp.status()).toBe(401)
      await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible({
        timeout: 15_000,
      })
      await expect(page.getByRole('heading', { name: 'Dashboard' })).not.toBeVisible()
    } finally {
      await ctx.close()
    }
  })
})
