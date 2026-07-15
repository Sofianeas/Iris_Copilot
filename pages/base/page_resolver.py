"""
Résolution des pages du Framework.

Le PageResolver établit la correspondance entre les
identifiants de navigation et les implémentations
concrètes des pages.

Responsabilités
----------------
- Résoudre une classe de page à partir de son identifiant.
- Centraliser les correspondances.
- Ne créer aucune instance de page.

Le PageResolver constitue le point de liaison entre le
système de navigation et le Framework des Pages.
"""

from __future__ import annotations

from pages.dashboard.page import DashboardPage

from .base_page import BasePage


class PageResolver:
    """
    Résout une classe de page à partir de son identifiant.
    """

    def __init__(self) -> None:
        """
        Initialise le registre de résolution.
        """

        self._pages: dict[str, type[BasePage]] = {
            "dashboard": DashboardPage,
        }

    def resolve(self, page_id: str) -> type[BasePage]:
        """
        Retourne la classe correspondant à une page.

        Parameters
        ----------
        page_id:
            Identifiant de la page.

        Returns
        -------
        type[BasePage]

        Raises
        ------
        KeyError
            Si aucune page ne correspond à l'identifiant.
        """

        try:
            return self._pages[page_id]

        except KeyError as exc:
            raise KeyError(
                f"Aucune implémentation enregistrée pour '{page_id}'."
            ) from exc