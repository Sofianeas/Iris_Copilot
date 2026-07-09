"""
Configuration du système de navigation.

Ce module centralise l'ensemble des constantes utilisées par
le système de navigation de l'application.

Responsabilités
----------------
- Définir les paramètres globaux de navigation.
- Fournir les valeurs par défaut.
- Centraliser les catégories de navigation.

Ce module ne contient aucune logique métier et ne dépend
ni de Streamlit, ni du Shell, ni de la Session.
"""

# ---------------------------------------------------------------------
# Page par défaut
# ---------------------------------------------------------------------

DEFAULT_PAGE_ID = "dashboard"


# ---------------------------------------------------------------------
# Catégories de navigation
# ---------------------------------------------------------------------

CATEGORY_HOME = "Accueil"
CATEGORY_SUPPORT = "Support"
CATEGORY_DOCUMENTATION = "Documentation"
CATEGORY_ADMINISTRATION = "Administration"
CATEGORY_AI = "Intelligence Artificielle"


# ---------------------------------------------------------------------
# Ordre d'affichage des catégories
# ---------------------------------------------------------------------

CATEGORY_ORDER = (
    CATEGORY_HOME,
    CATEGORY_SUPPORT,
    CATEGORY_DOCUMENTATION,
    CATEGORY_ADMINISTRATION,
    CATEGORY_AI,
)