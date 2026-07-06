"""
IRIS Copilot
Button Components

Composants de boutons réutilisables du Design System.
"""

from __future__ import annotations

import streamlit as st


def _button(
    *,
    label: str,
    variant: str,
    icon: str | None = None,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    full_width: bool = False,
) -> bool:
    """
    Fonction interne utilisée par toutes les variantes de boutons.

    Parameters
    ----------
    label:
        Texte affiché.
    variant:
        Variante visuelle.
    icon:
        Icône optionnelle.
    key:
        Clé Streamlit.
    help:
        Tooltip.
    disabled:
        Désactive le bouton.
    full_width:
        Étend le bouton sur toute la largeur disponible.

    Returns
    -------
    bool
        True si le bouton est cliqué.
    """

    return st.button(
        label=label,
        icon=icon,
        key=key,
        help=help,
        disabled=disabled,
        use_container_width=full_width,
        type="primary" if variant == "primary" else "secondary",
    )


def primary_button(
    label: str,
    *,
    icon: str | None = None,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    full_width: bool = False,
) -> bool:
    """
    Bouton principal.
    """

    return _button(
        label=label,
        variant="primary",
        icon=icon,
        key=key,
        help=help,
        disabled=disabled,
        full_width=full_width,
    )


def secondary_button(
    label: str,
    *,
    icon: str | None = None,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    full_width: bool = False,
) -> bool:
    """
    Bouton secondaire.
    """

    return _button(
        label=label,
        variant="secondary",
        icon=icon,
        key=key,
        help=help,
        disabled=disabled,
        full_width=full_width,
    )

def success_button(
    label: str,
    *,
    icon: str | None = None,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    full_width: bool = False,
) -> bool:
    """
    Bouton destiné aux actions positives.
    """

    return _button(
        label=label,
        variant="success",
        icon=icon,
        key=key,
        help=help,
        disabled=disabled,
        full_width=full_width,
    )


def warning_button(
    label: str,
    *,
    icon: str | None = None,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    full_width: bool = False,
) -> bool:
    """
    Bouton destiné aux actions nécessitant une attention particulière.
    """

    return _button(
        label=label,
        variant="warning",
        icon=icon,
        key=key,
        help=help,
        disabled=disabled,
        full_width=full_width,
    )


def danger_button(
    label: str,
    *,
    icon: str | None = None,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    full_width: bool = False,
) -> bool:
    """
    Bouton destiné aux actions destructives ou critiques.
    """

    return _button(
        label=label,
        variant="danger",
        icon=icon,
        key=key,
        help=help,
        disabled=disabled,
        full_width=full_width,
    )

# Alias conservé pour compatibilité
button = secondary_button