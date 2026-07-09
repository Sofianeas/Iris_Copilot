"""
Initialisation du registre des pages.

Ce module construit et initialise le registre central de
navigation de l'application.

Responsabilités
----------------
- Créer une instance de PageRegistry.
- Enregistrer les pages disponibles.
- Retourner un registre prêt à être utilisé.

Ce module constitue l'unique point d'enregistrement des
pages de l'application.
"""

from __future__ import annotations

from .registry import PageRegistry


def create_registry() -> PageRegistry:
    """
    Crée et initialise le registre des pages.

    Returns
    -------
    PageRegistry
        Registre contenant toutes les pages de l'application.
    """

    registry = PageRegistry()

    # -----------------------------------------------------------------
    # Enregistrement des pages
    #
    # Les appels à registry.register(Page(...)) seront ajoutés
    # progressivement au fur et à mesure du développement
    # des différentes pages métier.
    # -----------------------------------------------------------------

    return registry