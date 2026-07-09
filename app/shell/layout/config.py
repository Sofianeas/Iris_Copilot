"""
Configuration du Layout global.

Ce module centralise l'ensemble des paramètres utilisés par
le système de mise en page de l'application.

Responsabilités
----------------
- Définir les paramètres globaux du Layout.
- Centraliser les options d'affichage.
- Fournir les valeurs par défaut.

Ce module ne contient aucune logique métier et ne dépend
ni de Streamlit, ni du Shell, ni des pages métier.
"""

# ---------------------------------------------------------------------
# Affichage des zones du Layout
# ---------------------------------------------------------------------

SHOW_HEADER = True
SHOW_SIDEBAR = True
SHOW_WORKSPACE = True
SHOW_FOOTER = False


# ---------------------------------------------------------------------
# Configuration de la Sidebar
# ---------------------------------------------------------------------

SIDEBAR_STATE = "expanded"


# ---------------------------------------------------------------------
# Configuration du Workspace
# ---------------------------------------------------------------------

WORKSPACE_TITLE = "Workspace"


# ---------------------------------------------------------------------
# Configuration du Header
# ---------------------------------------------------------------------

APPLICATION_TITLE = "IRIS Copilot"
APPLICATION_ICON = "🛠️"


# ---------------------------------------------------------------------
# Configuration du Footer
# ---------------------------------------------------------------------

APPLICATION_VERSION = "0.1.0"