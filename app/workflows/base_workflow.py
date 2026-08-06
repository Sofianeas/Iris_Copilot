"""
app/workflows/base_workflow.py

Contrat officiel de tout Workflow du Framework (WF-000). Formalise
UNIQUEMENT le contrat public commun -- aucune logique métier, aucune
implémentation par défaut, aucune connaissance de ChromaDB/Gemini/OCR/UI/
d'un client particulier/Repository concret/Provider concret/Service
concret.

Générique (comme BaseRepository/BaseProvider) car chaque Workflow a des
entrées/sorties différentes -- contrairement à BaseAgent, qui a une forme
fixe (tous les Agents travaillent sur un Ticket).
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.models.workflow_contracts import WorkflowRequest, WorkflowResult

TRequest = TypeVar("TRequest", bound=WorkflowRequest)
TResult = TypeVar("TResult", bound=WorkflowResult)


class BaseWorkflow(ABC, Generic[TRequest, TResult]):
    """
    Contrat commun à tous les Workflows. Une seule méthode publique :
    `execute`. Comme pour BaseAgent/BaseRule, aucune autre méthode
    publique ne doit être ajoutée.

    Un Workflow :
      - possède une responsabilité unique (un seul cas d'usage métier) ;
      - orchestre des composants déjà existants (Services, Agents,
        Rules, Repositories, Providers) -- il ne réimplémente jamais
        leur logique ;
      - ne connaît jamais Streamlit, les Pages, les widgets ;
      - reçoit uniquement un `WorkflowRequest` (concret, spécifique au
        Workflow), retourne uniquement un `WorkflowResult` (concret,
        spécifique au Workflow).
    """

    @abstractmethod
    def execute(self, request: TRequest) -> TResult:
        """
        Exécute le Workflow sur `request` et retourne le résultat.
        Ne lève jamais d'exception métier non gérée vers l'appelant --
        toute erreur doit être reflétée dans le WorkflowResult concret
        (même convention que AgentResult.succes/erreur).
        """
        raise NotImplementedError