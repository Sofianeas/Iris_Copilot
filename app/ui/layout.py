"""
IRIS Copilot
Layout Components

Composants de structure réutilisables.
"""

from __future__ import annotations

import streamlit as st

from .constants import (
    APP_NAME,
    APP_SUBTITLE,
    COPYRIGHT,
)


# ==========================================================
# HERO
# ==========================================================

def hero(
    title: str,
    subtitle: str = "",
    icon: str = "🛠️",
) -> None:
    """
    Affiche le bandeau principal de la page.
    """

    st.markdown(
        f"""
<div class="hero fade-in">

<h1>{icon} {title}</h1>

<p>{subtitle}</p>

</div>
""",
        unsafe_allow_html=True,
    )


# ==========================================================
# SECTION
# ==========================================================

def section(
    title: str,
    icon: str = "",
) -> None:
    """
    Affiche un titre de section.
    """

    st.markdown(
        f"""
<h2>{icon} {title}</h2>
""",
        unsafe_allow_html=True,
    )

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