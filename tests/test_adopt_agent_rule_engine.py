# tests/test_adopt_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans adopt_agent.py. Point
# d'attention spécifique à cet agent : DEUX branches de sortie (cas
# normal, cas CATO) -- les deux doivent être couvertes séparément.

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import adopt_agent


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_signature_historique():
    ticket = Ticket()
    ticket.customer.pays = "France"
    ticket = adopt_agent.enrich_ticket(ticket, "Installation ecran standard.")

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.intervention.contrat == "On Demand France"


def test_branche_normale_urgence_declenche_rule_engine():
    ticket = Ticket()
    ticket.customer.pays = "France"
    ticket.intervention.problematique = "Panne urgente"
    ticket = adopt_agent.enrich_ticket(ticket, "texte", activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_branche_cato_rule_engine_actif_fonctionne_aussi():
    """Point d'attention spécifique ADOPT : le Rule Engine doit aussi s'exécuter dans la branche de retour anticipé CATO."""
    ticket = Ticket()
    ticket.intervention.problematique = "Installation CATO urgent"
    ticket = adopt_agent.enrich_ticket(ticket, "demande CATO urgent", activer_rule_engine=True)

    assert "CATO" in ticket.intervention.commentaire_interne
    assert "Rule Engine" in ticket.intervention.commentaire_interne


def test_branche_cato_rule_engine_inactif_par_defaut():
    ticket = Ticket()
    ticket = adopt_agent.enrich_ticket(ticket, "demande CATO")

    assert "CATO" in ticket.intervention.commentaire_interne
    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_aucun_champ_metier_modifie_par_le_rule_engine():
    ticket = Ticket()
    ticket.customer.pays = "France"
    ticket = adopt_agent.enrich_ticket(
        ticket, "texte", rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat == "On Demand France"  # jamais écrasé par une recommandation


def test_desactive_par_defaut_meme_avec_rag_decision_fournie():
    ticket = Ticket()
    ticket.customer.pays = "France"
    ticket = adopt_agent.enrich_ticket(ticket, "texte", rag_decision=_rag_decision_usable())

    assert "Rule Engine" not in ticket.intervention.commentaire_interne