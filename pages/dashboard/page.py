"""
Dashboard principal d'IRIS Copilot.

Responsabilités
---------------
- Orchestrer les composants du Dashboard.
- Construire la page d'accueil.
- Ne contient aucune logique métier.

Les différents composants (header, metrics, shortcuts,
activity, etc.) sont responsables de leur propre affichage.
"""

from .activity import render_activity
from .header import render_header
from .metrics import render_metrics
from .shortcuts import render_shortcuts


class DashboardPage:
    """
    Page d'accueil principale.

    Cette classe orchestre les différentes sections du Dashboard.
    """

    def render(self) -> None:
        """
        Construit la page complète.
        """

        self._render_sections()

    def _render_sections(self) -> None:
        """
        Orchestre les différentes sections du Dashboard.
        """

        render_header()
        render_metrics()
        render_shortcuts()
        render_activity()