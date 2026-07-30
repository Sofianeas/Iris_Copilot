"""
app/providers/base_provider.py

Contrat commun de tout Provider du Framework Métier (P3-440.0).
Infrastructure PURE -- aucune implémentation concrète, aucun Provider
métier (GeminiProvider, VectorStoreProvider, etc.) n'est créé dans cette
mission.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class BaseProvider(ABC, Generic[TInput, TOutput]):
    """
    Contrat commun de tout Provider. Un Provider encapsule l'accès à une
    SOURCE DE DONNÉES EXTERNE (API LLM, vectorstore, service tiers...) --
    il :
      - ne connaît jamais l'implémentation concrète au niveau du contrat
        (Gemini, ChromaDB, une future API Outlook...) ;
      - ne contient aucune logique métier ;
      - ne connaît jamais Streamlit, les Pages, les widgets ;
      - ne modifie jamais un état métier (Ticket ou autre) -- il se
        contente de récupérer une donnée externe et de la retourner.

    ⚠️ Proposition à valider (cf. mission P3-440.0) : signature générique
    à 2 paramètres de type (`TInput`/`TOutput`) pour couvrir aussi bien un
    GeminiProvider (`str -> str`) qu'un futur VectorStoreProvider (requête
    -> liste de résultats) sans figer une forme unique -- à confirmer ou
    simplifier selon les besoins réels des premières implémentations
    concrètes. Alternative possible : un seul TypeVar si la diversité des
    Providers futurs s'avère plus homogène que prévu.
    """

    @abstractmethod
    def fetch(self, request: TInput) -> TOutput:
        """Interroge la source externe et retourne le résultat. Ne modifie jamais d'état métier."""
        raise NotImplementedError