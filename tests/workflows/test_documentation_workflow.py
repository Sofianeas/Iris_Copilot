# tests/workflows/test_documentation_workflow.py
#
# Suite officielle du DocumentationWorkflow raccordé par injection
# (WF-DOC-003). Utilise exclusivement des DOUBLES DE TEST (fakes)
# implémentant les interfaces abstraites DocumentationRepository /
# DocumentationProvider -- jamais une implémentation concrète, jamais
# ChromaDB/Gemini/SDK. Vérifie l'orchestration (Repository -> Provider en
# repli), la propagation des erreurs, et la compatibilité avec les
# contrats WorkflowRequest/WorkflowResult.
#
# Révisé lors de la consolidation technique (WF-DOC-004) : ajout de la
# vérification des arguments réellement transmis au Provider (absente
# auparavant), et renforcement du test de non-dépendance à une
# implémentation concrète.

from app.models.documentation_workflow import DocumentationWorkflowRequest, DocumentationWorkflowResult
from app.models.workflow_contracts import WorkflowRequest, WorkflowResult
from app.providers.documentation_provider import DocumentationProvider
from app.repositories.documentation_repository import DocumentationRepository
from app.workflows.documentation_workflow import DocumentationWorkflow


class FakeDocumentationRepository(DocumentationRepository):
    """Fake configurable : retourne une réponse fixe, None, ou lève une exception."""

    def __init__(self, reponse=None, leve_exception=False):
        self._reponse = reponse
        self._leve_exception = leve_exception
        self.appels = []

    def save(self, entity):
        pass

    def get_by_id(self, entity_id):
        return None

    def find_by_question(self, client, question):
        self.appels.append((client, question))
        if self._leve_exception:
            raise RuntimeError("panne simulee du repository")
        return self._reponse


class FakeDocumentationProvider(DocumentationProvider):
    """Fake configurable : retourne une réponse fixe, None, ou lève une exception."""

    def __init__(self, reponse=None, leve_exception=False):
        self._reponse = reponse
        self._leve_exception = leve_exception
        self.appels = []

    def fetch(self, request):
        self.appels.append(request)
        if self._leve_exception:
            raise RuntimeError("panne simulee du provider")
        return self._reponse


def test_injection_correcte_des_dependances():
    repository = FakeDocumentationRepository(reponse="reponse repo")
    provider = FakeDocumentationProvider()

    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    assert workflow._repository is repository
    assert workflow._provider is provider


def test_workflow_ne_depend_que_du_comportement_contractuel_des_fakes():
    """
    Renforcé (WF-DOC-004) : au lieu de vérifier une tautologie
    (isinstance d'un fake sur sa propre classe parente, garanti par
    construction), vérifie que le WORKFLOW se comporte correctement
    avec DEUX fakes totalement indépendants et interchangeables --
    preuve concrète qu'il ne dépend que du contrat abstrait, pas d'une
    implémentation particulière.
    """
    repository_a = FakeDocumentationRepository(reponse="reponse A")
    provider_a = FakeDocumentationProvider()
    workflow_a = DocumentationWorkflow(repository=repository_a, provider=provider_a)

    repository_b = FakeDocumentationRepository(reponse="reponse B")
    provider_b = FakeDocumentationProvider()
    workflow_b = DocumentationWorkflow(repository=repository_b, provider=provider_b)

    resultat_a = workflow_a.execute(DocumentationWorkflowRequest(client="ADOPT", question="q"))
    resultat_b = workflow_b.execute(DocumentationWorkflowRequest(client="ADOPT", question="q"))

    assert resultat_a.reponse == "reponse A"
    assert resultat_b.reponse == "reponse B"


def test_repository_trouve_une_reponse_provider_jamais_appele():
    repository = FakeDocumentationRepository(reponse="Voir Anne ou David via Teams.")
    provider = FakeDocumentationProvider(reponse="ne devrait jamais etre utilise")

    workflow = DocumentationWorkflow(repository=repository, provider=provider)
    resultat = workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="Comment gerer un CATO ?"))

    assert resultat.succes is True
    assert resultat.reponse == "Voir Anne ou David via Teams."
    assert resultat.source == "repository"
    assert provider.appels == []


def test_repository_ne_trouve_rien_fallback_vers_provider():
    repository = FakeDocumentationRepository(reponse=None)
    provider = FakeDocumentationProvider(reponse="reponse trouvee via le provider")

    workflow = DocumentationWorkflow(repository=repository, provider=provider)
    resultat = workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="Question rare"))

    assert resultat.succes is True
    assert resultat.reponse == "reponse trouvee via le provider"
    assert resultat.source == "provider"
    assert repository.appels == [("ADOPT", "Question rare")]
    assert provider.appels == [("ADOPT", "Question rare")]


def test_ni_repository_ni_provider_ne_trouvent_rien():
    repository = FakeDocumentationRepository(reponse=None)
    provider = FakeDocumentationProvider(reponse=None)

    workflow = DocumentationWorkflow(repository=repository, provider=provider)
    resultat = workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="Question inconnue"))

    assert resultat.succes is False
    assert resultat.reponse is None
    assert resultat.source is None
    assert "ADOPT" in resultat.erreur
    assert "Question inconnue" in resultat.erreur


def test_requete_avec_client_vide_est_rejetee_sans_appeler_les_dependances():
    repository = FakeDocumentationRepository(reponse="ne devrait jamais etre atteint")
    provider = FakeDocumentationProvider()

    workflow = DocumentationWorkflow(repository=repository, provider=provider)
    resultat = workflow.execute(DocumentationWorkflowRequest(client="", question="question valide"))

    assert resultat.succes is False
    assert "requis" in resultat.erreur.lower()
    assert repository.appels == []
    assert provider.appels == []


def test_requete_avec_question_vide_est_rejetee():
    repository = FakeDocumentationRepository()
    provider = FakeDocumentationProvider()

    workflow = DocumentationWorkflow(repository=repository, provider=provider)
    resultat = workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question=""))

    assert resultat.succes is False
    assert repository.appels == []


def test_exception_du_repository_est_capturee_et_encapsulee():
    repository = FakeDocumentationRepository(leve_exception=True)
    provider = FakeDocumentationProvider(reponse="ne devrait jamais etre atteint")

    workflow = DocumentationWorkflow(repository=repository, provider=provider)
    resultat = workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    assert resultat.succes is False
    assert "Repository" in resultat.erreur
    assert "panne simulee" in resultat.erreur
    assert provider.appels == []


def test_exception_du_provider_est_capturee_et_encapsulee():
    repository = FakeDocumentationRepository(reponse=None)
    provider = FakeDocumentationProvider(leve_exception=True)

    workflow = DocumentationWorkflow(repository=repository, provider=provider)
    resultat = workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    assert resultat.succes is False
    assert "Provider" in resultat.erreur
    assert "panne simulee" in resultat.erreur


def test_le_resultat_reste_compatible_avec_workflow_result():
    repository = FakeDocumentationRepository(reponse="reponse")
    provider = FakeDocumentationProvider()

    workflow = DocumentationWorkflow(repository=repository, provider=provider)
    resultat = workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))

    assert isinstance(resultat, DocumentationWorkflowResult)
    assert isinstance(resultat, WorkflowResult)


def test_la_requete_reste_compatible_avec_workflow_request():
    request = DocumentationWorkflowRequest(client="ADOPT", question="test")

    assert isinstance(request, WorkflowRequest)