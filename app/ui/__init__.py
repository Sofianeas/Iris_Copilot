"""
IRIS Copilot
UI Library

Point d'entrée public du Design System.
Tous les composants UI doivent être importés depuis ce module.
"""

from __future__ import annotations

# ==========================================================
# Theme
# ==========================================================

from .theme import (
    load_theme,
    configure_page,
)

# ==========================================================
# Buttons
# ==========================================================

from .buttons import (
    button,
    primary_button,
    secondary_button,
    success_button,
    warning_button,
    danger_button,
)