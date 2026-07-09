"""
Composant Activity du Dashboard.

## Responsabilités

- Afficher l'activité récente du Dashboard.

Aucune logique métier ne doit être implémentée ici.
"""

from __future__ import annotations

import streamlit as st

from .config import DASHBOARD_ACTIVITY
from .models import DashboardActivity


def render_activity() -> None:
    """
    Affiche l'activité récente du Dashboard.
    """

    st.subheader("Activité récente")

    for activity in DASHBOARD_ACTIVITY:
        _render_activity(activity)


def _render_activity(activity: DashboardActivity) -> None:
    """
    Affiche un événement de l'activité récente.
    """

    with st.container(border=True):
        st.markdown(f"**{activity.title}**")
        st.write(activity.description)
        st.caption(activity.timestamp)