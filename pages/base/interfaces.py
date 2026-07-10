"""
Contrats du Framework des Pages.

Ce module définit les interfaces publiques que doivent respecter
les différents éléments du Framework des Pages.

Une interface décrit uniquement le comportement attendu.
Elle ne contient aucune implémentation.

Toutes les pages du projet devront, directement ou indirectement,
respecter ces contrats.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Page(ABC):
    """
    Contrat commun à toutes les pages d'IRIS Copilot.

    Une page représente un écran fonctionnel de l'application.
    Toute implémentation doit être capable de rendre son contenu.
    """

    @abstractmethod
    def render(self) -> None:
        """
        Affiche le contenu de la page.

        Cette méthode constitue le point d'entrée principal
        du cycle de vie d'une page.
        """
        raise NotImplementedError