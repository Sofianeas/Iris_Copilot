"""
IRIS Copilot
Timeline Components

Composants réutilisables pour l'affichage d'une chronologie.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def timeline(events: list[dict[str, Any]]) -> None:
    """
    Affiche une chronologie verticale.

    Parameters
    ----------
    events:
        Liste d'événements.

        Chaque événement peut contenir :

        - title (obligatoire)
        - timestamp (optionnel)
        - description (optionnelle)
    """

    if not events:
        st.info("Aucun événement.")
        return

    for index, event in enumerate(events):
        with st.container():
            st.markdown(f"**● {event['title']}**")

            if timestamp := event.get("timestamp"):
                st.caption(timestamp)

            if description := event.get("description"):
                st.write(description)

        if index < len(events) - 1:
            st.divider()