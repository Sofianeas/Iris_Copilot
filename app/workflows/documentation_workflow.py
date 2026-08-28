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

Observabilité (WF-DOC-016 / WF-003) : instrumentation minimale via le
module `logging` standard et mesure de durée via `time.perf_counter()`.
Aucune nouvelle abstraction d'observabilité n'est introduite.
"""

import logging
import time

from app.models.documentation_workflow import (
    DocumentationWorkflowRequest,
    DocumentationWorkflowResult,
)
from app.providers.documentation_provider import DocumentationProvider
from app.repositories.documentation_repository import DocumentationRepository
from app.workflows.base_workflow import BaseWorkflow


logger = logging.getLogger("iris_copilot.documentation_workflow")


class DocumentationWorkflow(
    BaseWorkflow[DocumentationWorkflowRequest, DocumentationWorkflowResult]
):
    """
    Workflow Documentation : répond à une question sur la documentation
    d'un client, en orchestrant un DocumentationRepository et un
    DocumentationProvider reçus par injection -- n'implémente lui-même
    aucune logique de recherche, aucun accès ChromaDB, aucun appel LLM.
    """

    def __init__(
        self,
        repository: DocumentationRepository,
        provider: DocumentationProvider,
    ):
        """
        `repository`/`provider` doivent être des instances concrètes des
        interfaces abstraites DocumentationRepository/DocumentationProvider
        -- ce Workflow ne connaît et ne doit jamais connaître leur
        implémentation réelle (aucun import concret dans ce fichier).
        """
        self._repository = repository
        self._provider = provider

    def execute(
        self,
        request: DocumentationWorkflowRequest,
    ) -> DocumentationWorkflowResult:
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

        L'instrumentation ajoutée ne modifie pas le comportement fonctionnel
        ni le contrat public de la méthode.
        """
        debut = time.perf_counter()

        logger.info(
            "execution_debut client=%r question=%r",
            request.client,
            request.question,
        )

        if not request.client or not request.question:
            duree_ms = (time.perf_counter() - debut) * 1000

            logger.warning(
                "requete_invalide client=%r question=%r duree_ms=%.3f",
                request.client,
                request.question,
                duree_ms,
            )

            return DocumentationWorkflowResult(
                succes=False,
                reponse=None,
                source=None,
                erreur="Requête invalide : 'client' et 'question' sont tous deux requis.",
            )

        try:
            reponse_repository = self._repository.find_by_question(
                request.client,
                request.question,
            )
        except Exception as exc:
            duree_ms = (time.perf_counter() - debut) * 1000

            logger.error(
                "execution_fin statut=echec composant=repository "
                "erreur=%r duree_ms=%.3f",
                exc,
                duree_ms,
            )

            return DocumentationWorkflowResult(
                succes=False,
                reponse=None,
                source=None,
                erreur=f"Erreur lors de la consultation du Repository : {exc!r}",
            )

        if reponse_repository is not None:
            duree_ms = (time.perf_counter() - debut) * 1000

            logger.info(
                "execution_fin statut=succes source=repository duree_ms=%.3f",
                duree_ms,
            )

            return DocumentationWorkflowResult(
                succes=True,
                reponse=reponse_repository,
                source="repository",
            )

        logger.info(
            "fallback_provider client=%r question=%r",
            request.client,
            request.question,
        )

        try:
            reponse_provider = self._provider.fetch(
                (request.client, request.question)
            )
        except Exception as exc:
            duree_ms = (time.perf_counter() - debut) * 1000

            logger.error(
                "execution_fin statut=echec composant=provider "
                "erreur=%r duree_ms=%.3f",
                exc,
                duree_ms,
            )

            return DocumentationWorkflowResult(
                succes=False,
                reponse=None,
                source=None,
                erreur=f"Erreur lors de la consultation du Provider : {exc!r}",
            )

        if reponse_provider is not None:
            duree_ms = (time.perf_counter() - debut) * 1000

            logger.info(
                "execution_fin statut=succes source=provider duree_ms=%.3f",
                duree_ms,
            )

            return DocumentationWorkflowResult(
                succes=True,
                reponse=reponse_provider,
                source="provider",
            )

        duree_ms = (time.perf_counter() - debut) * 1000

        logger.info(
            "execution_fin statut=echec raison=aucun_resultat duree_ms=%.3f",
            duree_ms,
        )

        return DocumentationWorkflowResult(
            succes=False,
            reponse=None,
            source=None,
            erreur=(
                f"Aucune réponse trouvée pour client={request.client!r}, "
                f"question={request.question!r} (ni Repository, ni Provider)."
            ),
        )

