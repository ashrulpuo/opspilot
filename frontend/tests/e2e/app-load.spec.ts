import { test, expect } from '@playwright/test'

/**
 * Guards against a blank white screen at hash-mode root (e.g. http://localhost:8848/#/).
 */
test.describe('App bootstrap', () => {
  test('hash root renders public auth shell (login or initial setup)', async ({ page }) => {
    await page.goto('/#/')
    await expect(page.locator('#app')).toBeVisible()
    const loginBox = page.locator('.login-box')
    const setupBox = page.locator('.setup-box')
    await expect(loginBox.or(setupBox)).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('heading', { name: 'OpsPilot' })).toBeVisible()
    await expect(
      page.getByRole('heading', { name: 'Welcome back' }).or(page.getByRole('heading', { name: 'Initial setup' })),
    ).toBeVisible()
  })
})
