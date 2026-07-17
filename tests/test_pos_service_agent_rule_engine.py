# tests/test_pos_service_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans pos_service_agent.py. Un seul
# point de sortie -- diff simple. Attention portée aux phrases "neutres"
# pour ne pas contenir accidentellement un mot-clé de scénario
# (geox/maxi zoo/onduleur/installation/demontage/reinstallation).

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import pos_service_agent


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_signature_historique():
    ticket = Ticket()
    ticket = pos_service_agent.enrich_ticket(ticket, "FRE0245 - probleme sur la caisse")

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.customer.enseigne == "Maxi Zoo"
    assert ticket.intervention.contrat == "MAINTENANCE"


def test_rule_engine_detecte_urgence():
    ticket = Ticket()
    ticket.intervention.problematique = "Panne bloquante sur le materiel"
    ticket = pos_service_agent.enrich_ticket(ticket, "GEO0188 - panne caisse", activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_actif_sans_declenchement():
    ticket = Ticket()
    ticket = pos_service_agent.enrich_ticket(ticket, "FRE0245 - probleme sur la caisse", activer_rule_engine=True)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_recommande_contrat_si_vide():
    """POS_SERVICE a toujours un contrat non-vide (chaque scénario en assigne un) -> client_rule ne se déclenche jamais ici."""
    ticket = Ticket()
    ticket = pos_service_agent.enrich_ticket(
        ticket, "FRE0245 - probleme sur la caisse", rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat  # jamais vide


def test_desactive_par_defaut_meme_avec_rag_decision_fournie():
    ticket = Ticket()
    ticket = pos_service_agent.enrich_ticket(
        ticket, "FRE0245 - probleme sur la caisse", rag_decision=_rag_decision_usable()
    )

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_non_regression_scenario_toujours_signale():
    """Non-régression : le flag SCÉNARIO déduit continue de fonctionner, Rule Engine actif ou non."""
    ticket = Ticket()
    ticket = pos_service_agent.enrich_ticket(ticket, "FRE0245 - probleme sur la caisse", activer_rule_engine=True)

    assert "SCÉNARIO déduit automatiquement" in ticket.intervention.commentaire_interne