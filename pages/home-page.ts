import { expect } from '@playwright/test';
import { BasePage } from './base-page';

/** Page Object for the oneshop home page. */
export class HomePage extends BasePage {
  protected readonly path = '/';

  async expectLoaded(): Promise<void> {
    await expect(this.page).toHaveURL(/oneshop/i);
  }
}
