"""
app/services/rule_engine.py

Moteur de règles métier PURES. Reçoit un Ticket (lecture seule) et,
éventuellement, une RagDecision déjà calculée par la couche RAG -- exécute
toutes les règles enregistrées, collecte leurs recommandations, élimine
les doublons, et journalise chaque étape.

Ne modifie JAMAIS le Ticket. Le métier ne dépend jamais directement du
VectorStore ici : ce moteur ne reçoit qu'une RagDecision déjà tranchée
(produite ailleurs, cf. rag_integration_layer/rag_decision_service),
jamais de dossier_persistance ni d'embed_fn -- aucune connaissance du RAG
brut, uniquement de son résultat final typé.

Contrat d'une règle (RegleFn) : chaque fichier de app/rules/ expose une
fonction `evaluer(ticket: Ticket, rag_decision: RagDecision | None) ->
list[RuleRecommendation]`, indépendante des autres, testable isolément,
qui ne modifie jamais `ticket`.
"""

import logging
from typing import Callable

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket
from app.rules.client_rule import evaluer as regle_client
from app.rules.priority_rule import evaluer as regle_priorite

logger = logging.getLogger("iris_copilot.rule_engine")

RegleFn = Callable[[Ticket, RagDecision | None], list[RuleRecommendation]]

# Registre explicite des règles actives -- volontairement une simple liste
# (pas de découverte dynamique de fichiers) : plus transparent, plus facile
# à auditer/tester qu'un mécanisme de plugin implicite, cohérent avec
# "éviter la complexité inutile".
REGLES: list[RegleFn] = [
    regle_priorite,
    regle_client,
]


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
    L'indépendance entre règles s'applique aussi à leurs échecs.
    """
    toutes_recommandations: list[RuleRecommendation] = []

    for regle in REGLES:
        nom_regle = regle.__module__
        try:
            recommandations = regle(ticket, rag_decision)
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