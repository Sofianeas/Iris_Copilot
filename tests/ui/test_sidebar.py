"""
Tests des composants Sidebar.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.ui.sidebar import (
    sidebar,
    sidebar_divider,
    sidebar_section,
    sidebar_text,
    sidebar_title,
)


@patch("app.ui.sidebar.st.sidebar.title")
def test_sidebar_title(mock_title: MagicMock) -> None:
    """sidebar_title() doit appeler st.sidebar.title()."""

    sidebar_title("IRIS")

    mock_title.assert_called_once_with("IRIS")


@patch("app.ui.sidebar.st.sidebar.subheader")
def test_sidebar_section(mock_subheader: MagicMock) -> None:
    """sidebar_section() doit appeler st.sidebar.subheader()."""

    sidebar_section("Informations")

    mock_subheader.assert_called_once_with("Informations")


@patch("app.ui.sidebar.st.sidebar.write")
def test_sidebar_text(mock_write: MagicMock) -> None:
    """sidebar_text() doit appeler st.sidebar.write()."""

    sidebar_text("Version")

    mock_write.assert_called_once_with("Version")


@patch("app.ui.sidebar.st.sidebar.divider")
def test_sidebar_divider(mock_divider: MagicMock) -> None:
    """sidebar_divider() doit appeler st.sidebar.divider()."""

    sidebar_divider()

    mock_divider.assert_called_once()


@patch("app.ui.sidebar.st.sidebar")
def test_sidebar_context(mock_sidebar: MagicMock) -> None:
    """sidebar() doit ouvrir un contexte sur st.sidebar."""

    mock_sidebar.__enter__.return_value = MagicMock()

    with sidebar():
        pass

    mock_sidebar.__enter__.assert_called_once()
    mock_sidebar.__exit__.assert_called_once()