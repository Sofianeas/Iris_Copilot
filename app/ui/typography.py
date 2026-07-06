"""
IRIS Copilot
Typography Components

Composants typographiques du Design System.
"""

from __future__ import annotations

import streamlit as st


def page_title(
    text: str,
    *,
    anchor: bool = False,
) -> None:
    """
    Affiche le titre principal d'une page.
    """
    st.title(text, anchor=anchor)


def section_title(
    text: str,
    *,
    anchor: bool = False,
) -> None:
    """
    Affiche le titre d'une section.
    """
    st.header(text, anchor=anchor)


def subtitle(
    text: str,
) -> None:
    """
    Affiche un sous-titre.
    """
    st.subheader(text)


def body_text(
    text: str,
) -> None:
    """
    Affiche un paragraphe.
    """
    st.write(text)


def caption(
    text: str,
) -> None:
    """
    Affiche une légende.
    """
    st.caption(text)


def code_block(
    code: str,
    *,
    language: str | None = None,
) -> None:
    """
    Affiche un bloc de code.
    """
    st.code(code, language=language)


def divider() -> None:
    """
    Affiche un séparateur horizontal.
    """
    st.divider()