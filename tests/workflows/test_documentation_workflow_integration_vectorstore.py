# tests/workflows/test_documentation_workflow_integration_vectorstore.py
#
# WF-DOC-012 -- Démontre l'assemblage RÉEL et complet :
#   DocumentationWorkflowRequest -> DocumentationWorkflow ->
#   DocumentationRepository (démonstrateur, test-only) -> fallback ->
#   VectorStoreDocumentationProvider -> vectorstore_service (ChromaDB réel,
#   construit à la volée avec le stand-in TF-IDF, sans clé API) ->
#   DocumentationWorkflowResult.
#
# Aucune fondation gelée modifiée. Le Repository utilisé ici est un
# DÉMONSTRATEUR défini localement dans ce fichier de test -- ce n'est PAS
# un composant de production (cf. contrainte WF-DOC-012 point 6).

import pytest

from app.models.documentation_workflow import DocumentationWorkflowRequest
from app.providers.vectorstore_documentation_provider import VectorStoreDocumentationProvider
from app.repositories.documentation_repository import DocumentationRepository
from app.services.vectorstore_service import construire_chunks, construire_vectorstore, make_tfidf_embedder
from app.workflows.documentation_workflow import DocumentationWorkflow


# --------------------------------------------------------------------------
# Repository démonstrateur -- STRICTEMENT limité à ce fichier de test,
# jamais destiné à la production (cf. contrainte WF-DOC-012 point 6).
# --------------------------------------------------------------------------

class RepositoryDemonstrateurVide(DocumentationRepository):
    """
    Démonstrateur test-only : retourne toujours None, pour forcer le
    fallback vers le Provider concret et démontrer l'assemblage complet.
    Aucune persistance réelle, aucun usage prévu hors de ce fichier.
    """

    def save(self, entity):
        pass

    def get_by_id(self, entity_id):
        return None

    def find_by_question(self, client, question):
        return None


@pytest.fixture
def vectorstore_reel(tmp_path):
    """Construit un vrai vectorstore ChromaDB (stand-in TF-IDF, aucune clé API) pour le client ADOPT."""
    dossier_sources = tmp_path / "sources"
    dossier_sources.mkdir()
    (dossier_sources / "ADOPT.docx").write_text(
        "Titre ignoré (avant le premier '*')\n"
        "*Contrat : On Demand France pour les interventions standard en France\n"
        "*CATO : Installation Boîtier CATO nécessite une validation avec Anne ou David via Teams (CDS Alger)\n"
        "*Technicien anglophone : Non si intervention en France, Oui sinon\n",
        encoding="utf-8",
    )
    dossier_persistance = tmp_path / "vectorstore"

    chunks = construire_chunks(dossier_sources)
    embedder = make_tfidf_embedder([c.texte for c in chunks])
    construire_vectorstore(dossier_sources, dossier_persistance, embed_fn=embedder)

    return dossier_persistance, embedder


# --------------------------------------------------------------------------
# 1. Question documentaire connue -> résultat concret via l'assemblage complet
# --------------------------------------------------------------------------

def test_assemblage_complet_question_connue_retourne_un_resultat_concret(vectorstore_reel):
    dossier_persistance, embedder = vectorstore_reel
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)
    repository = RepositoryDemonstrateurVide()
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="ADOPT", question="Comment gérer une demande de boîtier CATO ?")
    )

    assert resultat.succes is True
    assert resultat.source == "provider"  # confirme le passage par le fallback (point 2)
    assert "CATO" in resultat.reponse


# --------------------------------------------------------------------------
# 3. Client inexistant -> comportement cohérent
# --------------------------------------------------------------------------

def test_assemblage_complet_client_inexistant_comportement_coherent(vectorstore_reel):
    dossier_persistance, embedder = vectorstore_reel
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)
    repository = RepositoryDemonstrateurVide()
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="CLIENT_JAMAIS_INGERE", question="Question quelconque")
    )

    assert resultat.succes is False
    assert resultat.reponse is None
    assert "CLIENT_JAMAIS_INGERE" in resultat.erreur


# --------------------------------------------------------------------------
# 4. Erreur du Provider -> encapsulation conforme au contrat
# --------------------------------------------------------------------------

def test_assemblage_complet_erreur_provider_est_encapsulee(vectorstore_reel):
    dossier_persistance, _embedder = vectorstore_reel

    def embed_fn_casse(textes):
        raise RuntimeError("panne simulee de l'embedder")

    provider_casse = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embed_fn_casse)
    repository = RepositoryDemonstrateurVide()
    workflow = DocumentationWorkflow(repository=repository, provider=provider_casse)

    resultat = workflow.execute(DocumentationWorkflowRequest(client="ADOPT", question="test"))  # ne doit pas lever

    assert resultat.succes is False
    assert "Provider" in resultat.erreur
    assert "panne simulee" in resultat.erreur


# --------------------------------------------------------------------------
# 5-6. Réponse finale correctement encapsulée, sans transformation
# --------------------------------------------------------------------------

def test_assemblage_complet_reponse_non_transformee(vectorstore_reel):
    dossier_persistance, embedder = vectorstore_reel
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)
    repository = RepositoryDemonstrateurVide()
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    # Chunk brut directement obtenu depuis le Provider, pour comparaison bit a bit
    chunk_attendu = provider.fetch(("ADOPT", "Le technicien parle-t-il anglais ?"))

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="ADOPT", question="Le technicien parle-t-il anglais ?")
    )

    assert resultat.reponse == chunk_attendu  # identique bit a bit -- aucune transformation par le Workflow


# --------------------------------------------------------------------------
# 9. Le Workflow ne connaît rien de ChromaDB/embeddings/recherche vectorielle
# --------------------------------------------------------------------------

def test_workflow_ne_connait_rien_de_chromadb_ni_des_embeddings():
    """
    Vérification structurelle correcte : inspecte les IMPORTS réels du
    module (via ast), pas son texte brut -- une recherche de sous-chaîne
    sur le fichier entier capturerait aussi les docstrings explicatives
    (qui mentionnent légitimement "ChromaDB" en prose pour documenter son
    absence), produisant un faux positif.
    """
    import ast
    import inspect

    from app.workflows import documentation_workflow

    source = inspect.getsource(documentation_workflow)
    arbre = ast.parse(source)

    modules_importes = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            for alias in noeud.names:
                modules_importes.add(alias.name.split(".")[0])
        elif isinstance(noeud, ast.ImportFrom) and noeud.module:
            modules_importes.add(noeud.module.split(".")[0])

    modules_interdits = {"chromadb", "sklearn", "google"}
    intersection = modules_importes & modules_interdits

    assert not intersection, (
        f"documentation_workflow.py importe {intersection} -- le Workflow ne "
        f"doit connaître que les interfaces abstraites, jamais un SDK concret."
    )
    # Confirme aussi positivement que les imports réels restent bien
    # circonscrits aux couches abstraites du Framework.
    assert modules_importes <= {"app"}