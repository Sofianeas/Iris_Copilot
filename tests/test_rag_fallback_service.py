# tests/test_rag_fallback_service.py
#
# pytest (convention spécifique à ce module RAG -- les autres tests du
# projet restent des scripts `python -m tests.<module>`, cf. README/
# conventions existantes). Lancer avec : pytest tests/test_rag_fallback_service.py -v

import chromadb
import pytest

from app.services.rag_fallback_service import RagResult, tenter_fallback_rag
from app.services.vectorstore_service import make_tfidf_embedder

# --------------------------------------------------------------------------
# Corpus de test minimal, contrôlé -- ne réutilise PAS les vraies sources du
# projet (déjà couvertes par tests/test_vectorstore.py) : ce fichier teste
# la logique PROPRE de rag_fallback_service.py (sélection du meilleur
# candidat, seuil, contrat RagResult), pas le chunking.
# --------------------------------------------------------------------------

CORPUS_TEST = {
    "TESTCLIENT": [
        ("procedures.docx", "docx", "Le contrat applicable pour TESTCLIENT est OD.TEST.001 - On Demand France."),
        ("procedures.docx", "docx", "La procedure de remplacement necessite un formulaire signe par le client."),
        ("toki_test.txt", "toki", "Horaires d'intervention : du lundi au vendredi, de 9h a 17h."),
    ],
    "AUTRECLIENT": [
        ("autre.docx", "docx", "AUTRECLIENT utilise toujours le contrat MAINTENANCE FRANCE, sans exception."),
    ],
}


@pytest.fixture
def vectorstore_prepare(tmp_path):
    """
    Construit un mini-vectorstore de test (2 clients, quelques chunks
    connus) dans un dossier temporaire pytest (`tmp_path`, nettoyé
    automatiquement). Retourne (dossier_persistance, embed_fn) -- le MÊME
    embed_fn (vectorizer déjà entraîné) doit être réutilisé pour toute
    requête ultérieure dans le test, cf. avertissement de
    vectorstore_service.make_tfidf_embedder.
    """
    tous_les_textes = [texte for chunks in CORPUS_TEST.values() for (_src, _type, texte) in chunks]
    embed_fn = make_tfidf_embedder(tous_les_textes)

    store = chromadb.PersistentClient(path=str(tmp_path))
    for client, chunks in CORPUS_TEST.items():
        collection = store.create_collection(client.lower())
        textes = [texte for (_src, _type, texte) in chunks]
        collection.add(
            ids=[f"{client}-{i}" for i in range(len(chunks))],
            documents=textes,
            embeddings=embed_fn(textes),
            metadatas=[{"client": client, "source": src, "type_source": t} for (src, t, _texte) in chunks],
        )
    return tmp_path, embed_fn


# --------------------------------------------------------------------------
# 1. Document trouvé
# --------------------------------------------------------------------------

def test_document_trouve(vectorstore_prepare):
    """Une question dont la réponse existe clairement dans le corpus -> found=True, valeur et source correctes."""
    dossier, embed_fn = vectorstore_prepare
    resultat = tenter_fallback_rag("TESTCLIENT", "quel est le contrat applicable", dossier, embed_fn=embed_fn)

    assert resultat.found is True
    assert "OD.TEST.001" in resultat.value
    assert resultat.source == "docx:procedures.docx"
    assert resultat.chunk_id is not None
    assert resultat.score is not None and 0.0 < resultat.score <= 1.0


# --------------------------------------------------------------------------
# 2. Plusieurs documents (sélection du meilleur parmi plusieurs candidats)
# --------------------------------------------------------------------------

def test_plusieurs_documents_meilleur_candidat_retenu(vectorstore_prepare):
    """
    TESTCLIENT a 3 chunks distincts (contrat / procédure / horaires) --
    une requête sur les horaires doit retourner LE chunk horaires, pas un
    autre candidat même s'il est aussi renvoyé par ChromaDB (n_candidats=3
    par défaut interroge tous les chunks du client).
    """
    dossier, embed_fn = vectorstore_prepare
    resultat = tenter_fallback_rag("TESTCLIENT", "quels sont les horaires d'intervention", dossier, embed_fn=embed_fn)

    assert resultat.found is True
    assert "9h" in resultat.value and "17h" in resultat.value
    assert resultat.source == "docx:procedures.docx" or resultat.source == "toki:toki_test.txt"
    # Le chunk horaires vient bien du fichier toki_test.txt (index 2 -> id "TESTCLIENT-2")
    assert resultat.chunk_id == "TESTCLIENT-2"


def test_plusieurs_documents_isolation_stricte_par_client(vectorstore_prepare):
    """
    TESTCLIENT et AUTRECLIENT ont chacun leur propre contrat -- une requête
    identique sur les 2 clients doit retourner 2 réponses DIFFÉRENTES,
    chacune fidèle à SA collection, jamais un mélange/une fuite croisée.
    """
    dossier, embed_fn = vectorstore_prepare
    resultat_a = tenter_fallback_rag("TESTCLIENT", "quel contrat", dossier, embed_fn=embed_fn)
    resultat_b = tenter_fallback_rag("AUTRECLIENT", "quel contrat", dossier, embed_fn=embed_fn)

    assert "OD.TEST.001" in resultat_a.value
    assert "MAINTENANCE FRANCE" in resultat_b.value
    assert "MAINTENANCE FRANCE" not in resultat_a.value
    assert "OD.TEST.001" not in resultat_b.value
    assert resultat_a.source != resultat_b.source


# --------------------------------------------------------------------------
# 3. Aucun document
# --------------------------------------------------------------------------

def test_aucun_document_client_sans_collection(vectorstore_prepare):
    """Client jamais ingéré (aucune collection ChromaDB) -> found=False, jamais d'exception."""
    dossier, embed_fn = vectorstore_prepare
    resultat = tenter_fallback_rag("CLIENT_SANS_DOC", "n'importe quelle question", dossier, embed_fn=embed_fn)

    assert resultat == RagResult(found=False, value=None, source=None, score=None, chunk_id=None)


# --------------------------------------------------------------------------
# 4. Score insuffisant
# --------------------------------------------------------------------------

def test_score_insuffisant_seuil_explicite(vectorstore_prepare):
    """
    Même requête que test_document_trouve, mais avec un score_min
    délibérément trop élevé pour être atteint -> found=False malgré
    l'existence d'un candidat techniquement récupéré par ChromaDB. Vérifie
    que le seuil est réellement appliqué, pas seulement documenté.
    """
    dossier, embed_fn = vectorstore_prepare
    resultat_permissif = tenter_fallback_rag(
        "TESTCLIENT", "quel est le contrat applicable", dossier, embed_fn=embed_fn, score_min=0.0
    )
    resultat_strict = tenter_fallback_rag(
        "TESTCLIENT", "quel est le contrat applicable", dossier, embed_fn=embed_fn, score_min=0.99
    )

    assert resultat_permissif.found is True  # même requête, seuil permissif -> trouvé
    assert resultat_strict.found is False  # seuil quasi impossible à atteindre -> rejeté
    assert resultat_strict.value is None
    assert resultat_strict.source is None


# --------------------------------------------------------------------------
# 5. None-safe (jamais d'exception, quel que soit l'état du vectorstore)
# --------------------------------------------------------------------------

def test_none_safe_dossier_jamais_construit(tmp_path):
    """Dossier de persistance qui n'a jamais été construit du tout -> found=False, jamais d'exception."""
    dossier_jamais_construit = tmp_path / "jamais_construit"
    embed_fn = make_tfidf_embedder(["texte quelconque pour entrainer le vectorizer"])

    resultat = tenter_fallback_rag("TESTCLIENT", "question", dossier_jamais_construit, embed_fn=embed_fn)

    assert resultat == RagResult(found=False, value=None, source=None, score=None, chunk_id=None)


def test_none_safe_metadata_absente(tmp_path):
    """
    Collection ChromaDB peuplée SANS métadonnées (cas anormal, ex. bug
    d'ingestion futur) -> found=False plutôt qu'une exception -- le
    contrat "found=True => source renseignée" doit primer sur la
    disponibilité brute d'un chunk texte.
    """
    textes = ["un chunk sans metadata associee"]
    embed_fn = make_tfidf_embedder(textes)
    store = chromadb.PersistentClient(path=str(tmp_path))
    collection = store.create_collection("clientsansmeta")
    collection.add(ids=["x"], documents=textes, embeddings=embed_fn(textes))  # pas de metadatas=

    resultat = tenter_fallback_rag("CLIENTSANSMETA", "question", tmp_path, embed_fn=embed_fn)

    assert resultat.found is False
    assert resultat.value is None
    assert resultat.source is None


# --------------------------------------------------------------------------
# 6. Aucune hallucination (extraction verbatim, jamais de paraphrase)
# --------------------------------------------------------------------------

def test_aucune_hallucination_extrait_verbatim(vectorstore_prepare):
    """
    La valeur retournée doit être un extrait VERBATIM d'un chunk réellement
    indexé -- jamais un texte généré/paraphrasé/absent du corpus source.
    """
    dossier, embed_fn = vectorstore_prepare
    resultat = tenter_fallback_rag("TESTCLIENT", "quel est le contrat applicable", dossier, embed_fn=embed_fn)

    textes_source_connus = [texte for (_src, _type, texte) in CORPUS_TEST["TESTCLIENT"]]
    assert resultat.value in textes_source_connus, (
        "La valeur retournée n'est pas un extrait verbatim d'un chunk connu -- "
        "risque d'hallucination ou de paraphrase non tracée."
    )


def test_found_false_implique_tous_les_champs_none(vectorstore_prepare):
    """Invariant du contrat RagResult : found=False => value/source/score/chunk_id TOUS None (aucune valeur partielle)."""
    dossier, embed_fn = vectorstore_prepare
    resultat = tenter_fallback_rag("CLIENT_INEXISTANT", "question", dossier, embed_fn=embed_fn)

    assert resultat.found is False
    assert resultat.value is None
    assert resultat.source is None
    assert resultat.score is None
    assert resultat.chunk_id is None