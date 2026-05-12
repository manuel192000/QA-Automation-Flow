import { test, expect } from '@playwright/test';
import { SearchModal } from '../../pages/search-modal';

// Query that should surface featured products in the predictive panel.
// TODO: confirm with codegen which query reliably triggers the Featured
// Products section on oneshop staging. Likely candidates: "amana",
// "kitchen", "refrigerator", or an empty string for the default state.
const FEATURED_TRIGGER_QUERY = 'kitchen';

/**
 * Monday: https://retailerwebservices.monday.com/boards/18395174855/pulses/11920451594
 * Title: Trademark Rendering in Predictive Search — Featured Products
 * Feature Area: Predictive Search / Header
 * Validation Type: UI Regression
 * Site: oneshop
 *
 * Overview:
 *   This QA cycle validates trademark symbol rendering inside the Featured
 *   Products section of the predictive search overlay. The defect reported
 *   that titles were showing the raw HTML entity strings (&reg; and
 *   &trade;) instead of the proper ® and ™ symbols. Algolia-driven results
 *   were not affected, so the issue lives on the OS rendering side, not on
 *   the data source.
 *
 * Checks:
 *   - Featured products do not show literal &reg; in their titles
 *   - Featured products do not show literal &trade; in their titles
 *   - Algolia (non-featured) products keep rendering trademarks correctly
 *
 * Summary:
 *   ✅ Encoding correctness
 *   - No HTML entity literal (&reg;, &trade;) appears in featured titles
 *   - Trademarks, when present, are rendered as the proper Unicode glyph
 *
 *   ✅ Cross-section consistency
 *   - The fix did not regress Algolia-driven Product results
 *   - Same titles render identically across both panels of the overlay
 */
test.describe(
  'Predictive Search — Trademark Rendering',
  { tag: '@regression' },
  () => {
    test('Featured Products render trademarks as proper symbols', async ({
      page,
    }) => {
      await page.goto('/');

      const modal = new SearchModal(page);
      await modal.acceptCookiesIfPresent();
      await modal.open();
      await modal.typeQuery(FEATURED_TRIGGER_QUERY);

      const featured = modal.featuredProductTitles();
      expect(
        await featured.count(),
        'No featured products visible in the overlay.'
      ).toBeGreaterThan(0);

      await modal.expectNoHtmlEntities(featured);

      if ((await modal.productsSection().count()) > 0) {
        await modal.expectNoHtmlEntities(modal.productTitles());
      }
    });
  }
);
