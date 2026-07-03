"""
IRIS Copilot
Layout Components

Composants de structure réutilisables.
"""

from __future__ import annotations

import streamlit as st

from .constants import COPYRIGHT

from .render import render_html


# ==========================================================
# HERO
# ==========================================================

def _build_hero(
    title: str,
    subtitle: str = "",
    icon: str = "🛠️",
) -> str:
    """
    Build the hero section HTML.
    """
    return f"""
    <div class="hero">
        <div class="hero-title">{icon} {title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """


def hero(
    title: str,
    subtitle: str = "",
    icon: str = "🛠️",
) -> None:
    """
    Affiche le bandeau principal de la page.
    """
    render_html(_build_hero(title, subtitle, icon))


# ==========================================================
# SECTION
# ==========================================================

def _build_section(
    title: str,
    icon: str = "",
) -> str:
    """
    Build a section heading HTML.
    """
    return f"""
    <div class="section-title">
        {icon} {title}
    </div>
    """


def section(
    title: str,
    icon: str = "",
) -> None:
    """
    Affiche un titre de section.
    """
    render_html(_build_section(title, icon))
    st.divider()


# ==========================================================
# DIVIDER
# ==========================================================

def divider() -> None:
    """
    Affiche une ligne de séparation.
    """
    st.divider()


# ==========================================================
# EMPTY STATE
# ==========================================================

def empty_state(
    text: str,
    icon: str = "📄",
) -> None:
    """
    Affiche un message lorsqu'il n'y a aucune donnée.
    """
    st.info(f"{icon} {text}")


# ==========================================================
# FOOTER
# ==========================================================

def footer() -> None:
    """
    Pied de page commun.
    """
    st.divider()
    st.caption(COPYRIGHT)


# ==========================================================
# PAGE TITLE
# ==========================================================

def page_title(
    title: str,
    icon: str = "📄",
) -> None:
    """
    Affiche un titre simple.
    """
    st.title(f"{icon} {title}")