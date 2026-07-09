"""
Registre central des pages de l'application.

Ce module fournit la source unique de vérité des pages
disponibles dans l'application.

Responsabilités
----------------
- Enregistrer les pages.
- Rechercher une page.
- Vérifier l'existence d'une page.
- Retourner la liste des pages enregistrées.
- Garantir l'unicité des identifiants.

Ce module ne dépend ni de Streamlit, ni de la Session,
ni du Shell. Il manipule uniquement les modèles de
navigation.
"""

from __future__ import annotations

from .models import Page


class PageRegistry:
    """
    Registre central des pages.
    """

    def __init__(self) -> None:
        """Initialise un registre vide."""
        self._pages: dict[str, Page] = {}

    def register(self, page: Page) -> None:
        """
        Enregistre une nouvelle page.

        Raises
        ------
        ValueError
            Si l'identifiant ou le titre est vide.
        KeyError
            Si une page avec le même identifiant existe déjà.
        """
        if not page.id.strip():
            raise ValueError("Le champ 'id' d'une page ne peut pas être vide.")

        if not page.title.strip():
            raise ValueError("Le champ 'title' d'une page ne peut pas être vide.")

        if page.id in self._pages:
            raise KeyError(
                f"Une page avec l'identifiant '{page.id}' est déjà enregistrée."
            )

        self._pages[page.id] = page

    def get(self, page_id: str) -> Page:
        """
        Retourne une page à partir de son identifiant.

        Raises
        ------
        KeyError
            Si la page n'existe pas.
        """
        return self._pages[page_id]

    def get_all(self) -> tuple[Page, ...]:
        """
        Retourne toutes les pages enregistrées.

        Returns
        -------
        tuple[Page, ...]
            Collection immuable des pages.
        """
        return tuple(self._pages.values())

    def exists(self, page_id: str) -> bool:
        """
        Indique si une page est enregistrée.
        """
        return page_id in self._pages

    def clear(self) -> None:
        """
        Supprime toutes les pages du registre.
        """
        self._pages.clear()