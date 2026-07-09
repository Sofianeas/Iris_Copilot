"""
Composant Header du Dashboard.

Responsabilités
---------------
- Présenter IRIS Copilot.
- Accueillir l'utilisateur.
- Introduire le Dashboard.

Aucune logique métier ne doit être implémentée ici.
"""

from __future__ import annotations

import streamlit as st

from .config import (
    DASHBOARD_TITLE,
    DASHBOARD_SUBTITLE,
    DASHBOARD_DESCRIPTION,
    WELCOME_MESSAGE,
)


def render_header() -> None:
    """
    Affiche l'en-tête du Dashboard.
    """

    st.title(DASHBOARD_TITLE)

    st.caption(DASHBOARD_SUBTITLE)

    st.write(DASHBOARD_DESCRIPTION)

    st.info(WELCOME_MESSAGE)