# tests/test_but_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans but_agent.py. Point d'attention
# spécifique : DEUX branches de sortie (matériel non détecté = retour
# anticipé, matériel détecté = fin normale) -- les deux doivent être
# couvertes séparément.

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import but_agent


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_branche_normale():
    ticket = Ticket()
    ticket.customer.ville = "CHAUMONT"
    ticket.customer.code_site = "062"
    ticket = but_agent.enrich_ticket(ticket, "La caisse n°1 ne fonctionne plus.")

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.intervention.contrat == "CT.BUTINT17.001.1 - CONTRAT MCO"


def test_retrocompatibilite_stricte_branche_materiel_non_detecte():
    ticket = Ticket()
    ticket = but_agent.enrich_ticket(ticket, "Demande generique sans mot-cle materiel.")

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert "non détecté automatiquement" in ticket.intervention.commentaire_interne


def test_branche_normale_urgence_declenche_rule_engine():
    ticket = Ticket()
    ticket.intervention.problematique = "Panne urgente de la caisse"
    ticket = but_agent.enrich_ticket(ticket, "La caisse n°1 est en panne urgente.", activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_branche_materiel_non_detecte_rule_engine_actif_fonctionne_aussi():
    """Point d'attention spécifique BUT : le Rule Engine doit aussi s'exécuter dans la branche de retour anticipé."""
    ticket = Ticket()
    ticket.intervention.problematique = "Probleme urgent, materiel non precise"
    ticket = but_agent.enrich_ticket(ticket, "Demande generique urgente sans mot-cle materiel.", activer_rule_engine=True)

    assert "non détecté automatiquement" in ticket.intervention.commentaire_interne
    assert "Rule Engine" in ticket.intervention.commentaire_interne


def test_branche_materiel_non_detecte_rule_engine_inactif_par_defaut():
    ticket = Ticket()
    ticket = but_agent.enrich_ticket(ticket, "Demande generique urgente sans mot-cle materiel.")

    assert "non détecté automatiquement" in ticket.intervention.commentaire_interne
    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_aucun_champ_metier_modifie_par_le_rule_engine():
    ticket = Ticket()
    ticket.customer.ville = "CHAUMONT"
    ticket = but_agent.enrich_ticket(
        ticket, "La caisse n°1 ne fonctionne plus.", rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat == "CT.BUTINT17.001.1 - CONTRAT MCO"  # jamais écrasé