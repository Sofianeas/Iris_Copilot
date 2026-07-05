"""
app/models/rule_recommendation.py

Représente une recommandation produite par une règle métier pure (cf.
app/rules/). Aucune logique -- porteur de données uniquement.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleRecommendation:
    field: str
    value: str
    confidence: float
    source: str
    reason: str