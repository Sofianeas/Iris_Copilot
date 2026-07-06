"""
Tests des composants Navigation.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.ui.navigation import (
    breadcrumbs,
    nav_group,
    nav_link,
    tabs,
)


@patch("app.ui.navigation.st.caption")
def test_breadcrumbs(mock_caption: MagicMock) -> None:
    """breadcrumbs() doit afficher le fil d'Ariane."""

    breadcrumbs(["Accueil", "Support", "Ticket"])

    mock_caption.assert_called_once_with(
        "Accueil › Support › Ticket"
    )


@patch("app.ui.navigation.st.tabs")
def test_tabs(mock_tabs: MagicMock) -> None:
    """tabs() doit appeler st.tabs()."""

    tabs(["A", "B"])

    mock_tabs.assert_called_once_with(["A", "B"])


@patch("app.ui.navigation.st.subheader")
def test_nav_group(mock_subheader: MagicMock) -> None:
    """nav_group() doit appeler st.subheader()."""

    nav_group("Administration")

    mock_subheader.assert_called_once_with("Administration")


@patch("app.ui.navigation.st.write")
def test_nav_link(mock_write: MagicMock) -> None:
    """nav_link() doit appeler st.write()."""

    nav_link("Accueil")

    mock_write.assert_called_once_with("• Accueil")