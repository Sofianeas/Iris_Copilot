# tests/test_barron_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans barron_agent.py. Un seul point
# de sortie (contrairement à ADOPT/BUT) -- diff le plus simple du groupe.

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import barron_agent


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_signature_historique():
    ticket = Ticket()
    ticket.customer.enseigne = "PRIMARK"
    ticket = barron_agent.enrich_ticket(ticket, "texte quelconque")

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.intervention.contrat == "OD.BARRONM16.001.1 - Pricing FR - NBD SLA (ON DEMAND)"


def test_rule_engine_detecte_urgence():
    ticket = Ticket()
    ticket.intervention.problematique = "Panne urgente sur le TPE"
    ticket = barron_agent.enrich_ticket(ticket, "texte", activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_actif_sans_declenchement():
    ticket = Ticket()
    ticket.customer.enseigne = "PRIMARK"
    ticket = barron_agent.enrich_ticket(ticket, "texte", activer_rule_engine=True)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_recommande_contrat_si_vide():
    """Contrat déjà résolu par la logique déterministe BARRON -> client_rule ne recommande rien (champ non vide)."""
    ticket = Ticket()
    ticket.customer.enseigne = "PRIMARK"
    ticket = barron_agent.enrich_ticket(
        ticket, "texte", rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    # Le contrat BARRON est TOUJOURS déterminé par get_groupe(), jamais vide
    # -> client_rule (qui ne recommande que si contrat vide) ne se déclenche jamais ici.
    assert "contrat" not in ticket.intervention.commentaire_interne.lower() or "🧩" not in ticket.intervention.commentaire_interne
    assert ticket.intervention.contrat == "OD.BARRONM16.001.1 - Pricing FR - NBD SLA (ON DEMAND)"


def test_desactive_par_defaut_meme_avec_rag_decision_fournie():
    ticket = Ticket()
    ticket.customer.enseigne = "PRIMARK"
    ticket = barron_agent.enrich_ticket(ticket, "texte", rag_decision=_rag_decision_usable())

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_ped_toujours_remplace_meme_avec_rule_engine_actif():
    """Non-régression : la règle métier PED->TPE continue de fonctionner normalement, Rule Engine actif ou non."""
    ticket = Ticket()
    ticket.intervention.problematique = "Le PED est en panne"
    ticket = barron_agent.enrich_ticket(ticket, "texte", activer_rule_engine=True)

    assert "PED" not in ticket.intervention.problematique
    assert "TPE" in ticket.intervention.problematique