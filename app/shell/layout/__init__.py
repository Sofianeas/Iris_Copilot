"""
API publique du package Layout.

Ce package regroupe les composants constituant le Layout
global de l'application.

Les modules internes restent masqués afin que le reste
de l'application utilise uniquement les interfaces
publiques exposées ici.
"""

from .layout import Layout

__all__ = (
    "Layout",
)