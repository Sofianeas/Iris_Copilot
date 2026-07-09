"""
Gestion centralisée de la session Streamlit.

Toutes les interactions avec ``st.session_state`` doivent
passer par ce module.

Responsabilités
----------------
- Initialiser la session.
- Lire une valeur.
- Écrire une valeur.
- Vérifier l'existence d'une clé.
- Supprimer une clé.
- Réinitialiser la session.

Aucune logique métier ne doit être implémentée ici.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


DEFAULT_SESSION = {
    "app": {},
    "user": {},
    "navigation": {},
    "workspace": {},
    "context": {},
}


class SessionManager:
    """
    Gestionnaire de la session applicative.

    Cette classe encapsule entièrement ``st.session_state`` afin
    d'éviter que le reste de l'application y accède directement.
    """

    def initialize(self) -> None:
        """
        Initialise les clés globales de la session.

        Les clés sont créées uniquement lors du premier lancement
        afin de ne jamais écraser les données déjà présentes.
        """
        for key, value in DEFAULT_SESSION.items():
            if key not in st.session_state:
                st.session_state[key] = value.copy()

    def exists(self, key: str) -> bool:
        """
        Vérifie si une clé existe dans la session.
        """
        return key in st.session_state

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retourne une valeur de la session.

        Parameters
        ----------
        key : str
            Nom de la clé.
        default : Any, optional
            Valeur par défaut si la clé n'existe pas.

        Returns
        -------
        Any
            Valeur stockée dans la session.
        """
        return st.session_state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Enregistre une valeur dans la session.
        """
        st.session_state[key] = value

    def delete(self, key: str) -> None:
        """
        Supprime une clé de la session.
        """
        if key in st.session_state:
            del st.session_state[key]

    def clear(self) -> None:
        """
        Vide entièrement la session.
        """
        st.session_state.clear()