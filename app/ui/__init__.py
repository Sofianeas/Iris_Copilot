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

# ==========================================================
# Forms
# ==========================================================

from .forms import (
    checkbox,
    date_input,
    file_uploader,
    form_submit_button,
    multiselect,
    number_input,
    radio,
    selectbox,
    slider,
    text_area,
    text_input,
    time_input,
    toggle,
)

# ==========================================================
# Icons
# ==========================================================

from .icons import (
    add,
    analytics,
    arrow_back,
    arrow_forward,
    attachment,
    calendar,
    cancel,
    check,
    close,
    dashboard,
    delete,
    download,
    edit,
    error,
    expand_less,
    expand_more,
    file,
    filter,
    folder,
    group,
    help,
    home,
    info,
    lock,
    mail,
    pause,
    person,
    phone,
    play,
    refresh,
    save,
    schedule,
    search,
    settings,
    stop,
    support,
    ticket,
    unlock,
    upload,
    visibility,
    warning,
)