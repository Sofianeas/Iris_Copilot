"""
Application Shell.

Ce module contient l'orchestrateur principal de l'application
IRIS Copilot.

Responsabilités
----------------
- Initialiser le cycle de vie de l'application.
- Orchestrer les composants du Shell.
- Construire l'interface globale.
- Coordonner les différentes couches du Framework.

Le Shell ne contient aucune logique métier.
"""

from __future__ import annotations

from .layout import Layout
from .navigation import Navigator, PageRegistry, create_registry
from .session import SessionManager


class ApplicationShell:
    """
    Orchestrateur principal de l'application.

    Cette classe est responsable du cycle de vie de
    l'application. Elle coordonne les différentes briques
    du Framework (Session, Navigation, Layout...).

    Aucune logique métier ne doit être implémentée ici.
    """

    def __init__(self) -> None:
        """
        Initialise le Shell et ses composants.
        """
        self._initialized = False

        # Infrastructure
        self.session: SessionManager = SessionManager()
        self.registry: PageRegistry = create_registry()
        self.navigator: Navigator = Navigator(self.registry)
        self.layout: Layout = Layout(self.navigator)

    def initialize(self) -> None:
        """
        Initialise les composants du Shell.

        Cette méthode sera enrichie progressivement
        au fil des prochaines étapes de la roadmap.
        """
        self.session.initialize()
        self._initialized = True

    def configure(self) -> None:
        """
        Configure les éléments globaux de l'application.

        Cette méthode accueillera progressivement
        la configuration globale du Framework.
        """
        pass

    def build(self) -> None:
        """
        Construit l'interface globale de l'application.
        """
        self.layout.render()

    def run(self) -> None:
        """
        Lance le cycle de vie complet de l'application.

        Ordre d'exécution
        -----------------
        1. Initialisation
        2. Configuration
        3. Construction de l'interface
        """
        if not self._initialized:
            self.initialize()

        self.configure()
        self.build()