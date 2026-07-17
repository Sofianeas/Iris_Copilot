# tests/test_amplifon_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans amplifon_agent.py. Un seul
# point de sortie (les 4 modèles A/B/C/D convergent) -- diff simple.

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import amplifon_agent


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_signature_historique():
    ticket = Ticket()
    ticket = amplifon_agent.enrich_ticket(ticket, "BDC 4866 - demande generique")

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.intervention.contrat == "IMAC"
    assert ticket.intervention.categorie == "Expédition matériel sans intégration"  # modèle A par défaut


def test_rule_engine_detecte_urgence():
    ticket = Ticket()
    ticket.intervention.problematique = "Panne critique du materiel"
    ticket = amplifon_agent.enrich_ticket(ticket, "BDC 4866 - demande", activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_actif_sans_declenchement():
    ticket = Ticket()
    ticket = amplifon_agent.enrich_ticket(ticket, "BDC 4866 - demande generique", activer_rule_engine=True)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_recommande_contrat_si_vide():
    """AMPLIFON a toujours contrat='IMAC' (jamais vide) -> client_rule ne se déclenche jamais ici."""
    ticket = Ticket()
    ticket = amplifon_agent.enrich_ticket(
        ticket, "BDC 4866 - demande", rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat == "IMAC"  # jamais écrasé


def test_desactive_par_defaut_meme_avec_rag_decision_fournie():
    ticket = Ticket()
    ticket = amplifon_agent.enrich_ticket(ticket, "BDC 4866 - demande", rag_decision=_rag_decision_usable())

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_non_regression_modele_incident_toujours_signale():
    """Non-régression : le flag MODÈLE D'INCIDENT continue de fonctionner, Rule Engine actif ou non."""
    ticket = Ticket()
    ticket = amplifon_agent.enrich_ticket(ticket, "BDC 4866 - demande generique", activer_rule_engine=True)

    assert "MODÈLE D'INCIDENT déduit automatiquement" in ticket.intervention.commentaire_interne


def test_non_regression_modele_d_imprimante_lourde():
    """Non-régression : la détection imprimante lourde (Ricoh) continue de fonctionner, Rule Engine actif."""
    ticket = Ticket()
    ticket = amplifon_agent.enrich_ticket(
        ticket, "BDC 4715 - installation Epson avec reprise Ricoh 305", activer_rule_engine=True
    )

    assert "NVA" in ticket.intervention.commentaire_interne
    assert "PGU" in ticket.intervention.commentaire_interne