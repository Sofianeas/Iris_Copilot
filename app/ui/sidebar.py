"""
IRIS Copilot
Sidebar Components

Composants réutilisables pour la barre latérale.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import streamlit as st


@contextmanager
def sidebar() -> Iterator[None]:
    """
    Fournit un contexte d'écriture dans la barre latérale.
    """

    with st.sidebar:
        yield


def sidebar_title(text: str) -> None:
    """
    Affiche un titre dans la barre latérale.
    """

    st.sidebar.title(text)


def sidebar_section(text: str) -> None:
    """
    Affiche un en-tête de section dans la barre latérale.
    """

    st.sidebar.subheader(text)


def sidebar_text(text: str) -> None:
    """
    Affiche un texte dans la barre latérale.
    """

    st.sidebar.write(text)


def sidebar_divider() -> None:
    """
    Affiche un séparateur dans la barre latérale.
    """

    st.sidebar.divider()