"""
Tests unitaires de la PageFactory.

Ces tests vérifient que la fabrique construit correctement
les pages du Framework et injecte le PageContext.
"""

from __future__ import annotations

import pytest

from pages.base import BasePage, PageContext, PageFactory


class DummyPage(BasePage):
    """
    Page factice utilisée pour les tests.
    """

    def render(self) -> None:
        pass


class InvalidPage:
    """
    Classe ne respectant pas le contrat BasePage.
    """
    pass


def test_create_returns_page_instance() -> None:
    """
    La fabrique doit retourner une instance de la page demandée.
    """
    context = PageContext()
    factory = PageFactory(context)

    page = factory.create(DummyPage)

    assert isinstance(page, DummyPage)


def test_create_injects_context() -> None:
    """
    Le contexte doit être injecté dans la page créée.
    """
    context = PageContext()
    factory = PageFactory(context)

    page = factory.create(DummyPage)

    assert page.context is context


def test_create_returns_base_page() -> None:
    """
    Toute page créée doit hériter de BasePage.
    """
    context = PageContext()
    factory = PageFactory(context)

    page = factory.create(DummyPage)

    assert isinstance(page, BasePage)


def test_create_rejects_invalid_page() -> None:
    """
    Une classe ne dérivant pas de BasePage doit être refusée.
    """
    context = PageContext()
    factory = PageFactory(context)

    with pytest.raises(TypeError):
        factory.create(InvalidPage)