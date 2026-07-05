"""
IRIS Copilot
Theme Management
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

_THEME_LOADED = False

CSS_FILES = [
    "variables.css",
    "typography.css",
    "layout.css",
    "cards.css",
    "badges.css",
    "alerts.css",
    "forms.css",
    "tables.css",
    "sidebar.css",
    "animations.css",
]


def load_theme() -> None:
    """
    Charge le Design System une seule fois.
    """

    global _THEME_LOADED

    if _THEME_LOADED:
        return

    styles_dir = Path(__file__).parent / "styles"

    css = ""

    for filename in CSS_FILES:
        css_path = styles_dir / filename

        if css_path.exists():
            css += css_path.read_text(encoding="utf-8")
            css += "\n\n"

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )

    _THEME_LOADED = True


def configure_page(title: str | None = None) -> None:
    """
    Configure une page IRIS.

    - Charge automatiquement le thème.
    - Affiche éventuellement un titre.
    """

    load_theme()

    if title:
        st.title(title)