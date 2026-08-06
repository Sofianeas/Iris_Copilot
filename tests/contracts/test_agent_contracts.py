# tests/contracts/test_agent_contracts.py
#
# Certifie les contrats publics AgentRequest/AgentResult -- construction,
# immutabilité, valeurs par défaut, types. Aucune logique métier testée.

import dataclasses

import pytest

from app.models.agent_contracts import AgentRequest, AgentResult
from app.models.rag_decision import RagDecision
from app.models.ticket import Ticket
from app.services.rag_fallback_service import RagResult


# --------------------------------------------------------------------------
# AgentRequest
# --------------------------------------------------------------------------

def test_agent_request_construction_minimale():
    request = AgentRequest(ticket=Ticket(), texte_mail="contenu du mail")

    assert isinstance(request.ticket, Ticket)
    assert request.texte_mail == "contenu du mail"


def test_agent_request_valeurs_par_defaut():
    request = AgentRequest(ticket=Ticket(), texte_mail="texte")

    assert request.fichier_attache is None
    assert request.rag_decision is None


def test_agent_request_construction_complete():
    ticket = Ticket()
    rag_decision = RagDecision(
        usable=True, reason="ok",
        result=RagResult(found=True, value="X", source="docx:x", score=0.8, chunk_id="1"),
    )
    request = AgentRequest(
        ticket=ticket, texte_mail="texte", fichier_attache="/chemin/fichier.xlsx", rag_decision=rag_decision
    )

    assert request.ticket is ticket
    assert request.fichier_attache == "/chemin/fichier.xlsx"
    assert request.rag_decision is rag_decision


def test_agent_request_est_immutable():
    request = AgentRequest(ticket=Ticket(), texte_mail="texte")

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.texte_mail = "autre texte"


def test_agent_request_est_bien_un_frozen_dataclass():
    assert dataclasses.is_dataclass(AgentRequest)
    assert AgentRequest.__dataclass_params__.frozen is True


# --------------------------------------------------------------------------
# AgentResult
# --------------------------------------------------------------------------

def test_agent_result_construction_minimale():
    ticket = Ticket()
    result = AgentResult(ticket=ticket)

    assert result.ticket is ticket


def test_agent_result_succes_true_par_defaut():
    result = AgentResult(ticket=Ticket())

    assert result.succes is True


def test_agent_result_erreur_none_par_defaut():
    result = AgentResult(ticket=Ticket())

    assert result.erreur is None


def test_agent_result_cas_echec():
    result = AgentResult(ticket=Ticket(), succes=False, erreur="message d'erreur lisible")

    assert result.succes is False
    assert result.erreur == "message d'erreur lisible"


def test_agent_result_est_immutable():
    result = AgentResult(ticket=Ticket())

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.succes = False


def test_agent_result_est_bien_un_frozen_dataclass():
    assert dataclasses.is_dataclass(AgentResult)
    assert AgentResult.__dataclass_params__.frozen is True