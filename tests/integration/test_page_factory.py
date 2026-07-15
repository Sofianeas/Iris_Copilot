"""
Tests d'intégration de la PageFactory.

La PageFactory est responsable de créer les instances des
pages du Framework et d'y injecter automatiquement le
PageContext.
"""

from pages.base import (
    PageContext,
    PageFactory,
)

from pages.dashboard.page import DashboardPage


def test_factory_creates_dashboard_page() -> None:
    """
    La factory doit créer une instance de DashboardPage.
    """
    context = PageContext()

    factory = PageFactory(context)

    page = factory.create(DashboardPage)

    assert isinstance(page, DashboardPage)


def test_factory_injects_page_context() -> None:
    """
    La factory doit injecter le PageContext dans la page.
    """
    context = PageContext()

    factory = PageFactory(context)

    page = factory.create(DashboardPage)

    assert page.context is context


def test_factory_preserves_context_instance() -> None:
    """
    La même instance de contexte doit être partagée.
    """
    context = PageContext()

    factory = PageFactory(context)

    page1 = factory.create(DashboardPage)
    page2 = factory.create(DashboardPage)

    assert page1.context is context
    assert page2.context is context
    assert page1.context is page2.context