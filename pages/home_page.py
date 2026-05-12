"""Page Object para la home de oneshop."""

import re
from playwright.sync_api import expect
from pages.base_page import BasePage


class HomePage(BasePage):
    path = "/"

    def expect_loaded(self):
        """
        Verifica que la home cargó. Ajusta este criterio cuando conozcas
        un elemento estable (ej: el logo, un heading principal, etc.).
        """
        expect(self.page).to_have_url(re.compile(r"oneshop"))
        return self
