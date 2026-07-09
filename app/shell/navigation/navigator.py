"""
Gestion de la navigation de l'application.

Le Navigator est responsable de la page actuellement active.

Responsabilités
----------------
- Connaître la page courante.
- Changer de page.
- Fournir la page active.
- Utiliser exclusivement la couche Session pour
  persister l'état de navigation.

Le Navigator ne dépend ni de Streamlit, ni des pages
métier. Il s'appuie uniquement sur le registre des pages
et la couche Session.
"""

from __future__ import annotations

from app.shell import session

from .config import DEFAULT_PAGE_ID
from .models import Page
from .registry import PageRegistry


_SESSION_KEY = "current_page"


class Navigator:
    """
    Gestionnaire de la navigation de l'application.
    """

    def __init__(self, registry: PageRegistry) -> None:
        """
        Initialise le navigateur.

        Parameters
        ----------
        registry : PageRegistry
            Registre des pages disponibles.
        """
        self._registry = registry

        if not session.has(_SESSION_KEY):
            session.set(_SESSION_KEY, DEFAULT_PAGE_ID)

    def current_page_id(self) -> str:
        """
        Retourne l'identifiant de la page active.
        """
        return session.get(_SESSION_KEY)

    def current_page(self) -> Page:
        """
        Retourne la page actuellement sélectionnée.
        """
        return self._registry.get(self.current_page_id())

    def navigate(self, page_id: str) -> None:
        """
        Change la page active.

        Raises
        ------
        KeyError
            Si la page demandée n'existe pas.
        """
        self._registry.get(page_id)
        session.set(_SESSION_KEY, page_id)

    def reset(self) -> None:
        """
        Réinitialise la navigation sur la page par défaut.
        """
        session.set(_SESSION_KEY, DEFAULT_PAGE_ID)

def pages(self) -> tuple[Page, ...]:
    """
    Retourne les pages enregistrées.

    Returns
    -------
    tuple[Page, ...]
        Ensemble des pages disponibles.
    """
    return self._registry.get_all()