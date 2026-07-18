# tests/test_shoppertrak_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans shoppertrak_agent.py. Un seul
# point de sortie -- diff simple. Dernier agent du Groupe A.

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import shoppertrak_agent

MAIL_TYPE = """INTER
RETAIL
NOCIBE
189
S80109419
FRANCE
GIVORS
49 Zone Industrielle du Gier
69700
Reboot de camera de comptage necessaire. Contacter Diogo
"""


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_signature_historique():
    ticket = Ticket()
    ticket = shoppertrak_agent.enrich_ticket(ticket, MAIL_TYPE)

    assert "🧩" not in ticket.intervention.commentaire_interne
    assert ticket.customer.enseigne == "NOCIBE"
    assert ticket.intervention.contrat == "OD.SHOPPE25.001.1 - ON DEMAND FRANCE (ON DEMAND)"
    # Le rappel "agent volontairement incomplet" reste present (regle metier existante,
    # non liee au Rule Engine)
    assert "volontairement incomplet" in ticket.intervention.commentaire_interne


def test_rule_engine_detecte_urgence():
    mail_urgent = MAIL_TYPE.replace("Reboot de camera", "Reboot urgent de camera")
    ticket = Ticket()
    ticket = shoppertrak_agent.enrich_ticket(ticket, mail_urgent, activer_rule_engine=True)

    assert "🧩" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_actif_sans_declenchement_urgence():
    ticket = Ticket()
    ticket = shoppertrak_agent.enrich_ticket(ticket, MAIL_TYPE, activer_rule_engine=True)

    assert "🧩" not in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_recommande_contrat_si_vide():
    """Contrat trouvé via PAYS_VERS_CONTRAT (non vide dans ce cas) -> client_rule ne se déclenche pas."""
    ticket = Ticket()
    ticket = shoppertrak_agent.enrich_ticket(
        ticket, MAIL_TYPE, rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat == "OD.SHOPPE25.001.1 - ON DEMAND FRANCE (ON DEMAND)"  # jamais écrasé


def test_desactive_par_defaut_meme_avec_rag_decision_fournie():
    ticket = Ticket()
    ticket = shoppertrak_agent.enrich_ticket(ticket, MAIL_TYPE, rag_decision=_rag_decision_usable())

    assert "🧩" not in ticket.intervention.commentaire_interne


def test_non_regression_incompletude_volontaire_toujours_signalee():
    """Non-régression : le rappel 'agent volontairement incomplet' continue de fonctionner, Rule Engine actif ou non."""
    ticket = Ticket()
    ticket = shoppertrak_agent.enrich_ticket(ticket, MAIL_TYPE, activer_rule_engine=True)

    assert "volontairement incomplet" in ticket.intervention.commentaire_interne