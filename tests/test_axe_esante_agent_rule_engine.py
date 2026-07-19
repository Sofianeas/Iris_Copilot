# tests/test_axe_esante_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans axe_esante_agent.py (Groupe B,
# signature différente : enrich_ticket_depuis_excel).
#
# ⚠️ Fixture xlsx MINIMALE et EXPLICITEMENT SYNTHÉTIQUE (construite via
# openpyxl dans le test lui-même) -- ne revalide PAS la logique de parsing
# AXE E-SANTE déjà stable (hors périmètre de cette catégorie de
# changement), se concentre uniquement sur le nouveau point d'intégration
# Rule Engine.

import openpyxl
import pytest

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import axe_esante_agent


def _construire_xlsx_minimal(chemin, description="Intervention standard sur borne."):
    """Construit un xlsx synthétique minimal, juste assez pour atteindre le point d'intégration Rule Engine."""
    wb = openpyxl.Workbook()
    ws = wb.active
    lignes = [
        ("Intitulé de la demande", "Test synthétique"),
        ("Type de demande", "Installation"),
        ("Adresse", "Nom du site : SITE TEST\n1 rue de Test, 75000 PARIS\nContact sur site pour intervention : M. Test"),
        ("Description complète de la demande", description),
        ("Besoin de matériel (oui/non)", "Non"),
    ]
    for label, valeur in lignes:
        ws.append([label])
        ws.append([valeur])
    wb.save(chemin)
    return chemin


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


@pytest.fixture
def xlsx_standard(tmp_path):
    chemin = tmp_path / "demande_standard.xlsx"
    return _construire_xlsx_minimal(chemin)


@pytest.fixture
def xlsx_urgence(tmp_path):
    chemin = tmp_path / "demande_urgence.xlsx"
    return _construire_xlsx_minimal(chemin, description="Panne urgente sur la borne d'accueil.")


def test_retrocompatibilite_stricte_signature_historique(xlsx_standard):
    ticket = Ticket()
    ticket = axe_esante_agent.enrich_ticket_depuis_excel(ticket, xlsx_standard)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.customer.enseigne == "SITE TEST"


def test_rule_engine_detecte_urgence(xlsx_urgence):
    ticket = Ticket()
    ticket = axe_esante_agent.enrich_ticket_depuis_excel(ticket, xlsx_urgence, activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_actif_sans_declenchement(xlsx_standard):
    ticket = Ticket()
    ticket = axe_esante_agent.enrich_ticket_depuis_excel(ticket, xlsx_standard, activer_rule_engine=True)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_recommande_contrat_si_vide(xlsx_standard):
    """CONTRAT_AXE_ESANTE est vide dans cet agent -> client_rule DOIT se déclencher si une RagDecision usable est fournie."""
    ticket = Ticket()
    ticket = axe_esante_agent.enrich_ticket_depuis_excel(
        ticket, xlsx_standard, rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert "contrat" in ticket.intervention.commentaire_interne.lower()
    assert "OD.X" in ticket.intervention.commentaire_interne


def test_aucun_champ_metier_modifie_par_le_rule_engine(xlsx_standard):
    ticket = Ticket()
    ticket = axe_esante_agent.enrich_ticket_depuis_excel(
        ticket, xlsx_standard, rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat == ""  # jamais écrasé par la recommandation


def test_desactive_par_defaut_meme_avec_rag_decision_fournie(xlsx_standard):
    ticket = Ticket()
    ticket = axe_esante_agent.enrich_ticket_depuis_excel(
        ticket, xlsx_standard, rag_decision=_rag_decision_usable()
    )

    assert "Rule Engine" not in ticket.intervention.commentaire_interne