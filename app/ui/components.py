"""
IRIS Copilot
UI Components

API publique officielle des composants UI.
Toutes les pages doivent importer leurs composants
uniquement depuis ce module.
"""

from __future__ import annotations

# ==========================================================
# Layout
# ==========================================================

from .layout import (
    hero,
    section,
    divider,
    footer,
    empty_state,
    page_title,
)

# ==========================================================
# Cards
# ==========================================================

from .cards import (
    metric_card,
    info_card,
    feature_card,
    action_card,
    stat_card,
)

# ==========================================================
# Badges
# ==========================================================

from .badges import (
    badge,
    badge_group,
)

# ==========================================================
# Alerts
# ==========================================================

from .alerts import (
    alert,
)

# ==========================================================
# Forms
# ==========================================================

# from .forms import *

# ==========================================================
# Tables
# ==========================================================

# from .tables import *

# ==========================================================
# Sidebar
# ==========================================================

# from .sidebar import *

# ==========================================================
# Icons
# ==========================================================

# from .icons import *

from .buttons import (
    button,
    primary_button,
)