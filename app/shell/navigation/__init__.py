"""
API publique du système de navigation.

Ce package fournit l'ensemble des composants nécessaires à la
gestion de la navigation de l'application.

Les modules internes restent encapsulés afin de garantir une
API stable pour le reste du projet.
"""

from .models import Page
from .navigator import Navigator
from .registry import PageRegistry

__all__ = (
    "Navigator",
    "Page",
    "PageRegistry",
)