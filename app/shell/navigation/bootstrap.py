"""
Initialisation du registre des pages.

Ce module construit et initialise le registre central de
navigation de l'application.

Responsabilités
----------------
- Créer une instance de PageRegistry.
- Enregistrer les métadonnées des pages.
- Retourner un registre prêt à être utilisé.

Ce module ne connaît pas les implémentations concrètes des
pages. Il manipule uniquement les modèles de navigation.
"""

from __future__ import annotations

from .config import (
    CATEGORY_HOME,
    DEFAULT_PAGE_ID,
)
from .models import Page
from .registry import PageRegistry


def create_registry() -> PageRegistry:
    """
    Crée et initialise le registre des pages.

    Returns
    -------
    PageRegistry
        Registre contenant toutes les pages de navigation.
    """

    registry = PageRegistry()

    registry.register(
        Page(
            id=DEFAULT_PAGE_ID,
            title="Dashboard",
            icon="🏠",
            category=CATEGORY_HOME,
            description="Tableau de bord principal d'IRIS Copilot.",
            visible=True,
        )
    )

    return registry