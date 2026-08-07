"""
app/workflows/documentation_workflow.py

Implémentation du Workflow Documentation (WF-DOC-001), conforme au
contrat BaseWorkflow (WF-000).

⚠️ ÉTAT ACTUEL : squelette d'orchestration uniquement. Aucun
VectorStoreProvider ni DocumentationRepository concret n'existe encore
dans le Framework -- `execute()` ne peut donc produire aucun résultat
documentaire réel à ce stade. Il retourne systématiquement un échec
explicite (succes=False, erreur=...) plutôt que de :
  - fabriquer une réponse ;
  - contourner la contrainte en appelant directement ChromaDB/
    vectorstore_service.py (interdit par la mission WF-DOC-001 :
    "aucune interaction avec ChromaDB", "aucun Provider concret") ;
  - simuler un comportement métier non encore implémenté.

Ce fichier constitue le point d'intégration officiel : quand un
VectorStoreProvider et/ou un DocumentationRepository concrets seront
créés (missions futures), `execute()` sera complété pour les orchestrer
-- sans que ce fichier lui-même n'ait besoin de changer de forme.
"""

from app.models.documentation_workflow import DocumentationWorkflowRequest, DocumentationWorkflowResult
from app.workflows.base_workflow import BaseWorkflow


class DocumentationWorkflow(BaseWorkflow[DocumentationWorkflowRequest, DocumentationWorkflowResult]):
    """
    Workflow Documentation : répond à une question sur la documentation
    d'un client. Orchestre (à terme) un VectorStoreProvider et/ou un
    DocumentationRepository -- n'implémente lui-même aucune logique de
    recherche, aucun accès ChromaDB, aucun appel LLM.
    """

    def execute(self, request: DocumentationWorkflowRequest) -> DocumentationWorkflowResult:
        """
        Orchestre le Workflow Documentation. À ce stade (aucun Provider/
        Repository concret disponible), retourne systématiquement un
        échec explicite et traçable.
        """
        return DocumentationWorkflowResult(
            succes=False,
            reponse=None,
            source=None,
            erreur=(
                f"DocumentationWorkflow n'a pas encore de Provider/Repository "
                f"concret branché (VectorStoreProvider, DocumentationRepository) "
                f"-- squelette de contrat uniquement, cf. WF-DOC-001. "
                f"Requête reçue : client={request.client!r}, question={request.question!r}."
            ),
        )