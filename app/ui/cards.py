"""
IRIS Copilot
UI Cards

Composants de cartes réutilisables.
"""

from __future__ import annotations

from .render import render_html


# ==========================================================
# Private helpers
# ==========================================================

def _render(html: str) -> None:
    """
    Affiche un composant HTML du Design System.
    """
    render_html(html)


# ==========================================================
# Metric Card
# ==========================================================

def metric_card(
    title: str,
    value: str | int | float,
    icon: str = "📊",
    help_text: str = "",
) -> None:
    """
    Affiche une carte de métrique.
    """
    _render(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-title">{title}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        """
    )


# ==========================================================
# Info Card
# ==========================================================

def info_card(
    title: str,
    content: str,
) -> None:
    """
    Affiche une carte d'information.
    """
    _render(
        f"""
        <div class="info-card">
            <h4>{title}</h4>
            <p>{content}</p>
        </div>
        """
    )


# ==========================================================
# Feature Card
# ==========================================================

def feature_card(
    title: str,
    description: str,
    icon: str = "✨",
) -> None:
    """
    Affiche une carte de fonctionnalité.
    """
    _render(
        f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
        """
    )


# ==========================================================
# Action Card
# ==========================================================

def action_card(
    label: str,
) -> None:
    """
    Affiche une carte d'action.
    """
    _render(
        f"""
        <div class="action-card">
            <strong>{label}</strong>
        </div>
        """
    )


# ==========================================================
# Stat Card
# ==========================================================

def stat_card(
    title: str,
    value: str | int | float,
    delta: str,
) -> None:
    """
    Affiche une statistique avec évolution.
    """
    _render(
        f"""
        <div class="stat-card">
            <div class="stat-value">{value}</div>
            <div class="stat-title">{title}</div>
            <div class="stat-delta">{delta}</div>
        </div>
        """
    )