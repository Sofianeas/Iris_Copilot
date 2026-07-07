#!/usr/bin/env python3
"""
scripts/validate_rule_engine.py

Script de validation autonome (pas pytest) de app/services/rule_engine.py
et des règles enregistrées dans REGLES.

Vérifie automatiquement :
  1. Toutes les règles retournent une liste (jamais un autre type).
  2. Chaque RuleRecommendation produite possède source/reason/confidence
     valides (non vides, confidence ∈ [0, 1]).
  3. Aucune règle ne modifie le Ticket qu'elle reçoit.
  4. Aucune exception ne sort du moteur (executer()), même si une règle
     est volontairement cassée.
  5. Le moteur reste déterministe : même Ticket + même RagDecision ->
     même liste de recommandations, à chaque appel.

Usage : python -m scripts.validate_rule_engine
Sortie : 0 si tout passe, 1 sinon (code de sortie exploitable en CI).
"""

import dataclasses
import sys

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket
from app.services import rule_engine
from app.services.rag_fallback_service import RagResult
from app.services.rule_engine import executer


def _decision_usable() -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value="OD.TEST.001", source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def _scenarios() -> list[tuple[str, Ticket, RagDecision | None]]:
    """Batterie de scénarios couvrant les 2 règles enregistrées (priority_rule, client_rule)."""
    t_urgence_et_contrat_manquant = Ticket()
    t_urgence_et_contrat_manquant.intervention.problematique = "urgent, arret complet"

    t_neutre = Ticket()

    t_contrat_deja_rempli = Ticket()
    t_contrat_deja_rempli.intervention.contrat = "Deja rempli"

    return [
        ("urgence_et_contrat_manquant", t_urgence_et_contrat_manquant, _decision_usable()),
        ("ticket_neutre_sans_rag", t_neutre, None),
        ("contrat_deja_rempli", t_contrat_deja_rempli, _decision_usable()),
    ]


def _verifier_toutes_regles_retournent_une_liste(echecs: list[str]) -> None:
    for nom, ticket, decision in _scenarios():
        for regle in rule_engine.REGLES:
            try:
                resultat = regle(ticket, decision)
            except Exception as exc:
                echecs.append(f"[{nom}] regle={regle.__module__} a leve une exception : {exc!r}")
                continue
            if not isinstance(resultat, list):
                echecs.append(
                    f"[{nom}] regle={regle.__module__} ne retourne pas une liste "
                    f"(type={type(resultat).__name__})"
                )


def _verifier_recommandations_completes(echecs: list[str]) -> None:
    for nom, ticket, decision in _scenarios():
        for regle in rule_engine.REGLES:
            try:
                resultat = regle(ticket, decision)
            except Exception:
                continue  # déjà signalé ci-dessus
            if not isinstance(resultat, list):
                continue  # déjà signalé ci-dessus
            for reco in resultat:
                if not isinstance(reco, RuleRecommendation):
                    echecs.append(f"[{nom}] regle={regle.__module__} a retourne un element non-RuleRecommendation : {reco!r}")
                    continue
                if not reco.source:
                    echecs.append(f"[{nom}] regle={regle.__module__} : recommandation sans source : {reco!r}")
                if not reco.reason:
                    echecs.append(f"[{nom}] regle={regle.__module__} : recommandation sans reason : {reco!r}")
                if not isinstance(reco.confidence, float) or not (0.0 <= reco.confidence <= 1.0):
                    echecs.append(f"[{nom}] regle={regle.__module__} : confidence invalide : {reco!r}")


def _verifier_aucune_regle_ne_modifie_le_ticket(echecs: list[str]) -> None:
    for nom, ticket, decision in _scenarios():
        for regle in rule_engine.REGLES:
            avant = dataclasses.asdict(ticket)
            try:
                regle(ticket, decision)
            except Exception:
                continue  # exception déjà signalée par ailleurs
            apres = dataclasses.asdict(ticket)
            if avant != apres:
                echecs.append(f"[{nom}] regle={regle.__module__} a modifie le Ticket")


def _verifier_aucune_exception_ne_sort_du_moteur(echecs: list[str]) -> None:
    """Injecte une règle volontairement cassée dans REGLES (temporairement) et vérifie qu'executer() ne propage jamais l'exception."""
    def regle_cassee(ticket: Ticket, rag_decision: RagDecision | None) -> list[RuleRecommendation]:
        raise RuntimeError("panne simulee pour validation")

    regles_originales = list(rule_engine.REGLES)
    try:
        rule_engine.REGLES.append(regle_cassee)
        for nom, ticket, decision in _scenarios():
            try:
                executer(ticket, decision)
            except Exception as exc:
                echecs.append(f"[{nom}] executer() a laisse fuiter une exception malgre une regle cassee : {exc!r}")
    finally:
        rule_engine.REGLES[:] = regles_originales


def _verifier_determinisme(echecs: list[str]) -> None:
    for nom, ticket, decision in _scenarios():
        resultat_1 = executer(ticket, decision)
        resultat_2 = executer(ticket, decision)
        if resultat_1 != resultat_2:
            echecs.append(f"[{nom}] executer() n'est pas deterministe pour une entree identique")


def main() -> int:
    echecs: list[str] = []

    verifications = [
        ("toutes_les_regles_retournent_une_liste", _verifier_toutes_regles_retournent_une_liste),
        ("recommandations_completes_source_reason_confidence", _verifier_recommandations_completes),
        ("aucune_regle_ne_modifie_le_ticket", _verifier_aucune_regle_ne_modifie_le_ticket),
        ("aucune_exception_ne_sort_du_moteur", _verifier_aucune_exception_ne_sort_du_moteur),
        ("determinisme", _verifier_determinisme),
    ]

    print("=" * 60)
    print("VALIDATE RULE ENGINE")
    print("=" * 60 + "\n")

    resultats: dict[str, bool] = {}
    for nom, fonction in verifications:
        echecs_avant = len(echecs)
        fonction(echecs)
        resultats[nom] = len(echecs) == echecs_avant

    for nom, _fonction in verifications:
        marque = "✔" if resultats[nom] else "✘"
        print(f"{marque} {nom}")

    print()
    if echecs:
        print(f"❌ {len(echecs)} echec(s) detecte(s) :\n")
        for e in echecs:
            print(f"  - {e}")
        print("\nFAILURE")
        return 1

    print("SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())