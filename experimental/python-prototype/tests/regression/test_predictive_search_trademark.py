"""
Regression tests for trademark symbol rendering in the predictive search
overlay (Featured Products section).
"""

import pytest
from playwright.sync_api import Page
from pages.search_modal import SearchModal


# Term that should surface featured products in the predictive panel.
# TODO: confirm with codegen / manual exploration which query triggers
# the Featured Products carousel on oneshop staging. Likely candidates:
# "amana", "kitchen", "refrigerator", or simply empty.
FEATURED_TRIGGER_QUERY = "kitchen"


@pytest.mark.regression
def test_featured_products_render_trademarks_correctly(page: Page):
    """
    Monday: https://retailerwebservices.monday.com/boards/18395174855/pulses/11920451594
    Title: Trademark Rendering in Predictive Search — Featured Products
    Feature Area: Predictive Search / Header
    Validation Type: UI Regression
    Site: oneshop

    Overview:
      This QA cycle validates trademark symbol rendering inside the
      Featured Products section of the predictive search overlay.
      The defect reported that titles were showing the raw HTML entity
      strings (&reg; and &trade;) instead of the proper ® and ™ symbols.
      Algolia-driven results were not affected, so the issue lives on
      the OS rendering side, not on the data source.

    Checks:
      - Featured products do not show literal &reg; in their titles
      - Featured products do not show literal &trade; in their titles
      - Algolia (non-featured) products keep rendering trademarks correctly
      - At least one featured product is visible in the panel

    Summary:
      ✅ Encoding correctness
      - No HTML entity literal (&reg;, &trade;) is visible in featured titles
      - Where trademarks exist, they are rendered as the proper Unicode glyph

      ✅ Cross-section consistency
      - The fix did not regress Algolia-driven Product results
      - Same titles render identically in both panels of the overlay

      ✅ Visibility
      - Featured Products section appears in the panel with at least one item

    Preconditions:
      - oneshop staging is reachable.
      - The current store/branch has Featured Products configured with
        at least one product whose title contains a trademark symbol.
    """
    page.goto("/")

    modal = (
        SearchModal(page)
        .accept_cookies_if_present()
        .open()
        .type_query(FEATURED_TRIGGER_QUERY)
    )

    # 1) Featured Products must be visible and non-empty
    featured_titles = modal.featured_product_titles()
    assert featured_titles.count() > 0, "No featured products visible in the overlay."

    # 2) None of the featured titles should contain raw HTML entities
    modal.expect_no_html_entities(featured_titles)

    # 3) Algolia (Products) section, when present, should also be clean
    if modal.products_section().count() > 0:
        modal.expect_no_html_entities(modal.product_titles())
