"""
IRIS Copilot
Navigation Components

Composants réutilisables pour la navigation.
"""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st


def breadcrumbs(items: Sequence[str]) -> None:
    """
    Affiche un fil d'Ariane.

    Parameters
    ----------
    items:
        Liste ordonnée des éléments du fil d'Ariane.
    """

    if not items:
        return

    st.caption(" › ".join(items))


def tabs(names: Sequence[str]) -> list:
    """
    Crée une série d'onglets.

    Parameters
    ----------
    names:
        Noms des onglets.

    Returns
    -------
    list
        Liste des conteneurs Streamlit correspondant aux onglets.
    """

    return st.tabs(list(names))


def nav_group(title: str) -> None:
    """
    Affiche un groupe de navigation.

    Parameters
    ----------
    title:
        Nom du groupe.
    """

    st.subheader(title)


def nav_link(label: str) -> None:
    """
    Affiche un élément de navigation.

    Cette première version est volontairement simple.
    Les futures versions pourront ajouter une icône,
    un état actif ou un lien réel.

    Parameters
    ----------
    label:
        Libellé du lien.
    """

    st.write(f"• {label}")