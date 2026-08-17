# tests/repositories/test_in_memory_documentation_repository.py
#
# Tests de InMemoryDocumentationRepository (WF-DOC-014), première
# implémentation concrète de DocumentationRepository. Le test final
# démontre l'intégration réelle avec DocumentationWorkflow et
# VectorStoreDocumentationProvider (chemin prioritaire du fallback).

from app.models.documentation_workflow import DocumentationWorkflowRequest
from app.providers.vectorstore_documentation_provider import VectorStoreDocumentationProvider
from app.repositories.base_repository import BaseRepository
from app.repositories.documentation_repository import DocumentationRepository
from app.repositories.in_memory_documentation_repository import InMemoryDocumentationRepository
from app.services.vectorstore_service import construire_chunks, construire_vectorstore, make_tfidf_embedder
from app.workflows.documentation_workflow import DocumentationWorkflow


DONNEES_TEST = {
    "ADOPT": {
        "comment gerer une demande cato ?": "Voir Anne ou David via Teams (CDS Alger).",
    },
    "BARRON": {
        "que signifie ped chez ce client ?": "PED = TPE chez Barron Mac Cann.",
    },
}


# --------------------------------------------------------------------------
# 1-2 : instanciation et conformité
# --------------------------------------------------------------------------

def test_instantiable_et_conforme_au_contrat():
    repo = InMemoryDocumentationRepository()

    assert isinstance(repo, DocumentationRepository)
    assert isinstance(repo, BaseRepository)


# --------------------------------------------------------------------------
# 3 : save() puis get_by_id()
# --------------------------------------------------------------------------

def test_save_et_get_by_id_ne_levent_pas_conformes_au_contrat_de_base():
    """save()/get_by_id() ne sont pas exploitées par ce Repository (find_by_question est la voie utilisée), mais doivent rester appelables sans erreur, conformément au contrat BaseRepository."""
    repo = InMemoryDocumentationRepository()

    repo.save({"id": "x"})  # ne doit pas lever
    assert repo.get_by_id("x") is None


# --------------------------------------------------------------------------
# 4-5 : find_by_question avec résultat / question inexistante
# --------------------------------------------------------------------------

def test_find_by_question_avec_resultat():
    repo = InMemoryDocumentationRepository(donnees=DONNEES_TEST)

    reponse = repo.find_by_question("ADOPT", "Comment gerer une demande CATO ?")

    assert reponse == "Voir Anne ou David via Teams (CDS Alger)."


def test_find_by_question_normalisation_casse_et_espaces():
    repo = InMemoryDocumentationRepository(donnees=DONNEES_TEST)

    reponse = repo.find_by_question("ADOPT", "  COMMENT GERER UNE DEMANDE CATO ?  ")

    assert reponse == "Voir Anne ou David via Teams (CDS Alger)."


def test_find_by_question_question_inexistante_retourne_none():
    repo = InMemoryDocumentationRepository(donnees=DONNEES_TEST)

    reponse = repo.find_by_question("ADOPT", "Question totalement sans rapport")

    assert reponse is None


# --------------------------------------------------------------------------
# 6 : client inexistant
# --------------------------------------------------------------------------

def test_find_by_question_client_inexistant_retourne_none():
    repo = InMemoryDocumentationRepository(donnees=DONNEES_TEST)

    reponse = repo.find_by_question("CLIENT_INEXISTANT", "Comment gerer une demande CATO ?")

    assert reponse is None


# --------------------------------------------------------------------------
# 7 : isolation stricte entre clients
# --------------------------------------------------------------------------

def test_isolation_stricte_entre_clients():
    repo = InMemoryDocumentationRepository(donnees=DONNEES_TEST)

    # question ADOPT posee pour BARRON -> ne doit jamais repondre
    reponse = repo.find_by_question("BARRON", "Comment gerer une demande CATO ?")

    assert reponse is None


# --------------------------------------------------------------------------
# 8 : utilisation correcte des données injectées
# --------------------------------------------------------------------------

def test_donnees_injectees_utilisees_correctement():
    donnees_specifiques = {"CLIENT_X": {"question x": "reponse x specifique"}}
    repo = InMemoryDocumentationRepository(donnees=donnees_specifiques)

    assert repo.find_by_question("CLIENT_X", "question x") == "reponse x specifique"
    assert repo.find_by_question("ADOPT", "question x") is None  # donnees DONNEES_TEST non utilisees ici


def test_donnees_par_defaut_vides_si_non_injectees():
    repo = InMemoryDocumentationRepository()

    assert repo.find_by_question("ADOPT", "n'importe quoi") is None


# --------------------------------------------------------------------------
# 9 : absence de persistance externe
# --------------------------------------------------------------------------

def test_absence_de_persistance_externe_deux_instances_independantes():
    """Deux instances distinctes ne doivent jamais partager d'état -- confirme l'absence de fichier/DB partagé en arrière-plan."""
    repo_a = InMemoryDocumentationRepository(donnees={"ADOPT": {"q": "reponse A"}})
    repo_b = InMemoryDocumentationRepository(donnees={"ADOPT": {"q": "reponse B"}})

    assert repo_a.find_by_question("ADOPT", "q") == "reponse A"
    assert repo_b.find_by_question("ADOPT", "q") == "reponse B"


def test_mutation_du_dict_source_apres_injection_ne_pollue_pas_le_repository():
    """Le Repository copie les données injectées -- une mutation externe ultérieure du dict source ne doit pas se répercuter."""
    donnees_source = {"ADOPT": {"q": "reponse originale"}}
    repo = InMemoryDocumentationRepository(donnees=donnees_source)

    donnees_source["ADOPT"]["q"] = "reponse modifiee apres coup"

    assert repo.find_by_question("ADOPT", "q") == "reponse originale"


# --------------------------------------------------------------------------
# 10 : cohérence complète avec le contrat abstrait -- déjà couverte par
# les tests 1-9 ci-dessus (héritage vérifié, toutes les méthodes
# abstraites implémentées, isolation respectée).
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Test d'intégration réel : Workflow -> InMemoryDocumentationRepository
# -> VectorStoreDocumentationProvider. Scénario : Repository trouve la
# réponse -> Provider NON appelé.
# --------------------------------------------------------------------------

def test_integration_reelle_repository_trouve_provider_non_appele(tmp_path):
    # Repository concret réel, avec une vraie reponse pour ADOPT
    repository = InMemoryDocumentationRepository(donnees=DONNEES_TEST)

    # Provider concret réel, pointant vers un vectorstore construit a la
    # volee (TF-IDF, sans cle API) -- mais qui NE DOIT JAMAIS etre appele
    # dans ce scenario, puisque le Repository repond en premier.
    dossier_sources = tmp_path / "sources"
    dossier_sources.mkdir()
    (dossier_sources / "ADOPT.docx").write_text(
        "*Contrat : ne devrait jamais etre utilise pour cette question\n", encoding="utf-8"
    )
    dossier_persistance = tmp_path / "vectorstore"
    chunks = construire_chunks(dossier_sources)
    embedder = make_tfidf_embedder([c.texte for c in chunks])
    construire_vectorstore(dossier_sources, dossier_persistance, embed_fn=embedder)

    # Provider instrumenté pour detecter s'il a ete appele
    class ProviderTrace(VectorStoreDocumentationProvider):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.a_ete_appele = False

        def fetch(self, request):
            self.a_ete_appele = True
            return super().fetch(request)

    provider = ProviderTrace(dossier_persistance=dossier_persistance, embed_fn=embedder)
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="ADOPT", question="Comment gerer une demande CATO ?")
    )

    assert resultat.succes is True
    assert resultat.source == "repository"
    assert resultat.reponse == "Voir Anne ou David via Teams (CDS Alger)."
    assert provider.a_ete_appele is False  # le chemin prioritaire Repository a bien court-circuite le Provider