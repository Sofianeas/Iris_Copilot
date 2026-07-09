"""
Application Framework - Shell.

Ce package regroupe les composants d'infrastructure
responsables du cycle de vie de l'application.

Responsabilités
----------------
- Initialiser le Framework.
- Orchestrer les composants du Shell.
- Exposer l'API publique du Shell.

Ce package ne contient aucune logique métier.
"""

from .app_shell import ApplicationShell

__all__ = (
    "ApplicationShell",
)