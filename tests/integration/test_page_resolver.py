"""
Tests d'intégration du PageResolver.

Le PageResolver est responsable de convertir un identifiant
de navigation en classe concrète de page.

Ces tests ne créent aucune page.
Ils vérifient uniquement la résolution.
"""

import pytest

from pages.base import PageResolver
from pages.dashboard.page import DashboardPage


def test_resolve_dashboard_page() -> None:
    """
    Le resolver doit retourner DashboardPage
    pour l'identifiant 'dashboard'.
    """
    resolver = PageResolver()

    page_cls = resolver.resolve("dashboard")

    assert page_cls is DashboardPage


def test_resolve_unknown_page_raises_key_error() -> None:
    """
    Un identifiant inconnu doit lever KeyError.
    """
    resolver = PageResolver()

    with pytest.raises(KeyError):
        resolver.resolve("unknown_page")