"""
Configuration du Dashboard.

Toutes les constantes spécifiques au Dashboard
sont centralisées dans ce module.
"""
from .models import DashboardMetric, DashboardShortcut, DashboardActivity


DASHBOARD_TITLE = "IRIS Copilot"

DASHBOARD_SUBTITLE = (
    "Plateforme d'assistance au support informatique"
)

DASHBOARD_DESCRIPTION = (
    "Centralisez vos tickets, vos e-mails, votre documentation "
    "et vos outils d'assistance dans une interface unique."
)

WELCOME_MESSAGE = (
    "Bienvenue dans votre espace de travail."
)

DASHBOARD_SHORTCUTS: list[DashboardShortcut] = [
    DashboardShortcut(
        title="Analyse Mail",
        description="Analyser un e-mail SAV.",
        icon="📧",
        page_id="analyse_mail",
    ),
    DashboardShortcut(
        title="Documentation",
        description="Consulter la documentation.",
        icon="📚",
        page_id="documentation",
    ),
    DashboardShortcut(
        title="Historique",
        description="Consulter les tickets récents.",
        icon="🕘",
        page_id="historique",
    ),
    DashboardShortcut(
        title="Génération Ticket",
        description="Créer un ticket SAV.",
        icon="🎫",
        page_id="generation_ticket",
    ),
]

DASHBOARD_METRICS: list[DashboardMetric] = [

    DashboardMetric(
        label="Tickets ouverts",
        value="24",
    ),

    DashboardMetric(
        label="Mails analysés",
        value="156",
    ),

    DashboardMetric(
        label="Documentation",
        value="42",
    ),

    DashboardMetric(
        label="Agents IA",
        value="3",
    ),
]

DASHBOARD_ACTIVITY: list[DashboardActivity] = [
    DashboardActivity(
        title="Analyse Mail",
        description="Un e-mail SAV a été analysé.",
        timestamp="Il y a 5 minutes",
    ),
    DashboardActivity(
        title="Documentation",
        description="Documentation consultée.",
        timestamp="Il y a 18 minutes",
    ),
    DashboardActivity(
        title="Ticket",
        description="Nouveau ticket créé.",
        timestamp="Aujourd'hui",
    ),
]