"""
Tests d'intégration du pipeline de navigation.

Ce module valide la chaîne complète :

PageRegistry
    ↓
Navigator
    ↓
PageResolver
    ↓
PageFactory
    ↓
DashboardPage
"""

from app.shell.navigation import Navigator, create_registry
from app.shell.session import SessionManager

from pages.base import (
    PageContext,
    PageFactory,
    PageResolver,
)

from pages.dashboard.page import DashboardPage


def test_navigation_pipeline() -> None:
    """
    Vérifie le pipeline complet de création d'une page.
    """

    # ------------------------------------------------------------------
    # Infrastructure
    # ------------------------------------------------------------------

    session = SessionManager()
    session.initialize()

    registry = create_registry()

    navigator = Navigator(
        registry=registry,
        session=session,
    )

    # ------------------------------------------------------------------
    # Framework des Pages
    # ------------------------------------------------------------------

    context = PageContext(
        navigator=navigator,
        session=session,
    )

    factory = PageFactory(context)
    resolver = PageResolver()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    page = navigator.current_page()

    assert page.id == "dashboard"

    # ------------------------------------------------------------------
    # Résolution
    # ------------------------------------------------------------------

    page_cls = resolver.resolve(page.id)

    assert page_cls is DashboardPage

    # ------------------------------------------------------------------
    # Instanciation
    # ------------------------------------------------------------------

    dashboard = factory.create(page_cls)

    assert isinstance(dashboard, DashboardPage)

    # ------------------------------------------------------------------
    # Injection
    # ------------------------------------------------------------------

    assert dashboard.context is context