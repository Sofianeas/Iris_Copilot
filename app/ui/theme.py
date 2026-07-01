"""
IRIS Copilot
Theme Manager

Charge et applique le thème global de l'application.
Toutes les pages doivent appeler apply_theme()
en tout début de leur exécution.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st


# ------------------------------------------------------------------
# Localisation du CSS
# ------------------------------------------------------------------

UI_DIR = Path(__file__).resolve().parent
CSS_FILE = UI_DIR / "styles.css"


# ------------------------------------------------------------------
# Chargement du CSS
# ------------------------------------------------------------------

@st.cache_resource
def _load_css() -> str:
    """
    Charge le fichier CSS une seule fois.
    """
    if not CSS_FILE.exists():
        raise FileNotFoundError(
            f"Impossible de trouver le fichier CSS : {CSS_FILE}"
        )

    return CSS_FILE.read_text(encoding="utf-8")


# ------------------------------------------------------------------
# Application du thème
# ------------------------------------------------------------------

def apply_theme() -> None:
    """
    Injecte le thème global IRIS Copilot.

    À appeler une seule fois
    au début de chaque page Streamlit.
    """

    css = _load_css()

    st.markdown(
        f"""
<style>
{css}
</style>
""",
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def horizontal_rule() -> None:
    """Séparateur standard."""

    st.markdown("<hr>", unsafe_allow_html=True)


def vertical_space(lines: int = 1) -> None:
    """Ajoute de l'espace vertical."""

    for _ in range(lines):
        st.write("")

# ==========================================================
# CONFIGURATION DE PAGE
# ==========================================================

def configure_page(
    title: str,
    icon: str = "🛠️",
    layout: str = "wide",
) -> None:
    """
    Configure une page Streamlit avec les paramètres
    standard d'IRIS Copilot puis applique le thème.
    """

    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state="expanded",
    )

    apply_theme()