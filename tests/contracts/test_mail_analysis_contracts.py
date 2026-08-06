# tests/contracts/test_mail_analysis_contracts.py
#
# Certifie les contrats publics MailAnalysisRequest/MailAnalysisResult --
# construction, immutabilité, valeurs par défaut, types. Aucune logique
# métier testée.

import dataclasses

import pytest

from app.models.mail_analysis import MailAnalysisRequest, MailAnalysisResult
from app.models.rag_decision import RagDecision
from app.models.ticket import Ticket
from app.services.rag_fallback_service import RagResult


# --------------------------------------------------------------------------
# MailAnalysisRequest
# --------------------------------------------------------------------------

def test_mail_analysis_request_construction_minimale():
    request = MailAnalysisRequest(texte_mail="contenu du mail")

    assert request.texte_mail == "contenu du mail"


def test_mail_analysis_request_valeurs_par_defaut():
    request = MailAnalysisRequest(texte_mail="texte")

    assert request.fichier_attache is None
    assert request.client_force is None


def test_mail_analysis_request_construction_complete():
    request = MailAnalysisRequest(
        texte_mail="texte", fichier_attache="/chemin/fichier.xlsx", client_force="ADOPT"
    )

    assert request.fichier_attache == "/chemin/fichier.xlsx"
    assert request.client_force == "ADOPT"


def test_mail_analysis_request_est_immutable():
    request = MailAnalysisRequest(texte_mail="texte")

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.texte_mail = "autre texte"


def test_mail_analysis_request_est_bien_un_frozen_dataclass():
    assert dataclasses.is_dataclass(MailAnalysisRequest)
    assert MailAnalysisRequest.__dataclass_params__.frozen is True


# --------------------------------------------------------------------------
# MailAnalysisResult
# --------------------------------------------------------------------------

def test_mail_analysis_result_construction_cas_succes():
    ticket = Ticket()
    result = MailAnalysisResult(succes=True, ticket=ticket, client_detecte="ADOPT")

    assert result.succes is True
    assert result.ticket is ticket
    assert result.client_detecte == "ADOPT"


def test_mail_analysis_result_construction_cas_echec():
    result = MailAnalysisResult(succes=False, ticket=None, client_detecte=None, erreur="client non reconnu")

    assert result.succes is False
    assert result.ticket is None
    assert result.client_detecte is None
    assert result.erreur == "client non reconnu"


def test_mail_analysis_result_valeurs_par_defaut():
    result = MailAnalysisResult(succes=True, ticket=Ticket(), client_detecte="ADOPT")

    assert result.rag_decision is None
    assert result.erreur is None


def test_mail_analysis_result_avec_rag_decision():
    rag_decision = RagDecision(
        usable=True, reason="ok",
        result=RagResult(found=True, value="X", source="docx:x", score=0.8, chunk_id="1"),
    )
    result = MailAnalysisResult(succes=True, ticket=Ticket(), client_detecte="ADOPT", rag_decision=rag_decision)

    assert result.rag_decision is rag_decision


def test_mail_analysis_result_est_immutable():
    result = MailAnalysisResult(succes=True, ticket=Ticket(), client_detecte="ADOPT")

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.succes = False


def test_mail_analysis_result_est_bien_un_frozen_dataclass():
    assert dataclasses.is_dataclass(MailAnalysisResult)
    assert MailAnalysisResult.__dataclass_params__.frozen is True