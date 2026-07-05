"""
app/rules/priority_rule.py

Règle indépendante : détecte des mots-clés d'urgence dans la
Problématique et recommande un niveau de priorité plus élevé.

Ne modifie JAMAIS le Ticket -- retourne une liste de RuleRecommendation
(0 ou 1 élément). Ne connaît pas les autres règles.
"""

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket

MOTS_CLES_URGENCE = ("urgent", "critique", "bloquant", "arret complet", "arrêt complet")


def evaluer(ticket: Ticket, rag_decision: RagDecision | None = None) -> list[RuleRecommendation]:
    """
    `rag_decision` est accepté pour respecter le contrat commun à toutes
    les règles (RegleFn), mais n'est pas utilisé ici -- cette règle ne
    dépend que du Ticket.
    """
    texte = (ticket.intervention.problematique or "").lower()
    for mot in MOTS_CLES_URGENCE:
        if mot in texte:
            return [
                RuleRecommendation(
                    field="niveau_priorite",
                    value="Urgent",
                    confidence=0.7,
                    source="priority_rule:mot_cle_urgence",
                    reason=f"mot-clé d'urgence détecté dans la Problématique : {mot!r}",
                )
            ]
    return []