"""
Layout global de l'application.

Ce module orchestre les différents composants constituant
l'interface utilisateur.

Responsabilités
----------------
- Construire les composants du Layout.
- Orchestrer leur rendu.
- Respecter la configuration globale.

Le Layout ne contient aucune logique métier.
"""

from __future__ import annotations

from app.shell.navigation import Navigator

from pages.base import (
    PageFactory,
    PageResolver,
)

from .config import (
    SHOW_FOOTER,
    SHOW_HEADER,
    SHOW_SIDEBAR,
    SHOW_WORKSPACE,
)
from .footer import Footer
from .header import Header
from .sidebar import Sidebar
from .workspace import Workspace

class Layout:
    """
    Layout principal de l'application.
    """

    def __init__(self, navigator: Navigator, page_factory: PageFactory, page_resolver: PageResolver,) -> None:
        """
        Initialise les composants du Layout.

        Parameters
        ----------
        navigator : Navigator
            Gestionnaire de navigation.
        """
        self._header = Header()
        self._sidebar = Sidebar(navigator)
        self._workspace = Workspace(navigator=navigator,page_factory=page_factory,page_resolver=page_resolver,)
        self._footer = Footer()

    def render(self) -> None:
        """
        Affiche le Layout complet de l'application.
        """

        if SHOW_HEADER:
            self._header.render()

        if SHOW_SIDEBAR:
            self._sidebar.render()

        if SHOW_WORKSPACE:
            self._workspace.render()

        if SHOW_FOOTER:
            self._footer.render()