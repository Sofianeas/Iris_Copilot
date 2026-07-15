"""
Modèles de navigation.

Ce module définit les structures de données utilisées par le
système de navigation de l'application.

Responsabilités
----------------
- Définir les modèles de navigation.
- Fournir des objets immuables représentant les pages.
- Ne contenir aucune logique métier.

Les modèles de navigation décrivent uniquement les
métadonnées nécessaires au système de navigation.
Ils ne connaissent ni le Framework des Pages, ni Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Page:
    """
    Métadonnées d'une page de navigation.

    Cette classe représente uniquement une entrée du registre
    de navigation. Elle ne contient aucun comportement et ne
    référence aucune implémentation concrète de page.
    """

    id: str
    title: str
    icon: str

    category: str = "General"
    description: str = ""
    visible: bool = True