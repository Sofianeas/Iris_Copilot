# tests/test_promethean_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans promethean_agent.py (dernier
# agent, Groupe C). Signature : enrich_ticket(ticket, texte_page,
# texte_mail). Un seul point de sortie.

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import promethean_agent

TEXTE_PAGE_STANDARD = """Job Request Number: JR12345
Model: ActiveBoard 4
Serial Number: AB4-987654
Comments: Ecran endommage lors du transport, remplacement standard requis.
"""


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_signature_historique():
    ticket = Ticket()
    ticket = promethean_agent.enrich_ticket(ticket, TEXTE_PAGE_STANDARD)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.customer.client == "PROMETHEAN"
    assert ticket.intervention.numero_incident_client == "JR12345"


def test_rule_engine_detecte_urgence():
    texte_urgent = TEXTE_PAGE_STANDARD.replace("remplacement standard requis", "remplacement urgent requis")
    ticket = Ticket()
    ticket = promethean_agent.enrich_ticket(ticket, texte_urgent, activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_actif_sans_declenchement():
    ticket = Ticket()
    ticket = promethean_agent.enrich_ticket(ticket, TEXTE_PAGE_STANDARD, activer_rule_engine=True)

    assert "🧩" not in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_recommande_contrat():
    """contrat n'est jamais assigné dans cet agent -> client_rule DOIT se déclencher."""
    ticket = Ticket()
    ticket = promethean_agent.enrich_ticket(
        ticket, TEXTE_PAGE_STANDARD, rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert "contrat" in ticket.intervention.commentaire_interne.lower()
    assert "OD.X" in ticket.intervention.commentaire_interne


def test_aucun_champ_metier_modifie_par_le_rule_engine():
    ticket = Ticket()
    ticket = promethean_agent.enrich_ticket(
        ticket, TEXTE_PAGE_STANDARD, rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat == ""  # jamais écrasé par la recommandation


def test_desactive_par_defaut_meme_avec_rag_decision_fournie():
    ticket = Ticket()
    ticket = promethean_agent.enrich_ticket(
        ticket, TEXTE_PAGE_STANDARD, rag_decision=_rag_decision_usable()
    )

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_non_regression_scenario_piece():
    """Non-régression : le scénario 'pièce' continue de fonctionner normalement, Rule Engine actif ou non."""
    texte_piece = "Part Replacement requested.\nModel: ActiveBoard 4\nSerial Number: AB4-111\n"
    ticket = Ticket()
    ticket = promethean_agent.enrich_ticket(ticket, texte_piece, activer_rule_engine=True)

    assert "Damien C." in ticket.intervention.commentaire_interne
    assert "SUPPORT_N3" not in ticket.intervention.commentaire_interne  # pas le nom de la constante, sa valeur