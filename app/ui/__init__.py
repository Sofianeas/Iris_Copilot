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

# ==========================================================
# Typography
# ==========================================================

from .typography import (
    page_title,
    section_title,
    subtitle,
    body_text,
    caption,
    code_block,
    divider,
)

# ==========================================================
# Metrics
# ==========================================================

from .metrics import (
    metric,
    metric_row,
)

# ==========================================================
# Tables
# ==========================================================

from .tables import (
    data_table,
)

# ==========================================================
# Timeline
# ==========================================================

from .timeline import (
    timeline,
)

# ==========================================================
# Sidebar
# ==========================================================

from .sidebar import (
    sidebar,
    sidebar_divider,
    sidebar_section,
    sidebar_text,
    sidebar_title,
)

# ==========================================================
# Navigation
# ==========================================================

from .navigation import (
    breadcrumbs,
    nav_group,
    nav_link,
    tabs,
)