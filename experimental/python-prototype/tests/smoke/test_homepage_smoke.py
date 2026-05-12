"""
Smoke test inicial — verifica que oneshop carga correctamente.
Este es el primer test del proyecto, sirve para validar el setup.
"""

import pytest
from playwright.sync_api import Page, expect
from pages.home_page import HomePage


@pytest.mark.smoke
def test_homepage_loads(page: Page):
    """
    Monday: N/A (smoke de infraestructura)
    Verifica que la home de oneshop carga sin errores y devuelve
    una URL válida.
    """
    home = HomePage(page).navigate()
    home.expect_loaded()


@pytest.mark.smoke
def test_homepage_has_no_console_errors(page: Page):
    """
    Monday: N/A (smoke de infraestructura)
    Verifica que al cargar la home no aparecen errores graves en la consola
    del navegador.
    """
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    HomePage(page).navigate().expect_loaded()

    assert not errors, f"Errores en consola: {errors}"
