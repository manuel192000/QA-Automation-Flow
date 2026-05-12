"""
Regression tests for the predictive search panel (header).

Covers the NGSCH Follow-Up change: featured brands are no longer rendered
as logos, they now appear as text pills (same visual pattern as recent
searches pills).
"""

import pytest
from playwright.sync_api import Page, expect
from pages.search_modal import SearchModal


@pytest.mark.regression
def test_predictive_search_shows_amana_brand_as_pill(page: Page):
    """
    Monday: https://retailerwebservices.monday.com/boards/18395174855/pulses/11916681731
    Title: Predictive Search — Featured Brands as Pills
    Feature Area: Predictive Search / Header
    Validation Type: UI Regression
    Site: oneshop

    Overview:
      This QA cycle validates the visual treatment of featured brands in the
      predictive search panel of the header.
      Previously, brand suggestions were rendered as logos. The product
      decision was to align them with the existing pill pattern used by
      recent searches — text inside a rounded button, no logo image.
      The goal of this validation is to confirm that the new design renders
      correctly and that brands still appear under the "Brands" section of
      the panel after typing a brand query.

    Checks:
      - AMANA brand appears in the predictive search results
      - AMANA brand is rendered inside the "Brands" section of the panel
      - AMANA brand is rendered as a pill (rounded border-radius), not a logo

    Summary:
      ✅ Visual rendering
      - Brand appears as a rounded text pill, matching the recent-searches pattern
      - No logo image is rendered for the brand entry

      ✅ Section placement
      - The brand item is contained within the "Brands" section of the panel
      - The "Brands" label remains visible above its items

      ✅ Search behavior
      - Typing a brand term surfaces the matching brand in the panel
      - The result is reachable as a clickable button (role=button)

    Preconditions:
      - Brand "Amana" exists as a featured brand in oneshop staging.
    """
    page.goto("/")

    modal = (
        SearchModal(page)
        .accept_cookies_if_present()
        .open()
        .type_query("amana")
    )

    # 1) AMANA pill must be visible in the panel
    amana = modal.brand_pill("AMANA")
    expect(amana).to_be_visible()

    # 2) It must live inside the "Brands" section
    expect(modal.brands_section()).to_be_visible()
    expect(
        modal.brands_section().get_by_role("button", name="AMANA", exact=True)
    ).to_be_visible()

    # 3) And be rendered as a pill (rounded border-radius)
    modal.expect_rendered_as_pill(amana)
