# tests/test_innovorder_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans innovorder_agent.py. Un seul
# point de sortie -- diff simple comme BARRON.

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import innovorder_agent


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_signature_historique():
    ticket = Ticket()
    ticket.intervention.intitule = "Bagel corner Biganos - probleme"
    ticket = innovorder_agent.enrich_ticket(ticket, "123456 - probleme electrique")

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.intervention.contrat == "Maintenance France"


def test_rule_engine_detecte_urgence():
    ticket = Ticket()
    ticket.intervention.problematique = "Situation critique en boutique"
    ticket = innovorder_agent.enrich_ticket(ticket, "texte", activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_recommande_contrat_si_vide():
    """INNOVORDER a toujours un contrat non-vide (détecter_contrat retombe sur Maintenance France par défaut) -> client_rule ne se déclenche jamais ici."""
    ticket = Ticket()
    ticket = innovorder_agent.enrich_ticket(
        ticket, "texte", rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat  # jamais vide
    assert "🧩" not in ticket.intervention.commentaire_interne or "contrat" not in [
        l.split("'")[1].lower() for l in ticket.intervention.commentaire_interne.splitlines() if l.startswith("- Champ")
    ]


def test_desactive_par_defaut_meme_avec_rag_decision_fournie():
    ticket = Ticket()
    ticket = innovorder_agent.enrich_ticket(ticket, "texte", rag_decision=_rag_decision_usable())

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_non_regression_contrat_par_defaut_toujours_signale():
    """Non-régression : le flag 'contrat retenu par défaut' continue de fonctionner, Rule Engine actif ou non."""
    ticket = Ticket()
    ticket = innovorder_agent.enrich_ticket(ticket, "texte de test générique sans mot déclencheur", activer_rule_engine=True)

    assert "retenu PAR DÉFAUT" in ticket.intervention.commentaire_interne