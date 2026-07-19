# tests/test_etam_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans etam_agent.py (Groupe B,
# signature : enrich_ticket_depuis_fichier).
#
# ⚠️ Fixture xlsx MINIMALE et EXPLICITEMENT SYNTHÉTIQUE -- ne revalide PAS
# la logique de parsing ETAM déjà testée par ailleurs, se concentre sur le
# nouveau point d'intégration Rule Engine. Branche MOBILITE choisie (seule
# pleinement implémentée).

import openpyxl
import pytest

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import etam_agent


def _construire_xlsx_minimal(chemin, description_panne="Port de charge défectueux"):
    """xlsx synthétique minimal, branche MOBILITE (Samsung A52)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Code Magasin", "0351"])
    ws.append(["Adresse de livraison et d'enlèvement",
               "ETAM Lingerie (n° 0351)\n1 rue des platanes\n34970 LATTES\nFRANCE\nTél : 0033 (0) 4 67 64 04 46"])
    ws.append(["Nom et N° de téléphone d'un contact ou du responsable sur site", "Morgane"])
    ws.append(["Information technique du matériel en panne", ""])
    ws.append(["Description panne", description_panne])
    ws.append(["Langue", "Français"])
    ws.append(["Information technique du matériel à préparer", ""])
    ws.append(["Matériel (Modèle)", "SMARTPHONE SAMSUNG A52-5G", "CETAMOB-SAMSUNG-A52-5G"])
    ws.append(["Information N° incident Akkodis", ""])
    ws.append(["N° Dossier Akkodis :", "INC12345"])
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
    return _construire_xlsx_minimal(chemin, description_panne="Panne urgente, port de charge grillé")


def test_retrocompatibilite_stricte_signature_historique(xlsx_standard):
    ticket = Ticket()
    ticket = etam_agent.enrich_ticket_depuis_fichier(ticket, xlsx_standard)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.intervention.contrat == "Maintenance Mobilité"
    assert ticket.customer.client == "ETAM"


def test_rule_engine_detecte_urgence(xlsx_urgence):
    ticket = Ticket()
    ticket = etam_agent.enrich_ticket_depuis_fichier(ticket, xlsx_urgence, activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_actif_sans_declenchement(xlsx_standard):
    ticket = Ticket()
    ticket = etam_agent.enrich_ticket_depuis_fichier(ticket, xlsx_standard, activer_rule_engine=True)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_contrat_jamais_vide(xlsx_standard):
    """Le contrat ETAM n'est jamais vide (MOBILITE -> 'Maintenance Mobilité') -> client_rule ne se déclenche jamais ici."""
    ticket = Ticket()
    ticket = etam_agent.enrich_ticket_depuis_fichier(
        ticket, xlsx_standard, rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat == "Maintenance Mobilité"  # jamais écrasé


def test_desactive_par_defaut_meme_avec_rag_decision_fournie(xlsx_standard):
    ticket = Ticket()
    ticket = etam_agent.enrich_ticket_depuis_fichier(
        ticket, xlsx_standard, rag_decision=_rag_decision_usable()
    )

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_non_regression_regle_a52_toujours_appliquee():
    """Non-régression : la substitution A54->A52 continue de fonctionner, Rule Engine actif ou non."""
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        chemin = os.path.join(tmp, "demande_a54.xlsx")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Code Magasin", "0351"])
        ws.append(["Adresse de livraison et d'enlèvement", "ETAM Lingerie (n° 0351)\n1 rue X\n34970 LATTES\nFRANCE"])
        ws.append(["Information technique du matériel en panne", ""])
        ws.append(["Description panne", "Ecran casse"])
        ws.append(["Information technique du matériel à préparer", ""])
        ws.append(["Matériel (Modèle)", "SMARTPHONE SAMSUNG A54-5G", "CETAMOB-SAMSUNG-A54-5G"])
        wb.save(chemin)

        ticket = Ticket()
        ticket = etam_agent.enrich_ticket_depuis_fichier(ticket, chemin, activer_rule_engine=True)

        assert "RÈGLE CLIENT APPLIQUÉE" in ticket.intervention.commentaire_interne
        assert "CETAMOB-SAMSUNG-A52-5G" in ticket.logistics.pieces