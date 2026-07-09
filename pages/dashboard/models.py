"""
Modèles du Dashboard.

Décrit les structures de données utilisées
par les composants du Dashboard.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardShortcut:
    """
    Représente un raccourci affiché sur le Dashboard.
    """

    title: str
    description: str
    icon: str
    page_id: str



@dataclass(frozen=True)
class DashboardMetric:
    """
    Représente un indicateur affiché sur le Dashboard.
    """

    label: str
    value: str
    help: str | None = None


@dataclass(frozen=True)
class DashboardActivity:
    """
    Représente un événement affiché dans
    l'activité récente du Dashboard.
    """

    title: str
    description: str
    timestamp: str