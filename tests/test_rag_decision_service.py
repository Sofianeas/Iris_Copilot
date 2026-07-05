# tests/test_rag_decision_service.py
#
# pytest. Objectif : 100% des branches de evaluer_resultat() (cf.
# docstring de rag_decision_service.py pour l'ordre des 7 critères).
# Lancer avec : pytest tests/test_rag_decision_service.py -v

import pytest

import app.config.rag_settings as rag_settings
from app.services.rag_decision_service import evaluer_resultat
from app.services.rag_fallback_service import RagResult

RESULTAT_VALIDE = RagResult(
    found=True, value="Le contrat est OD.TEST.001", source="docx:procedures.docx",
    score=0.75, chunk_id="TESTCLIENT-0",
)


def test_resultat_valide_toutes_conditions_satisfaites():
    """Cas nominal : tous les critères passent -> usable=True, raison explicite, result echoed."""
    decision = evaluer_resultat(RESULTAT_VALIDE)

    assert decision.usable is True
    assert decision.reason == "tous_criteres_satisfaits"
    assert decision.result == RESULTAT_VALIDE


def test_configuration_desactivee(monkeypatch):
    """ENABLE_RAG=False -> usable=False immédiatement, même avec un résultat par ailleurs parfaitement valide."""
    monkeypatch.setattr(rag_settings, "ENABLE_RAG", False)

    decision = evaluer_resultat(RESULTAT_VALIDE)

    assert decision.usable is False
    assert "rag_desactive" in decision.reason


def test_resultat_non_trouve():
    """found=False -> usable=False, raison explicite (résultat non vide = 1er critère métier après ENABLE_RAG)."""
    resultat = RagResult(found=False, value=None, source=None, score=None, chunk_id=None)

    decision = evaluer_resultat(resultat)

    assert decision.usable is False
    assert decision.reason == "resultat_non_trouve"


def test_valeur_absente():
    """found=True mais value manquante -> usable=False, raison 'valeur_absente'."""
    resultat = RagResult(found=True, value=None, source="docx:x.docx", score=0.9, chunk_id="id-1")

    decision = evaluer_resultat(resultat)

    assert decision.usable is False
    assert decision.reason == "valeur_absente"


def test_source_absente():
    """found=True, value présente, mais source manquante -> usable=False, raison 'source_absente'."""
    resultat = RagResult(found=True, value="un extrait valide", source=None, score=0.9, chunk_id="id-1")

    decision = evaluer_resultat(resultat)

    assert decision.usable is False
    assert decision.reason == "source_absente"


def test_chunk_absent():
    """found=True, value/source présentes, mais chunk_id manquant -> usable=False, raison 'chunk_absent'."""
    resultat = RagResult(found=True, value="un extrait valide", source="docx:x.docx", score=0.9, chunk_id=None)

    decision = evaluer_resultat(resultat)

    assert decision.usable is False
    assert decision.reason == "chunk_absent"


def test_score_insuffisant(monkeypatch):
    """Tout est présent, mais score < MIN_SCORE (config) -> usable=False, raison mentionne 'score_insuffisant'."""
    monkeypatch.setattr(rag_settings, "MIN_SCORE", 0.5)  # sans ceci, 0.1 >= MIN_SCORE par défaut (0.0) et passerait
    resultat = RagResult(found=True, value="un extrait valide", source="docx:x.docx", score=0.1, chunk_id="id-1")

    decision = evaluer_resultat(resultat)

    assert decision.usable is False
    assert "score_insuffisant" in decision.reason


def test_score_none_traite_comme_insuffisant():
    """score=None (ne devrait pas arriver vu le contrat RagResult, mais défense en profondeur) -> usable=False."""
    resultat = RagResult(found=True, value="un extrait valide", source="docx:x.docx", score=None, chunk_id="id-1")

    decision = evaluer_resultat(resultat)

    assert decision.usable is False
    assert "score_insuffisant" in decision.reason


def test_document_non_autorise(monkeypatch):
    """Type de source hors AUTHORIZED_SOURCES (config) -> usable=False, raison 'document_non_autorise'."""
    monkeypatch.setattr(rag_settings, "AUTHORIZED_SOURCES", ("skill_md",))  # docx retiré de la liste
    resultat = RagResult(found=True, value="un extrait valide", source="docx:x.docx", score=0.9, chunk_id="id-1")

    decision = evaluer_resultat(resultat)

    assert decision.usable is False
    assert "document_non_autorise" in decision.reason


def test_document_autorise_par_config_personnalisee(monkeypatch):
    """
    Vérifie que AUTHORIZED_SOURCES est bien LU depuis la config (pas codé
    en dur) : élargir la liste à un type inhabituel doit suffire à faire
    passer un résultat qui aurait échoué avec la config par défaut si ce
    type n'y figurait pas.
    """
    monkeypatch.setattr(rag_settings, "AUTHORIZED_SOURCES", ("docx", "pdf_experimental"))
    resultat = RagResult(
        found=True, value="un extrait valide", source="pdf_experimental:notice.pdf", score=0.9, chunk_id="id-1"
    )

    decision = evaluer_resultat(resultat)

    assert decision.usable is True


def test_min_score_lu_depuis_la_config(monkeypatch):
    """Vérifie que MIN_SCORE est bien LU depuis la config à l'appel (pas figé à l'import) -- coeur du monkeypatching."""
    monkeypatch.setattr(rag_settings, "MIN_SCORE", 0.5)
    resultat_sous_le_nouveau_seuil = RagResult(
        found=True, value="extrait", source="docx:x.docx", score=0.4, chunk_id="id-1"
    )
    resultat_au_dessus = RagResult(found=True, value="extrait", source="docx:x.docx", score=0.6, chunk_id="id-1")

    assert evaluer_resultat(resultat_sous_le_nouveau_seuil).usable is False
    assert evaluer_resultat(resultat_au_dessus).usable is True


def test_toute_decision_a_une_raison_non_vide():
    """Invariant transversal : quel que soit le cas, `reason` n'est jamais vide (traçabilité totale)."""
    cas = [
        RESULTAT_VALIDE,
        RagResult(found=False, value=None, source=None, score=None, chunk_id=None),
        RagResult(found=True, value=None, source="docx:x", score=0.9, chunk_id="id"),
        RagResult(found=True, value="v", source=None, score=0.9, chunk_id="id"),
        RagResult(found=True, value="v", source="docx:x", score=0.9, chunk_id=None),
        RagResult(found=True, value="v", source="docx:x", score=0.0, chunk_id="id"),
    ]
    for resultat in cas:
        decision = evaluer_resultat(resultat)
        assert decision.reason, f"raison vide pour {resultat!r}"


def test_aucune_exception_jamais_levee():
    """Batterie de cas limites/malformés -> jamais d'exception, toujours une RagDecision."""
    cas_limites = [
        RagResult(found=True, value="", source="docx:x.docx", score=0.9, chunk_id="id-1"),  # value="" plutôt que None
        RagResult(found=True, value="v", source="", score=0.9, chunk_id="id-1"),  # source=""
        RagResult(found=True, value="v", source="docx:x.docx", score=0.9, chunk_id=""),  # chunk_id=""
        RagResult(found=True, value="v", source="sans_deux_points", score=0.9, chunk_id="id-1"),  # source malformée
    ]
    for resultat in cas_limites:
        decision = evaluer_resultat(resultat)  # ne doit jamais lever
        assert decision.usable is False
        assert decision.reason