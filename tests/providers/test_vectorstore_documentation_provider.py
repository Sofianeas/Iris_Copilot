# tests/providers/test_vectorstore_documentation_provider.py
#
# Tests de l'adaptateur VectorStoreDocumentationProvider (WF-DOC-011).
# Construit un vectorstore ChromaDB réel mais MINIMAL à la volée, via
# make_tfidf_embedder (stand-in de test documenté dans
# vectorstore_service.py, aucune clé API requise). Ne modifie jamais
# vectorstore_service.py lui-même.

import pytest

from app.providers.base_provider import BaseProvider
from app.providers.documentation_provider import DocumentationProvider
from app.providers.vectorstore_documentation_provider import VectorStoreDocumentationProvider
from app.services.vectorstore_service import construire_chunks, construire_vectorstore, make_tfidf_embedder


@pytest.fixture
def vectorstore_test(tmp_path):
    """Construit un mini-vectorstore réel pour le client ADOPT, avec le stand-in TF-IDF (pas de clé API)."""
    dossier_sources = tmp_path / "sources"
    dossier_sources.mkdir()
    (dossier_sources / "ADOPT.docx").write_text(
        "Titre du document ignoré (avant le premier '*')\n"
        "*Contrat : On Demand France pour les interventions en France standard\n"
        "*CATO : Installation Boîtier CATO nécessite une validation avec Anne ou David via Teams (CDS Alger)\n"
        "*Technicien anglophone : Non si intervention en France, Oui sinon\n",
        encoding="utf-8",
    )
    dossier_persistance = tmp_path / "vectorstore"

    chunks = construire_chunks(dossier_sources)
    corpus = [c.texte for c in chunks]
    embedder = make_tfidf_embedder(corpus)
    construire_vectorstore(dossier_sources, dossier_persistance, embed_fn=embedder)

    return dossier_persistance, embedder


# --------------------------------------------------------------------------
# Instanciation et conformité au contrat
# --------------------------------------------------------------------------

def test_provider_instantiable(tmp_path):
    provider = VectorStoreDocumentationProvider(dossier_persistance=tmp_path / "vectorstore_vide")

    assert isinstance(provider, DocumentationProvider)
    assert isinstance(provider, BaseProvider)


# --------------------------------------------------------------------------
# fetch() sur un vectorstore réel
# --------------------------------------------------------------------------

def test_fetch_retourne_le_chunk_le_plus_pertinent(vectorstore_test):
    dossier_persistance, embedder = vectorstore_test
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)

    reponse = provider.fetch(("ADOPT", "Comment gérer une demande de boîtier CATO ?"))

    assert reponse is not None
    assert "CATO" in reponse


def test_fetch_isolation_stricte_par_client(vectorstore_test):
    """Un client jamais ingéré (pas de collection ChromaDB) doit retourner None, jamais une recherche cross-client."""
    dossier_persistance, embedder = vectorstore_test
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)

    reponse = provider.fetch(("CLIENT_JAMAIS_INGERE", "Comment gérer une demande de boîtier CATO ?"))

    assert reponse is None


def test_fetch_reutilise_le_meme_embedder_que_la_construction(vectorstore_test):
    """Documente/vérifie explicitement l'exigence : le même embed_fn (même espace vectoriel) doit être utilisé pour la construction ET la requête."""
    dossier_persistance, embedder = vectorstore_test
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)

    # Fonctionne car `embedder` est EXACTEMENT le même objet que celui
    # utilisé lors de construire_vectorstore() dans la fixture.
    reponse = provider.fetch(("ADOPT", "technicien parle anglais ?"))

    assert reponse is not None  # ne lève aucune erreur de dimension d'embedding


# --------------------------------------------------------------------------
# Limitation connue, documentée explicitement (cf. docstring du module) :
# aucun filtrage par pertinence -- une question sans rapport retourne
# quand même un chunk (le moins éloigné), jamais None, tant que le client
# a une collection.
# --------------------------------------------------------------------------

def test_limitation_connue_question_sans_rapport_retourne_quand_meme_un_chunk(vectorstore_test):
    """
    Documente la limitation explicitement signalée dans le docstring du
    module : ce Provider ne filtre PAS par pertinence -- une question
    totalement sans rapport avec le corpus indexé retourne quand même un
    résultat (le chunk le moins éloigné), pas None. Un filtrage par score
    est un raffinement futur, non traité ici.
    """
    dossier_persistance, embedder = vectorstore_test
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)

    reponse = provider.fetch(("ADOPT", "Question totalement sans rapport avec ADOPT, ex. recette de cuisine"))

    # Comportement actuel ATTENDU (pas idéal) : un chunk est quand même retourné.
    assert reponse is not None