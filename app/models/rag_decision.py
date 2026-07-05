"""
app/models/rag_decision.py

Modèle de décision RAG. Représente la décision finale de savoir si un
RagResult peut être utilisé -- ne connaît ni la classe Ticket, ni aucun
Agent. Produit exclusivement par app.services.rag_decision_service.
"""

from dataclasses import dataclass

from app.services.rag_fallback_service import RagResult


@dataclass(frozen=True)
class RagDecision:
    usable: bool
    reason: str
    result: RagResult | None