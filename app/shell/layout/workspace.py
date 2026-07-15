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

from pages.base import (
    PageFactory,
    PageResolver,
)


class Workspace:
    """
    Zone principale de travail de l'application.
    """

    def __init__(self, navigator: Navigator, page_factory: PageFactory, page_resolver: PageResolver,) -> None:
        """
        Initialise le Workspace.

        Parameters
        ----------
        navigator : Navigator
            Gestionnaire de navigation.
        """
        self._navigator = navigator
        self._page_factory = page_factory
        self._page_resolver = page_resolver

    def render(self) -> None:
        """
        Affiche la page actuellement sélectionnée.
        """

        # Métadonnées de navigation
        page = self._navigator.current_page()

        # Classe concrète
        page_cls = self._page_resolver.resolve(page.id)

        # Instance de la page
        page_instance = self._page_factory.create(page_cls)

        # Rendu
        page_instance.render()