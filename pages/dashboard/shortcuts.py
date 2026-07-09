"""
Composant Shortcuts du Dashboard.

## Responsabilités

- Afficher les raccourcis du Dashboard.
- Présenter les principaux modules de l'application.

Aucune logique métier ne doit être implémentée ici.
"""

from __future__ import annotations

import streamlit as st

from .config import DASHBOARD_SHORTCUTS
from .models import DashboardShortcut


def render_shortcuts() -> None:
    """
    Affiche les raccourcis du Dashboard.
    """

    st.subheader("Accès rapides")

    columns = st.columns(2)

    for index, shortcut in enumerate(DASHBOARD_SHORTCUTS):
        with columns[index % 2]:
            _render_shortcut(shortcut)


def _render_shortcut(shortcut: DashboardShortcut) -> None:
    """
    Affiche un raccourci du Dashboard.
    """

    with st.container(border=True):
        st.markdown(f"### {shortcut.icon} {shortcut.title}")
        st.write(shortcut.description)