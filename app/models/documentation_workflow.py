"""
app/models/documentation_workflow.py

Contrats publics du Workflow Documentation (WF-DOC-001). Aucune logique
métier, aucune dépendance ChromaDB/Provider/Repository/UI/LLM.

Hérite de WorkflowRequest/WorkflowResult (app/models/workflow_contracts.py,
WF-000) -- nécessaire pour que DocumentationWorkflow puisse hériter de
BaseWorkflow[DocumentationWorkflowRequest, DocumentationWorkflowResult].

⚠️ Portée : ces contrats couvrent une REQUÊTE documentaire (client +
question -> réponse + source), cas d'usage le plus proche de l'existant
(`rag_fallback_service.tenter_fallback_rag`), plutôt qu'une ingestion de
nouveaux documents. Si le Workflow Documentation doit aussi couvrir
l'ingestion, un contrat séparé sera probablement nécessaire.
"""

from dataclasses import dataclass

from app.models.workflow_contracts import WorkflowRequest, WorkflowResult


@dataclass(frozen=True)
class DocumentationWorkflowRequest(WorkflowRequest):
    """
    Requête d'entrée du Workflow Documentation.

    Attributs :
        client : le client dont la documentation doit être interrogée
            (isolation stricte par client, cf. conventions déjà établies
            pour le RAG -- jamais de recherche cross-client).
        question : la question posée en langage naturel.
    """

    client: str
    question: str


@dataclass(frozen=True)
class DocumentationWorkflowResult(WorkflowResult):
    """
    Résultat du Workflow Documentation.

    Attributs :
        succes : indique si une réponse documentaire a pu être produite.
        reponse : la réponse trouvée, ou None si succes=False.
        source : la source documentaire ayant produit la réponse (fichier
            + section, cf. principe de traçabilité déjà établi pour le
            RAG), ou None si succes=False.
        erreur : message d'erreur lisible si succes=False, sinon None.
    """

    succes: bool
    reponse: str | None
    source: str | None
    erreur: str | None = None