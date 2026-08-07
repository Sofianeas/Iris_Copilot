# tests/workflows/test_documentation_workflow.py
#
# Tests du premier Workflow concret du Framework. Vérifie le contrat
# (héritage des marqueurs WorkflowRequest/WorkflowResult, conformité
# BaseWorkflow) et le comportement HONNÊTE de execute() en l'absence de
# Provider/Repository concret (cf. WF-DOC-001) -- ne teste aucune vraie
# logique documentaire, puisqu'aucune n'existe encore.

from app.models.documentation_workflow import DocumentationWorkflowRequest, DocumentationWorkflowResult
from app.models.workflow_contracts import WorkflowRequest, WorkflowResult
from app.workflows.base_workflow import BaseWorkflow
from app.workflows.documentation_workflow import DocumentationWorkflow


def test_documentation_workflow_request_herite_du_marqueur_commun():
    request = DocumentationWorkflowRequest(client="ADOPT", question="test")

    assert isinstance(request, WorkflowRequest)


def test_documentation_workflow_result_herite_du_marqueur_commun():
    result = DocumentationWorkflowResult(succes=True, reponse="test", source="test")

    assert isinstance(result, WorkflowResult)


def test_documentation_workflow_est_bien_un_base_workflow():
    workflow = DocumentationWorkflow()

    assert isinstance(workflow, BaseWorkflow)


def test_documentation_workflow_execute_retourne_un_echec_explicite():
    """Aucun Provider/Repository concret n'existe encore -- execute() ne doit jamais fabriquer une réponse."""
    workflow = DocumentationWorkflow()
    request = DocumentationWorkflowRequest(client="ADOPT", question="Comment gérer un CATO ?")

    resultat = workflow.execute(request)

    assert resultat.succes is False
    assert resultat.reponse is None
    assert resultat.source is None
    assert resultat.erreur is not None


def test_documentation_workflow_execute_erreur_trace_la_requete_recue():
    """L'erreur doit rester traçable -- mentionne le client et la question reçus, utile pour le debug."""
    workflow = DocumentationWorkflow()
    request = DocumentationWorkflowRequest(client="BARRON", question="Question specifique test")

    resultat = workflow.execute(request)

    assert "BARRON" in resultat.erreur
    assert "Question specifique test" in resultat.erreur


def test_documentation_workflow_execute_ne_leve_jamais_exception():
    """Conforme au contrat BaseWorkflow : jamais d'exception métier non gérée vers l'appelant."""
    workflow = DocumentationWorkflow()
    request = DocumentationWorkflowRequest(client="", question="")

    resultat = workflow.execute(request)  # ne doit pas lever, même avec une requête vide

    assert resultat.succes is False