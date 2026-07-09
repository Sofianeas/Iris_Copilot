"""
Composant Header du Layout.

Ce module définit la zone supérieure de l'application.

Responsabilités
----------------
- Afficher l'en-tête de l'application.
- Afficher le titre et l'icône.
- Fournir un point d'entrée unique pour le rendu.

Le Header ne contient aucune logique métier.
"""

from __future__ import annotations

import streamlit as st

from .config import APPLICATION_ICON, APPLICATION_TITLE


class Header:
    """
    Composant représentant le Header de l'application.
    """

    def render(self) -> None:
        """
        Affiche le Header de l'application.
        """
        st.title(f"{APPLICATION_ICON} {APPLICATION_TITLE}")