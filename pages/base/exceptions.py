"""
Exceptions du Framework des Pages.

Toutes les exceptions spécifiques au Framework des Pages
doivent être définies dans ce module.

L'objectif est de fournir des erreurs explicites, cohérentes
et spécialisées plutôt que d'utiliser des exceptions génériques.
"""

from __future__ import annotations


class PageError(Exception):
    """
    Exception de base du Framework des Pages.

    Toutes les exceptions spécifiques au Framework héritent
    de cette classe.
    """


class PageConfigurationError(PageError):
    """
    Levée lorsqu'une page est mal configurée.
    """


class PageInitializationError(PageError):
    """
    Levée lorsqu'une page ne peut pas être initialisée.
    """


class PageRenderError(PageError):
    """
    Levée lorsqu'une erreur survient pendant le rendu
    d'une page.
    """