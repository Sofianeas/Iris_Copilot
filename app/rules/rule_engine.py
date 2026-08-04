"""
app/services/rule_engine.py

Moteur de règles métier PURES. Reçoit un Ticket (lecture seule) et,
éventuellement, une RagDecision déjà calculée par la couche RAG -- exécute
toutes les règles enregistrées, collecte leurs recommandations, élimine
les doublons, et journalise chaque étape.

Ne modifie JAMAIS le Ticket. Le métier ne dépend jamais directement du
VectorStore ici : ce moteur ne reçoit qu'une RagDecision déjà tranchée,
jamais de dossier_persistance ni d'embed_fn.

--- Harmonisation Framework des Rules (P3-430) ---
`REGLES` contient désormais des instances de `BaseRule` (PriorityRule(),
ClientRule()) plutôt que des fonctions nues -- comportement fonctionnel
STRICTEMENT INCHANGÉ (mêmes règles, même déduplication, même isolation
des exceptions, même journalisation).

`executer()` reste compatible avec une règle passée comme fonction nue
(callable direct) plutôt qu'une instance BaseRule -- nécessaire pour ne
pas casser les tests existants qui injectent des fonctions factices dans
REGLES (règle cassée, règle en doublon, etc., cf.
tests/test_rule_engine.py). Une règle est appelée via `.evaluate()` si
c'est une instance BaseRule, ou directement si c'est un callable.
"""

import logging
from typing import Callable, Union

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket
from app.rules.base_rule import BaseRule
from app.rules.client_rule import ClientRule
from app.rules.priority_rule import PriorityRule

logger = logging.getLogger("iris_copilot.rule_engine")

RegleFn = Callable[[Ticket, RagDecision | None], list[RuleRecommendation]]
Regle = Union[BaseRule, RegleFn]

# Registre explicite des règles actives (BaseRule désormais, cf.
# harmonisation P3-430) -- volontairement une simple liste, pas de
# découverte dynamique (cf. décision de gouvernance : "architecture
# simple, explicite, facilement maintenable", pas de discovery/DI/plugins).
REGLES: list[Regle] = [
    PriorityRule(),
    ClientRule(),
]


def _identifiant_regle(regle: Regle) -> str:
    """Identifiant lisible pour le logging -- fonctionne pour une instance BaseRule ou une fonction nue."""
    if isinstance(regle, BaseRule):
        return f"{type(regle).__module__}.{type(regle).__name__}"
    return getattr(regle, "__module__", repr(regle))


def _appeler_regle(regle: Regle, ticket: Ticket, rag_decision: RagDecision | None) -> list[RuleRecommendation]:
    """Appelle une règle, qu'elle soit une instance BaseRule (.evaluate()) ou une fonction historique (callable direct)."""
    if isinstance(regle, BaseRule):
        return regle.evaluate(ticket, rag_decision)
    return regle(ticket, rag_decision)


def _dedupliquer(recommandations: list[RuleRecommendation]) -> list[RuleRecommendation]:
    """Élimine les doublons EXACTS (field+value+source identiques) -- garde la 1ère occurrence, ordre stable."""
    vues: set[tuple[str, str, str]] = set()
    resultat: list[RuleRecommendation] = []
    for reco in recommandations:
        cle = (reco.field, reco.value, reco.source)
        if cle not in vues:
            vues.add(cle)
            resultat.append(reco)
    return resultat


def executer(ticket: Ticket, rag_decision: RagDecision | None = None) -> list[RuleRecommendation]:
    """
    Exécute toutes les règles de REGLES sur `ticket` (jamais modifié),
    collecte leurs recommandations, élimine les doublons, journalise
    chaque règle exécutée (statut + nombre de recommandations) et le
    total avant/après déduplication.

    Une règle qui lève une exception est journalisée en erreur et
    IGNORÉE -- n'interrompt jamais l'exécution des autres règles.
    """
    toutes_recommandations: list[RuleRecommendation] = []

    for regle in REGLES:
        nom_regle = _identifiant_regle(regle)
        try:
            recommandations = _appeler_regle(regle, ticket, rag_decision)
        except Exception as exc:
            logger.error("regle=%s statut=exception erreur=%r", nom_regle, exc)
            continue

        if not isinstance(recommandations, list):
            logger.error("regle=%s statut=contrat_invalide type_retourne=%s", nom_regle, type(recommandations))
            continue

        logger.info("regle=%s statut=ok nb_recommandations=%d", nom_regle, len(recommandations))
        toutes_recommandations.extend(recommandations)

    dedupliquees = _dedupliquer(toutes_recommandations)
    logger.info(
        "rule_engine total_brut=%d total_deduplique=%d",
        len(toutes_recommandations), len(dedupliquees),
    )
    return dedupliquees