"""
app/rules/priority_rule.py

Règle indépendante : détecte des mots-clés d'urgence dans la
Problématique et recommande un niveau de priorité plus élevé.

Ne modifie JAMAIS le Ticket -- retourne une liste de RuleRecommendation
(0 ou 1 élément). Ne connaît pas les autres règles.

--- Harmonisation Framework des Rules (P3-430) ---
Logique déplacée dans `PriorityRule.evaluate()` (contrat BaseRule
officiel). La fonction `evaluer()` reste un adaptateur de compatibilité
-- aucun appelant existant (dont le Rule Engine actuel, s'il utilisait
encore la fonction nue) n'est cassé.
"""

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket
from app.rules.base_rule import BaseRule

MOTS_CLES_URGENCE = ("urgent", "critique", "bloquant", "arret complet", "arrêt complet")


class PriorityRule(BaseRule):
    """Détecte un mot-clé d'urgence dans la Problématique. Ne dépend jamais de `rag_decision`."""

    def evaluate(self, ticket: Ticket, rag_decision: RagDecision | None) -> list[RuleRecommendation]:
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


def evaluer(ticket: Ticket, rag_decision: RagDecision | None = None) -> list[RuleRecommendation]:
    """⚠️ ADAPTATEUR DE COMPATIBILITÉ -- délègue à PriorityRule.evaluate()."""
    return PriorityRule().evaluate(ticket, rag_decision)