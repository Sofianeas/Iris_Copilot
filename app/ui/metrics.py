"""
IRIS Copilot
Metric Components

Composants réutilisables pour l'affichage de métriques.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def metric(
    label: str,
    value: Any,
    delta: str | None = None,
    help: str | None = None,
) -> None:
    """
    Affiche une métrique standard.

    Parameters
    ----------
    label:
        Nom de la métrique.

    value:
        Valeur affichée.

    delta:
        Variation affichée sous la valeur.

    help:
        Texte affiché au survol.
    """

    st.metric(
        label=label,
        value=value,
        delta=delta,
        help=help,
    )


def metric_row(
    metrics: list[dict[str, Any]],
    columns: int | None = None,
) -> None:
    """
    Affiche plusieurs métriques sur une ligne.

    Parameters
    ----------
    metrics:
        Liste de dictionnaires contenant les paramètres
        acceptés par ``metric()``.

    columns:
        Nombre de colonnes à afficher.
        Si None, une colonne par métrique.
    """

    if not metrics:
        return

    n_columns = columns or len(metrics)
    cols = st.columns(n_columns)

    for col, item in zip(cols, metrics, strict=False):
        with col:
            metric(
                label=item["label"],
                value=item["value"],
                delta=item.get("delta"),
                help=item.get("help"),
            )