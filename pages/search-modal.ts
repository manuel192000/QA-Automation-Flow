import { Locator, Page, expect } from '@playwright/test';

/**
 * Page Object for the predictive search panel that opens from the header.
 *
 * Confirmed selectors (May 2026):
 *   - Trigger / input: data-testid="search-split-panel_input"
 *   - Brand pills:     <button> with accessible name in uppercase ("AMANA")
 *
 * Other selectors use `.or_()` fallbacks until confirmed with codegen.
 */
export class SearchModal {
  constructor(private readonly page: Page) {}

  // -------------------------- cookie banner (one-shot) ---------------------

  /** Dismiss the cookie consent banner if it is visible. Idempotent. */
  async acceptCookiesIfPresent(timeoutMs = 2000): Promise<this> {
    try {
      const btn = this.page.getByRole('button', { name: /accept all/i });
      await btn.waitFor({ state: 'visible', timeout: timeoutMs });
      await btn.click();
    } catch {
      /* banner not present — fine */
    }
    return this;
  }

  // -------------------------- input + open --------------------------------

  /** Search input in the header. Clicking it also opens the predictive panel. */
  get searchInput(): Locator {
    return this.page.getByTestId('search-split-panel_input');
  }

  /** Focus the search input to open the panel. */
  async open(): Promise<this> {
    await this.searchInput.click();
    return this;
  }

  /** Type a query; Playwright auto-waits for the debounce. */
  async typeQuery(query: string): Promise<this> {
    await this.searchInput.fill(query);
    return this;
  }

  // -------------------------- brands section ------------------------------

  /** A brand pill ("AMANA", "AMANA CANADA", ...) anywhere on the page. */
  brandPill(brandName: string): Locator {
    return this.page.getByRole('button', {
      name: brandName.toUpperCase(),
      exact: true,
    });
  }

  /**
   * Container of the "Brands" section. Confirmed by screenshot that the
   * "BRANDS" label is NOT a semantic heading, so we locate it by text.
   */
  brandsSection(): Locator {
    const label = this.page.getByText(/^\s*brands\s*$/i);
    return this.page
      .getByTestId('search-split-panel_brands')
      .or(this.page.locator('section, aside, div').filter({ has: label }))
      .first();
  }

  // -------------------------- featured products section --------------------

  /** Container of the "Featured Products" section. TODO: confirm testId via codegen. */
  featuredProductsSection(): Locator {
    const label = this.page.getByText(/^\s*featured products\s*$/i);
    return this.page
      .getByTestId('search-split-panel_featured-products')
      .or(this.page.locator('section, aside, div').filter({ has: label }))
      .first();
  }

  featuredProductTitles(): Locator {
    return this.featuredProductsSection().locator(
      'a, h3, [data-testid*="title" i]'
    );
  }

  // -------------------------- generic products section ---------------------

  productsSection(): Locator {
    const label = this.page.getByText(/^\s*products\s*$/i);
    return this.page
      .getByTestId('search-split-panel_products')
      .or(this.page.locator('section, aside, div').filter({ has: label }))
      .first();
  }

  productTitles(): Locator {
    return this.productsSection().locator('a, h3, [data-testid*="title" i]');
  }

  // -------------------------- style assertions -----------------------------

  /** Computed `border-radius` of an element, in pixels (0 if unparseable). */
  async borderRadiusPx(locator: Locator): Promise<number> {
    return locator.evaluate((el) => {
      const br = window.getComputedStyle(el).borderRadius;
      const match = br.match(/([\d.]+)px/);
      return match ? parseFloat(match[1]) : 0;
    });
  }

  /** Assert the element is visually a pill (rounded), not a logo. */
  async expectRenderedAsPill(locator: Locator, minRadiusPx = 12): Promise<void> {
    const radius = await this.borderRadiusPx(locator);
    expect(
      radius,
      `Expected pill with border-radius ≥ ${minRadiusPx}px, got ${radius}px`
    ).toBeGreaterThanOrEqual(minRadiusPx);
  }

  // -------------------------- text content assertions ----------------------

  /** True if the string still contains literal HTML entities (&reg;, &trade;...). */
  static hasUnrenderedHtmlEntities(text: string): boolean {
    return /&(?:reg|trade|copy|amp|nbsp|lt|gt);/i.test(text ?? '');
  }

  /** Fail if any element under `locator` has raw HTML entities in its text. */
  async expectNoHtmlEntities(locator: Locator): Promise<void> {
    const texts: string[] = await locator.evaluateAll((els) =>
      els.map((el) => el.textContent ?? '')
    );
    const offending = texts.filter((t) =>
      SearchModal.hasUnrenderedHtmlEntities(t)
    );
    expect(
      offending,
      `Found ${offending.length} element(s) with unrendered HTML entities:\n` +
        offending.map((t) => `  • ${t.trim()}`).join('\n')
    ).toEqual([]);
  }
}
