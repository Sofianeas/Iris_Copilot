"""
Composant Sidebar du Layout.

Ce module définit la barre latérale de l'application.

Responsabilités
----------------
- Afficher la navigation.
- Afficher les pages enregistrées.
- Mettre en évidence la page active.

La Sidebar ne contient aucune logique métier.
Elle s'appuie uniquement sur le Navigator.
"""

from __future__ import annotations

import streamlit as st

from app.shell.navigation import Navigator


class Sidebar:
    """
    Barre latérale de l'application.
    """

    def __init__(self, navigator: Navigator) -> None:
        """
        Initialise la Sidebar.

        Parameters
        ----------
        navigator : Navigator
            Gestionnaire de navigation.
        """
        self._navigator = navigator

    def render(self) -> None:
        """
        Affiche la barre latérale.
        """
        with st.sidebar:

            st.header("Navigation")

            current_page = self._navigator.current_page_id()

            for page in self._navigator.pages():

                label = page.title

                if page.id == current_page:
                    label = f"▶ {label}"

                st.write(label)