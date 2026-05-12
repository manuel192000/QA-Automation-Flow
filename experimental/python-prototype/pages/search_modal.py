"""
Page Object del modal de búsqueda predictiva de oneshop.

Selectores confirmados con `playwright codegen` (mayo 2026):
- Trigger / input visible del header: data-testid="search-split-panel_input"
- Pills de marcas (Brands section): <button> con accessible name exact = "<MARCA>"

Otros selectores (contenedor del panel, sección "Brands") aún no confirmados —
se manejan con `.or_()` y fallbacks robustos para que el test funcione mientras
se afinan.
"""

import re
from playwright.sync_api import Page, Locator, expect


class SearchModal:
    """Modal/panel de búsqueda predictiva del header."""

    def __init__(self, page: Page):
        self.page = page

    # ------------------------ cookies (one-shot) ------------------------

    def accept_cookies_if_present(self, timeout_ms: int = 2000) -> "SearchModal":
        """
        Cierra el banner de cookies si está visible. Idempotente: si ya
        fue aceptado o no existe, no rompe.
        """
        try:
            btn = self.page.get_by_role("button", name=re.compile(r"accept all", re.IGNORECASE))
            btn.wait_for(state="visible", timeout=timeout_ms)
            btn.click()
        except Exception:
            pass
        return self

    # ------------------------ apertura del panel ------------------------

    @property
    def search_input(self) -> Locator:
        """Input visible en el header — también funciona como trigger."""
        return self.page.get_by_test_id("search-split-panel_input")

    def open(self) -> "SearchModal":
        """Hace foco en el input para abrir el panel de resultados."""
        self.search_input.click()
        # No usamos expect(dialog) porque el panel no es role="dialog".
        # La verificación real viene cuando aparecen las secciones de resultados.
        return self

    # ------------------------ input -------------------------------------

    def type_query(self, query: str) -> "SearchModal":
        """Escribe el término de búsqueda. Playwright espera el debounce auto."""
        self.search_input.fill(query)
        return self

    # ------------------------ pills de marcas ---------------------------

    def brand_pill(self, brand_name: str) -> Locator:
        """
        Pill de una marca en la sección Brands del panel.
        Los pills son <button> con accessible name exacto = nombre de marca
        (en mayúsculas, ej. "AMANA").
        """
        return self.page.get_by_role(
            "button", name=brand_name.upper(), exact=True
        )

    # ------------------------ featured products section ---------------

    def featured_products_section(self) -> Locator:
        """
        Container of the "Featured Products" section of the panel.
        TODO(selector): confirm the real data-testid with codegen. The
        fallback looks for the section by its label text.
        """
        label_re = re.compile(r"^\s*featured products\s*$", re.IGNORECASE)
        return (
            self.page.get_by_test_id("search-split-panel_featured-products")
            .or_(
                self.page.locator("section, aside, div").filter(
                    has=self.page.get_by_text(label_re)
                )
            )
            .first
        )

    def featured_product_titles(self) -> Locator:
        """
        Titles of the products listed in the Featured Products section.
        TODO(selector): adjust to the real product-title element (heading,
        link, or specific data-testid). Today we treat each product item
        as a link or heading inside the section.
        """
        section = self.featured_products_section()
        return section.locator("a, h3, [data-testid*='title' i]")

    # ------------------------ generic products section -----------------

    def products_section(self) -> Locator:
        """
        Container of the generic "Products" (Algolia) section of the panel.
        Used to validate trademark rendering on the non-featured side.
        """
        label_re = re.compile(r"^\s*products\s*$", re.IGNORECASE)
        return (
            self.page.get_by_test_id("search-split-panel_products")
            .or_(
                self.page.locator("section, aside, div").filter(
                    has=self.page.get_by_text(label_re)
                )
            )
            .first
        )

    def product_titles(self) -> Locator:
        """Titles of items in the generic Products section (Algolia)."""
        return self.products_section().locator("a, h3, [data-testid*='title' i]")

    # ------------------------ assertions on text content ---------------

    @staticmethod
    def has_unrendered_html_entities(text: str) -> bool:
        """True if the string still contains literal HTML entities like &reg; or &trade;."""
        return bool(re.search(r"&(?:reg|trade|copy|amp|nbsp|lt|gt);", text or "", re.IGNORECASE))

    def expect_no_html_entities(self, locator: Locator):
        """
        Assert that none of the elements matched by `locator` contain raw
        HTML entities (&reg;, &trade;, etc.) in their text — they should
        be rendered as actual characters.
        """
        # Evaluate the textContent of every matching element
        texts = locator.evaluate_all("els => els.map(el => el.textContent || '')")
        offending = [t for t in texts if self.has_unrendered_html_entities(t)]
        assert not offending, (
            f"Found {len(offending)} element(s) with unrendered HTML entities:\n"
            + "\n".join(f"  • {t.strip()}" for t in offending)
        )

    def brands_section(self) -> Locator:
        """
        Contenedor de la sección "Brands" dentro del panel.

        Confirmado por screenshot (mayo 2026): el label "BRANDS" no es un
        heading semántico (<h*>), es texto plano dentro de la columna
        izquierda del panel. Localizamos por texto exacto y subimos al
        contenedor más cercano.
        """
        brands_label_re = re.compile(r"^\s*brands\s*$", re.IGNORECASE)
        return (
            self.page.get_by_test_id("search-split-panel_brands")
            .or_(
                # Contenedor que contiene el texto "BRANDS" como label de sección
                self.page.locator("section, aside, div").filter(
                    has=self.page.get_by_text(brands_label_re)
                )
            )
            .first
        )

    # ------------------------ aserciones de estilo ----------------------

    @staticmethod
    def border_radius_px(locator: Locator) -> float:
        """Lee el border-radius computado del elemento y lo devuelve en px."""
        return locator.evaluate(
            """el => {
                const br = window.getComputedStyle(el).borderRadius;
                const match = br.match(/([\\d.]+)px/);
                return match ? parseFloat(match[1]) : 0;
            }"""
        )

    def expect_rendered_as_pill(self, locator: Locator, min_radius_px: float = 12):
        """
        Verifica que el elemento está renderizado como pill, no como logo.
        12px es un umbral conservador; en la práctica las pills suelen tener
        border-radius >= 9999px (full rounded). Ajustar si el design system
        de oneshop usa otro valor.
        """
        radius = self.border_radius_px(locator)
        assert radius >= min_radius_px, (
            f"Se esperaba pill con border-radius ≥ {min_radius_px}px, "
            f"got: {radius}px"
        )
