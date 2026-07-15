"""
Tests d'intégration du Composition Root.

Ces tests vérifient que ApplicationShell construit
correctement toutes les dépendances du Framework.

Ils ne testent ni Streamlit, ni le rendu graphique.
"""

from app.shell.app_shell import ApplicationShell
from app.shell.layout import Layout
from app.shell.navigation import Navigator, PageRegistry
from app.shell.session import SessionManager

from pages.base import (
    PageContext,
    PageFactory,
    PageResolver,
)


def test_shell_creates_session_manager() -> None:
    shell = ApplicationShell()

    assert isinstance(shell.session, SessionManager)


def test_shell_creates_page_registry() -> None:
    shell = ApplicationShell()

    assert isinstance(shell.registry, PageRegistry)


def test_shell_creates_navigator() -> None:
    shell = ApplicationShell()

    assert isinstance(shell.navigator, Navigator)


def test_shell_creates_page_context() -> None:
    shell = ApplicationShell()

    assert isinstance(shell.page_context, PageContext)


def test_shell_creates_page_factory() -> None:
    shell = ApplicationShell()

    assert isinstance(shell.page_factory, PageFactory)


def test_shell_creates_page_resolver() -> None:
    shell = ApplicationShell()

    assert isinstance(shell.page_resolver, PageResolver)


def test_shell_creates_layout() -> None:
    shell = ApplicationShell()

    assert isinstance(shell.layout, Layout)