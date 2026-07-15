"""
Tests d'intégration du système de navigation.

Ces tests vérifient que le registre des pages est correctement
initialisé et que la navigation peut retrouver la page par défaut.
"""

from app.shell.navigation import create_registry
from app.shell.navigation.config import DEFAULT_PAGE_ID


def test_registry_contains_dashboard() -> None:
    """
    Le registre doit contenir la page Dashboard.
    """
    registry = create_registry()

    assert registry.exists(DEFAULT_PAGE_ID)


def test_registry_returns_dashboard() -> None:
    """
    Le registre doit retourner les métadonnées du Dashboard.
    """
    registry = create_registry()

    page = registry.get(DEFAULT_PAGE_ID)

    assert page.id == DEFAULT_PAGE_ID
    assert page.title == "Dashboard"


def test_registry_contains_one_page() -> None:
    """
    Le registre contient actuellement une seule page.
    """
    registry = create_registry()

    pages = registry.get_all()

    assert len(pages) == 1