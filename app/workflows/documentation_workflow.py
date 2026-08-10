"""
app/workflows/documentation_workflow.py

Implémentation du Workflow Documentation (WF-DOC-003), conforme au
contrat BaseWorkflow (WF-000). Raccordé par INJECTION à
DocumentationRepository et DocumentationProvider -- utilise
exclusivement leurs interfaces publiques abstraites, jamais une
implémentation concrète (aucun import ChromaDB/Gemini/SDK ici).

Orchestration volontairement minimale (aucune logique documentaire
métier), validée architecturalement : consulte le Repository (source
persistée et déterministe) en premier, puis le Provider (source externe,
repli) uniquement si rien n'a été trouvé. Le Workflow reste
l'orchestrateur -- il ne déplace jamais la responsabilité de ces
composants (aucune logique de recherche, aucun accès ChromaDB, aucun
appel LLM ici).

Gestion des erreurs (SD-007) : aucune exception ne sort jamais de
`execute()` -- toute erreur du Repository ou du Provider est capturée et
encapsulée dans DocumentationWorkflowResult.erreur.
"""

from app.models.documentation_workflow import DocumentationWorkflowRequest, DocumentationWorkflowResult
from app.providers.documentation_provider import DocumentationProvider
from app.repositories.documentation_repository import DocumentationRepository
from app.workflows.base_workflow import BaseWorkflow


class DocumentationWorkflow(BaseWorkflow[DocumentationWorkflowRequest, DocumentationWorkflowResult]):
    """
    Workflow Documentation : répond à une question sur la documentation
    d'un client, en orchestrant un DocumentationRepository et un
    DocumentationProvider reçus par injection -- n'implémente lui-même
    aucune logique de recherche, aucun accès ChromaDB, aucun appel LLM.
    """

    def __init__(self, repository: DocumentationRepository, provider: DocumentationProvider):
        """
        `repository`/`provider` doivent être des instances concrètes des
        interfaces abstraites DocumentationRepository/DocumentationProvider
        -- ce Workflow ne connaît et ne doit jamais connaître leur
        implémentation réelle (aucun import concret dans ce fichier).
        """
        self._repository = repository
        self._provider = provider

    def execute(self, request: DocumentationWorkflowRequest) -> DocumentationWorkflowResult:
        """
        Orchestre le Workflow Documentation :
          1. Valide le contrat d'entrée (client/question non vides).
          2. Consulte le Repository (find_by_question) -- source persistée.
          3. Si rien trouvé, consulte le Provider (fetch) -- repli externe.
          4. Construit un DocumentationWorkflowResult cohérent dans tous
             les cas (succès, absence de résultat, erreur contrôlée).

        Ne lève jamais d'exception métier non gérée (SD-007) -- toute
        erreur du Repository ou du Provider est capturée et reflétée
        dans `erreur`, conformément au contrat BaseWorkflow.
        """
        if not request.client or not request.question:
            return DocumentationWorkflowResult(
                succes=False, reponse=None, source=None,
                erreur="Requête invalide : 'client' et 'question' sont tous deux requis.",
            )

        try:
            reponse_repository = self._repository.find_by_question(request.client, request.question)
        except Exception as exc:
            return DocumentationWorkflowResult(
                succes=False, reponse=None, source=None,
                erreur=f"Erreur lors de la consultation du Repository : {exc!r}",
            )

        if reponse_repository is not None:
            return DocumentationWorkflowResult(succes=True, reponse=reponse_repository, source="repository")

        try:
            reponse_provider = self._provider.fetch((request.client, request.question))
        except Exception as exc:
            return DocumentationWorkflowResult(
                succes=False, reponse=None, source=None,
                erreur=f"Erreur lors de la consultation du Provider : {exc!r}",
            )

        if reponse_provider is not None:
            return DocumentationWorkflowResult(succes=True, reponse=reponse_provider, source="provider")

        return DocumentationWorkflowResult(
            succes=False, reponse=None, source=None,
            erreur=(
                f"Aucune réponse trouvée pour client={request.client!r}, "
                f"question={request.question!r} (ni Repository, ni Provider)."
            ),
        )