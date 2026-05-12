import { test, expect } from '@playwright/test';
import { SearchModal } from '../../pages/search-modal';

/**
 * Monday: https://retailerwebservices.monday.com/boards/18395174855/pulses/11916681731
 * Title: Predictive Search — Featured Brands as Pills
 * Feature Area: Predictive Search / Header
 * Validation Type: UI Regression
 * Site: oneshop
 *
 * Overview:
 *   This QA cycle validates the visual treatment of featured brands in the
 *   predictive search panel of the header. Previously, brand suggestions
 *   were rendered as logos. The product decision was to align them with the
 *   existing pill pattern used by recent searches — text inside a rounded
 *   button, no logo image. The goal is to confirm that the new design
 *   renders correctly and that brands still appear under the "Brands"
 *   section of the panel after typing a brand query.
 *
 * Checks:
 *   - AMANA brand appears in the predictive search results
 *   - AMANA brand is rendered inside the "Brands" section of the panel
 *   - AMANA brand is rendered as a pill (rounded border-radius), not a logo
 *
 * Summary:
 *   ✅ Visual rendering
 *   - Brand appears as a rounded text pill, matching the recent-searches pattern
 *   - No logo image is rendered for the brand entry
 *
 *   ✅ Section placement
 *   - The brand item is contained within the "Brands" section of the panel
 *   - The "Brands" label remains visible above its items
 *
 *   ✅ Search behavior
 *   - Typing a brand term surfaces the matching brand in the panel
 *   - The result is reachable as a clickable button (role=button)
 */
test.describe('Predictive Search — Featured Brands as Pills', { tag: '@regression' }, () => {
  test('AMANA appears as a pill inside the Brands section', async ({ page }) => {
    await page.goto('/');

    const modal = new SearchModal(page);
    await modal.acceptCookiesIfPresent();
    await modal.open();
    await modal.typeQuery('amana');

    // 1) The AMANA pill must be visible
    const amana = modal.brandPill('AMANA');
    await expect(amana).toBeVisible();

    // 2) It must live inside the "Brands" section
    await expect(modal.brandsSection()).toBeVisible();
    await expect(
      modal.brandsSection().getByRole('button', { name: 'AMANA', exact: true })
    ).toBeVisible();

    // 3) And be rendered as a pill (rounded border-radius)
    await modal.expectRenderedAsPill(amana);
  });
});
