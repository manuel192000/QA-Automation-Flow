import { test, expect } from '@playwright/test';
import { HomePage } from '../../pages/home-page';

/**
 * Monday: N/A (infrastructure smoke)
 * Title: oneshop home loads
 * Feature Area: Home
 * Validation Type: Smoke
 *
 * Overview:
 *   Sanity check that the home page loads on the configured BASE_URL and
 *   that no JavaScript errors are emitted during the first paint.
 *
 * Checks:
 *   - The home page loads and the URL belongs to oneshop
 *   - No `pageerror` events are captured during load
 */
test.describe('Homepage smoke', { tag: '@smoke' }, () => {
  test('homepage loads on a valid URL', async ({ page }) => {
    const home = new HomePage(page);
    await home.navigate();
    await home.expectLoaded();
  });

  test('homepage has no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));

    const home = new HomePage(page);
    await home.navigate();
    await home.expectLoaded();

    expect(errors, `Console errors detected: ${errors.join('\n')}`).toEqual([]);
  });
});
