# tests/base_components/test_base_agent.py
#
# Tests communs du contrat BaseAgent -- ne teste aucune logique métier
# d'un agent concret (déjà couvert par tests/*_agent_rule_engine.py).
# Vérifie uniquement que le CONTRAT lui-même est correctement appliqué :
# non-instanciabilité, respect de la signature abstraite.

import pytest

from app.agents.base_agent import BaseAgent
from app.models.agent_contracts import AgentRequest, AgentResult
from app.models.ticket import Ticket


def test_base_agent_non_instantiable_directement():
    with pytest.raises(TypeError):
        BaseAgent()


def test_sous_classe_complete_instantiable_et_fonctionnelle():
    class AgentFactice(BaseAgent):
        def analyze(self, request: AgentRequest) -> AgentResult:
            return AgentResult(ticket=request.ticket, succes=True)

    agent = AgentFactice()
    request = AgentRequest(ticket=Ticket(), texte_mail="texte")
    result = agent.analyze(request)

    assert isinstance(result, AgentResult)
    assert result.succes is True
    assert result.ticket is request.ticket


def test_sous_classe_incomplete_non_instantiable():
    class AgentIncomplet(BaseAgent):
        pass  # analyze() non implémentée

    with pytest.raises(TypeError):
        AgentIncomplet()