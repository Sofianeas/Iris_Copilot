# tests/workflows/test_documentation_workflow_observability.py
#
# WF-DOC-016 -- Vérifie l'instrumentation logging ajoutée à
# DocumentationWorkflow.execute() : identifiant/statut/durée/branche
# empruntée/erreurs (WF-003), via `logging` standard uniquement (aucune
# nouvelle abstraction, OBS-001 reste une dette connue -- ceci n'est pas
# le Framework d'Observabilité formel, seulement une instrumentation
# minimale compatible avec).

import logging

from app.models.documentation_workflow import DocumentationWorkflowRequest
from app.repositories.documentation_repository import DocumentationRepository
from app.providers.documentation_provider import DocumentationProvider
from app.workflows.documentation_workflow import DocumentationWorkflow


class _RepoConfigurable(DocumentationRepository):
    def __init__(self, reponse=None, leve_exception=False):
        self._reponse = reponse
        self._leve_exception = leve_exception

    def save(self, entity):
        pass

    def get_by_id(self, entity_id):
        return None

    def find_by_question(self, client, question):
        if self._leve_exception:
            raise RuntimeError("panne repo")
        return self._reponse


class _ProviderConfigurable(DocumentationProvider):
    def __init__(self, reponse=None, leve_exception=False):
        self._reponse = reponse
        self._leve_exception = leve_exception

    def fetch(self, request):
        if self._leve_exception:
            raise RuntimeError("panne provider")
        return self._reponse


def test_log_execution_debut_et_succes_repository(caplog):
    workflow = DocumentationWorkflow(repository=_RepoConfigurable(reponse="reponse"), provider=_ProviderConfigurable())

    with caplog.at_level(logging.INFO, logger="iris_copilot.documentation_workflow"):
        workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    messages = [r.message for r in caplog.records]
    assert any("execution_debut" in m and "ADOPT" in m for m in messages)
    assert any("statut=succes" in m and "source=repository" in m for m in messages)


def test_log_fallback_vers_provider_et_succes(caplog):
    workflow = DocumentationWorkflow(repository=_RepoConfigurable(reponse=None), provider=_ProviderConfigurable(reponse="reponse provider"))

    with caplog.at_level(logging.INFO, logger="iris_copilot.documentation_workflow"):
        workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    messages = [r.message for r in caplog.records]
    assert any("fallback_provider" in m for m in messages)
    assert any("statut=succes" in m and "source=provider" in m for m in messages)


def test_log_aucun_resultat(caplog):
    workflow = DocumentationWorkflow(repository=_RepoConfigurable(reponse=None), provider=_ProviderConfigurable(reponse=None))

    with caplog.at_level(logging.INFO, logger="iris_copilot.documentation_workflow"):
        workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    messages = [r.message for r in caplog.records]
    assert any("statut=echec" in m and "aucun_resultat" in m for m in messages)


def test_log_erreur_repository_niveau_error(caplog):
    workflow = DocumentationWorkflow(repository=_RepoConfigurable(leve_exception=True), provider=_ProviderConfigurable())

    with caplog.at_level(logging.INFO, logger="iris_copilot.documentation_workflow"):
        workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    erreurs = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(erreurs) == 1
    assert "composant=repository" in erreurs[0].message


def test_log_erreur_provider_niveau_error(caplog):
    workflow = DocumentationWorkflow(repository=_RepoConfigurable(reponse=None), provider=_ProviderConfigurable(leve_exception=True))

    with caplog.at_level(logging.INFO, logger="iris_copilot.documentation_workflow"):
        workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    erreurs = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(erreurs) == 1
    assert "composant=provider" in erreurs[0].message


def test_log_requete_invalide_niveau_warning(caplog):
    workflow = DocumentationWorkflow(repository=_RepoConfigurable(), provider=_ProviderConfigurable())

    with caplog.at_level(logging.INFO, logger="iris_copilot.documentation_workflow"):
        workflow.execute(DocumentationWorkflowRequest(client="", question="test"))

    avertissements = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avertissements) == 1
    assert "requete_invalide" in avertissements[0].message


def test_log_contient_une_duree_mesuree(caplog):
    """Vérifie qu'une durée (duree_ms) est bien présente dans le log de fin -- exigence WF-003."""
    workflow = DocumentationWorkflow(repository=_RepoConfigurable(reponse="r"), provider=_ProviderConfigurable())

    with caplog.at_level(logging.INFO, logger="iris_copilot.documentation_workflow"):
        workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    messages_fin = [r.message for r in caplog.records if "execution_fin" in r.message]
    assert len(messages_fin) == 1
    assert "duree_ms=" in messages_fin[0]


def test_contrat_public_inchange_aucune_regression_comportementale():
    """Non-régression : le comportement fonctionnel (pas seulement les logs) reste strictement identique après instrumentation."""
    workflow = DocumentationWorkflow(repository=_RepoConfigurable(reponse="reponse repo"), provider=_ProviderConfigurable(reponse="ne doit pas être utilisé"))

    resultat = workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    assert resultat.succes is True
    assert resultat.reponse == "reponse repo"
    assert resultat.source == "repository"