"""
IRIS Copilot
Render Utilities

Fonctions communes de rendu HTML.
"""

from __future__ import annotations

import streamlit as st


def render_html(
    html: str,
    unsafe_allow_html: bool =True,
) -> None:
    """
    Rend un fragment HTML.

    Parameters
    ----------
    html:
        Code HTML à afficher.

    unsafe_allow_html:
        Autorise le rendu HTML.
    """

    st.markdown(
        html,
        unsafe_allow_html=unsafe_allow_html,
    )