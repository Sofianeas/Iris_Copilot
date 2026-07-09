"""
Composant Workspace du Layout.

Ce module définit la zone principale de travail de
l'application.

Responsabilités
----------------
- Afficher la page actuellement sélectionnée.
- Déléguer le rendu au modèle Page.

Le Workspace ne contient aucune logique métier.
"""

from __future__ import annotations

from app.shell.navigation import Navigator


class Workspace:
    """
    Zone principale de travail de l'application.
    """

    def __init__(self, navigator: Navigator) -> None:
        """
        Initialise le Workspace.

        Parameters
        ----------
        navigator : Navigator
            Gestionnaire de navigation.
        """
        self._navigator = navigator

    def render(self) -> None:
        """
        Affiche la page actuellement sélectionnée.
        """
        page = self._navigator.current_page()
        page.render()