import { Page } from '@playwright/test';

/**
 * Base class for all Page Objects.
 * Subclasses set a `path` and implement `expectLoaded()`.
 */
export abstract class BasePage {
  protected readonly page: Page;
  protected readonly path: string = '/';

  constructor(page: Page) {
    this.page = page;
  }

  /** Navigate to this page using its `path` (relative to baseURL). */
  async navigate(): Promise<this> {
    await this.page.goto(this.path);
    return this;
  }

  /**
   * Each page must implement a load assertion that confirms it is ready
   * for interaction (a visible heading, a stable URL, a known testId, etc.).
   */
  abstract expectLoaded(): Promise<void>;
}
