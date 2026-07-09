"""
Composant Footer du Layout.

Ce module définit la zone inférieure de l'application.

Responsabilités
----------------
- Afficher les informations générales de l'application.
- Fournir un point d'entrée unique pour le rendu.

Le Footer ne contient aucune logique métier.
"""

from __future__ import annotations

import streamlit as st

from .config import APPLICATION_VERSION


class Footer:
    """
    Composant représentant le Footer de l'application.
    """

    def render(self) -> None:
        """
        Affiche le Footer de l'application.
        """
        st.caption(f"Version {APPLICATION_VERSION}")