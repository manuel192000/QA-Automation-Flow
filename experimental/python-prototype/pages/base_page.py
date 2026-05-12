"""
Clase base para todos los Page Objects.

Un Page Object es una clase que representa una página o componente de la
aplicación. Encapsula los locators y las acciones, para que los tests
queden limpios y los cambios de UI se arreglen en un solo lugar.
"""

from playwright.sync_api import Page, expect


class BasePage:
    """Funcionalidad compartida por todas las páginas."""

    # Subclases deben sobreescribir esto con la ruta relativa (ej: "/login")
    path: str = "/"

    def __init__(self, page: Page):
        self.page = page

    def navigate(self):
        """Navega a la página usando self.path + base_url del contexto."""
        self.page.goto(self.path)
        return self

    def expect_loaded(self):
        """
        Verifica que la página cargó correctamente.
        Las subclases deben implementar su criterio (un heading visible,
        un texto, una URL, etc.).
        """
        raise NotImplementedError(
            "Cada Page Object debe implementar expect_loaded()"
        )
