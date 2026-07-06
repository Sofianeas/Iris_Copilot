"""
IRIS Copilot
Table Components

Composants réutilisables pour l'affichage de tableaux.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def data_table(
    data: pd.DataFrame | Any,
    *,
    width: str = "stretch",
    hide_index: bool = True,
) -> None:
    """
    Affiche un tableau de données.

    Parameters
    ----------
    data:
        Données à afficher.

    width:
        Largeur du tableau.
        Valeurs possibles :
        - "stretch"
        - "content"

    hide_index:
        Masque l'index.
    """

    st.dataframe(
        data,
        width=width,
        hide_index=hide_index,
    )