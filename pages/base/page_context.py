"""
Contexte partagé du Framework des Pages.

Le PageContext regroupe les dépendances communes dont une page
peut avoir besoin durant son cycle de vie.

Il constitue le point d'entrée unique entre le Framework de
l'application et les implémentations concrètes des pages.

Le contexte ne contient aucune logique métier.
Il transporte uniquement les services et ressources partagés.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PageContext:
    """
    Contexte d'exécution d'une page.

    Les attributs seront enrichis progressivement au fur et à mesure
    de l'évolution du Framework (navigation, session, services, etc.).
    """

    navigator: Any | None = None
    session: Any | None = None
    services: Any | None = None