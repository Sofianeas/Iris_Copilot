# tests/workflows/test_documentation_workflow_full_assembly.py
#
# Complète la Priorité A (WF-DOC-014, suite) : les 2 scénarios encore
# non couverts avec des composants concrets réels (pas de fake) :
#   1. InMemoryDocumentationRepository ne répond pas -> fallback réel
#      vers VectorStoreDocumentationProvider.
#   2. Comportement de distance_max dans la chaîne assemblée complète.
# Les autres scénarios de la Priorité A sont déjà couverts par
# test_documentation_workflow_integration_vectorstore.py (WF-DOC-012) et
# test_in_memory_documentation_repository.py (WF-DOC-014) -- non dupliqués ici.

import pytest

from app.models.documentation_workflow import DocumentationWorkflowRequest
from app.providers.vectorstore_documentation_provider import VectorStoreDocumentationProvider
from app.repositories.in_memory_documentation_repository import InMemoryDocumentationRepository
from app.services.vectorstore_service import construire_chunks, construire_vectorstore, make_tfidf_embedder
from app.workflows.documentation_workflow import DocumentationWorkflow


@pytest.fixture
def vectorstore_reel(tmp_path):
    dossier_sources = tmp_path / "sources"
    dossier_sources.mkdir()
    (dossier_sources / "ADOPT.docx").write_text(
        "Titre ignoré (avant le premier '*')\n"
        "*CATO : Installation Boîtier CATO nécessite une validation avec Anne ou David via Teams (CDS Alger)\n",
        encoding="utf-8",
    )
    dossier_persistance = tmp_path / "vectorstore"
    chunks = construire_chunks(dossier_sources)
    embedder = make_tfidf_embedder([c.texte for c in chunks])
    construire_vectorstore(dossier_sources, dossier_persistance, embed_fn=embedder)
    return dossier_persistance, embedder


def test_repository_reel_vide_fallback_reel_vers_provider(vectorstore_reel):
    """InMemoryDocumentationRepository (réel, vide pour cette question) -> fallback réel vers VectorStoreDocumentationProvider."""
    dossier_persistance, embedder = vectorstore_reel
    repository = InMemoryDocumentationRepository()  # vide -- aucune donnée injectée
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="ADOPT", question="Comment gérer une demande de boîtier CATO ?")
    )

    assert resultat.succes is True
    assert resultat.source == "provider"
    assert "CATO" in resultat.reponse


def test_distance_max_dans_la_chaine_assemblee_complete(vectorstore_reel):
    """distance_max trop strict, propagé jusqu'au DocumentationWorkflowResult final -- échec cohérent, pas de résultat peu pertinent."""
    dossier_persistance, embedder = vectorstore_reel
    repository = InMemoryDocumentationRepository()
    provider_strict = VectorStoreDocumentationProvider(
        dossier_persistance=dossier_persistance, embed_fn=embedder, distance_max=0.0001
    )
    workflow = DocumentationWorkflow(repository=repository, provider=provider_strict)

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="ADOPT", question="Comment gérer une demande de boîtier CATO ?")
    )

    assert resultat.succes is False
    assert resultat.reponse is None