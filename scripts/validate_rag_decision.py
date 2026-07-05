#!/usr/bin/env python3
"""
validate_rag_decision.py

Script de validation autonome (pas pytest) de rag_decision_service.py en
isolation (aucun Ticket, aucun vectorstore -- uniquement des RagResult
synthétiques), pour vérifier les invariants structurels du moteur de
décision indépendamment de tout scénario métier.

Vérifie automatiquement :
  - score       : le seuil MIN_SCORE est réellement appliqué (rejet sous le
                  seuil, acceptation au-dessus).
  - source      : aucune décision usable=True sans source renseignée.
  - chunk       : aucune décision usable=True sans chunk_id renseigné.
  - logging     : chaque appel à evaluer_resultat produit au moins un log.
  - configuration : ENABLE_RAG=False force usable=False ; les valeurs de
                  config sont bien lues dynamiquement (monkeypatch-able).
  - typage      : le retour est TOUJOURS une instance de RagDecision aux
                  champs correctement typés, jamais une exception.

Usage : python validate_rag_decision.py
Sortie : 0 si tout passe, 1 sinon (code de sortie exploitable en CI).
"""

import logging
import sys

import app.config.rag_settings as rag_settings
from app.models.rag_decision import RagDecision
from app.services.rag_decision_service import evaluer_resultat
from app.services.rag_fallback_service import RagResult


class CapteurDeLogs(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


RESULTAT_VALIDE = RagResult(found=True, value="extrait valide", source="docx:x.docx", score=0.8, chunk_id="id-1")


def _verifier_score(echecs: list[str]) -> None:
    original = rag_settings.MIN_SCORE
    try:
        rag_settings.MIN_SCORE = 0.5
        sous_seuil = evaluer_resultat(dataclasses_replace_score(RESULTAT_VALIDE, 0.2))
        au_dessus = evaluer_resultat(dataclasses_replace_score(RESULTAT_VALIDE, 0.9))
        if sous_seuil.usable is not False:
            echecs.append("score : un score sous MIN_SCORE a été accepté")
        if au_dessus.usable is not True:
            echecs.append("score : un score au-dessus de MIN_SCORE a été rejeté")
    finally:
        rag_settings.MIN_SCORE = original


def _verifier_source(echecs: list[str]) -> None:
    import dataclasses
    sans_source = dataclasses.replace(RESULTAT_VALIDE, source=None)
    decision = evaluer_resultat(sans_source)
    if decision.usable is not False:
        echecs.append("source : un résultat sans source a été accepté comme usable")


def _verifier_chunk(echecs: list[str]) -> None:
    import dataclasses
    sans_chunk = dataclasses.replace(RESULTAT_VALIDE, chunk_id=None)
    decision = evaluer_resultat(sans_chunk)
    if decision.usable is not False:
        echecs.append("chunk : un résultat sans chunk_id a été accepté comme usable")


def _verifier_logging(echecs: list[str]) -> None:
    capteur = CapteurDeLogs()
    capteur.setLevel(logging.INFO)
    logger_decision = logging.getLogger("iris_copilot.rag_decision")
    logger_decision.addHandler(capteur)
    logger_decision.setLevel(logging.INFO)
    try:
        capteur.records.clear()
        evaluer_resultat(RESULTAT_VALIDE)
        if not capteur.records:
            echecs.append("logging : evaluer_resultat n'a émis aucun log")
    finally:
        logger_decision.removeHandler(capteur)


def _verifier_configuration(echecs: list[str]) -> None:
    original_enable = rag_settings.ENABLE_RAG
    try:
        rag_settings.ENABLE_RAG = False
        decision = evaluer_resultat(RESULTAT_VALIDE)
        if decision.usable is not False:
            echecs.append("configuration : ENABLE_RAG=False n'empêche pas usable=True")
    finally:
        rag_settings.ENABLE_RAG = original_enable

    # Vérifie que la lecture est bien dynamique (pas figée à l'import du module).
    original_min = rag_settings.MIN_SCORE
    try:
        rag_settings.MIN_SCORE = 0.99
        decision_stricte = evaluer_resultat(RESULTAT_VALIDE)  # score=0.8 < 0.99
        if decision_stricte.usable is not False:
            echecs.append("configuration : modifier MIN_SCORE après import n'a aucun effet (lecture non dynamique)")
    finally:
        rag_settings.MIN_SCORE = original_min


def _verifier_typage(echecs: list[str]) -> None:
    cas = [
        RESULTAT_VALIDE,
        RagResult(found=False, value=None, source=None, score=None, chunk_id=None),
        RagResult(found=True, value="", source="", score=0.0, chunk_id=""),
    ]
    for resultat in cas:
        try:
            decision = evaluer_resultat(resultat)
        except Exception as exc:
            echecs.append(f"typage : evaluer_resultat a levé une exception pour {resultat!r} : {exc!r}")
            continue
        if not isinstance(decision, RagDecision):
            echecs.append(f"typage : retour non-RagDecision pour {resultat!r}")
        if not isinstance(decision.usable, bool):
            echecs.append(f"typage : decision.usable n'est pas un bool pour {resultat!r}")
        if not isinstance(decision.reason, str) or not decision.reason:
            echecs.append(f"typage : decision.reason vide/non-str pour {resultat!r}")


def dataclasses_replace_score(resultat: RagResult, score: float) -> RagResult:
    import dataclasses
    return dataclasses.replace(resultat, score=score)


def main() -> int:
    echecs: list[str] = []
    verifications = [
        ("score", _verifier_score),
        ("source", _verifier_source),
        ("chunk", _verifier_chunk),
        ("logging", _verifier_logging),
        ("configuration", _verifier_configuration),
        ("typage", _verifier_typage),
    ]

    print("RAG DECISION VALIDATION\n")

    resultats_par_categorie: dict[str, bool] = {}
    for nom, fonction in verifications:
        echecs_avant = len(echecs)
        fonction(echecs)
        resultats_par_categorie[nom] = len(echecs) == echecs_avant

    for nom, _fonction in verifications:
        marque = "✔" if resultats_par_categorie[nom] else "✘"
        print(f"{marque} {nom}")

    print()
    if echecs:
        print("Détail des échecs :")
        for e in echecs:
            print(f"  - {e}")
        print("\nFAILURE")
        return 1

    print("SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())