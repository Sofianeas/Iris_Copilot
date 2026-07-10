"""
Classe de base du Framework des Pages.

Toutes les pages de l'application doivent hériter de BasePage.

Cette classe centralise les comportements communs et constitue
le point d'entrée du Framework des Pages.
"""

from __future__ import annotations

from abc import abstractmethod

from .interfaces import Page
from .page_context import PageContext


class BasePage(Page):
    """
    Classe de base de toutes les pages d'IRIS Copilot.
    """

    def __init__(self, context: PageContext) -> None:
        """
        Initialise une nouvelle page.

        Parameters
        ----------
        context:
            Contexte partagé fourni par le Framework.
        """
        self._context = context

    @property
    def context(self) -> PageContext:
        """
        Retourne le contexte partagé de la page.
        """
        return self._context

    @abstractmethod
    def render(self) -> None:
        """
        Affiche le contenu de la page.
        """
        raise NotImplementedError