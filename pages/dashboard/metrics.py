"""
Composant Metrics du Dashboard.

## Responsabilités

- Afficher les principaux indicateurs du Dashboard.

Aucune logique métier ne doit être implémentée ici.
"""

from __future__ import annotations

import streamlit as st

from .config import DASHBOARD_METRICS
from .models import DashboardMetric


def render_metrics() -> None:
    """
    Affiche les indicateurs du Dashboard.
    """

    st.subheader("Vue d'ensemble")

    columns = st.columns(len(DASHBOARD_METRICS))

    for column, metric in zip(columns, DASHBOARD_METRICS):
        with column:
            _render_metric(metric)


def _render_metric(metric: DashboardMetric) -> None:
    """
    Affiche un indicateur du Dashboard.
    """

    st.metric(
        label=metric.label,
        value=metric.value,
        help=metric.help,
    )