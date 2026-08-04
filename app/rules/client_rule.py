"""
app/rules/client_rule.py

Règle indépendante : si le Contrat du ticket est vide et qu'une
RagDecision utilisable existe, recommande la valeur RAG comme candidate.

Ne l'applique JAMAIS au Ticket -- ce n'est pas le rôle d'une règle,
confiance plafonnée à 0.6 : une suggestion RAG reste une donnée non
vérifiée, jamais présentée comme certaine même si son score de retrieval
est élevé.

--- Harmonisation Framework des Rules (P3-430) ---
Logique déplacée dans `ClientRule.evaluate()` (contrat BaseRule officiel).
La fonction `evaluer()` reste un adaptateur de compatibilité.
"""

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket
from app.rules.base_rule import BaseRule

CONFIANCE_MAX_RAG = 0.6  # jamais > ceci : donnée RAG non vérifiée, cf. docstring


class ClientRule(BaseRule):
    """Recommande un Contrat manquant depuis une RagDecision utilisable. Ne dépend pas du client spécifique (générique)."""

    def evaluate(self, ticket: Ticket, rag_decision: RagDecision | None) -> list[RuleRecommendation]:
        if ticket.intervention.contrat:
            return []  # champ déjà résolu -- le déterministe prime
        if rag_decision is None or not rag_decision.usable or rag_decision.result is None:
            return []

        resultat = rag_decision.result
        confiance = min(resultat.score, CONFIANCE_MAX_RAG) if resultat.score is not None else CONFIANCE_MAX_RAG

        return [
            RuleRecommendation(
                field="contrat",
                value=resultat.value,
                confidence=confiance,
                source=resultat.source,
                reason="Contrat manquant sur le ticket, suggestion RAG disponible et jugée utilisable",
            )
        ]


def evaluer(ticket: Ticket, rag_decision: RagDecision | None = None) -> list[RuleRecommendation]:
    """⚠️ ADAPTATEUR DE COMPATIBILITÉ -- délègue à ClientRule.evaluate()."""
    return ClientRule().evaluate(ticket, rag_decision)