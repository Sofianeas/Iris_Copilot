# tests/base_components/test_base_rule.py
#
# Tests communs du contrat BaseRule -- ne teste aucune logique métier
# d'une règle concrète (déjà couvert par tests/rules/test_priority_rule.py
# et test_client_rule.py). Vérifie uniquement que le CONTRAT lui-même est
# correctement appliqué.

import pytest

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket
from app.rules.base_rule import BaseRule


def test_base_rule_non_instantiable_directement():
    with pytest.raises(TypeError):
        BaseRule()


def test_sous_classe_complete_instantiable_et_fonctionnelle():
    class RegleFactice(BaseRule):
        def evaluate(self, ticket: Ticket, rag_decision: RagDecision | None) -> list[RuleRecommendation]:
            return []

    regle = RegleFactice()
    resultat = regle.evaluate(Ticket(), None)

    assert isinstance(resultat, list)
    assert resultat == []


def test_sous_classe_incomplete_non_instantiable():
    class RegleIncomplete(BaseRule):
        pass  # evaluate() non implémentée

    with pytest.raises(TypeError):
        RegleIncomplete()