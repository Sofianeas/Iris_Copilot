"""
Fabrique des pages du Framework.

La PageFactory est responsable de la création des instances
de pages de l'application.

Elle centralise l'injection du PageContext afin d'éviter
que le reste de l'application n'instancie directement les
pages concrètes.

La Factory ne contient aucune logique métier.
"""

from __future__ import annotations

from typing import TypeVar

from .base_page import BasePage
from .page_context import PageContext

T = TypeVar("T", bound=BasePage)


class PageFactory:
    """
    Fabrique des pages du Framework.
    """

    def __init__(self, context: PageContext) -> None:
        """
        Initialise la fabrique.

        Parameters
        ----------
        context:
            Contexte partagé injecté dans toutes les pages.
        """
        self._context = context

    @property
    def context(self) -> PageContext:
        """
        Retourne le contexte partagé.
        """
        return self._context

    def create(self, page_cls: type[T]) -> T:
        """
        Construit une nouvelle instance d'une page.

        Parameters
        ----------
        page_cls:
            Classe de la page à instancier.

        Returns
        -------
        T
            Instance de la page demandée.

        Raises
        ------
        TypeError
            Si la classe fournie n'hérite pas de BasePage.
        """
        if not issubclass(page_cls, BasePage):
            raise TypeError(
                f"{page_cls.__name__} doit hériter de BasePage."
            )

        return page_cls(self._context)
    
    
    
    

    

