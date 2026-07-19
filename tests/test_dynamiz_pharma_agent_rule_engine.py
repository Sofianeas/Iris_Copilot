# tests/test_dynamiz_pharma_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans dynamiz_pharma_agent.py
# (Groupe B, signature : enrich_ticket(ticket, texte_source, fichier_excel)).
#
# ⚠️ Texte synthétique minimal -- ne revalide PAS la logique de parsing
# déjà testée par ailleurs. Particularité de cet agent : CONTRAT_DYNAMIZ
# n'est jamais assigné -> client_rule DOIT se déclencher (contrairement à
# la majorité des autres agents où le contrat est toujours pré-rempli).

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import dynamiz_pharma_agent


def _texte_synthetique(contexte="Probleme standard sur site."):
    return f"""Client à facturer
Nom : SITE TEST - code client : 1234567
Intitulé de la demande (SAV, INSTALLATION, PREVISITE)
SAV
Description de la demande (ce qui sera visible du technicien)
Contexte:
{contexte}

Intervention à réaliser:
Verifier le materiel.

Numéro incident client
Normal
Site d'intervention
Code site

Adresse
1 RUE DE TEST

CP: 75000                             VILLE: PARIS
Nom point de vente
SITE TEST
Contact sur site 
M TEST
telephone
0100000000
"""


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_signature_historique():
    ticket = Ticket()
    ticket = dynamiz_pharma_agent.enrich_ticket(ticket, _texte_synthetique())

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.customer.client == "DYNAMIZ"
    assert ticket.procedure.procedure is False  # règle unique DYNAMIZ, non liée au Rule Engine


def test_rule_engine_detecte_urgence():
    ticket = Ticket()
    texte = _texte_synthetique(contexte="Probleme urgent, arret complet du systeme.")
    ticket = dynamiz_pharma_agent.enrich_ticket(ticket, texte, activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_actif_sans_declenchement_urgence():
    ticket = Ticket()
    ticket = dynamiz_pharma_agent.enrich_ticket(ticket, _texte_synthetique(), activer_rule_engine=True, rag_decision=None)

    # Pas d'urgence, pas de rag_decision -> aucune recommandation
    assert "🧩" not in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_recommande_contrat():
    """CONTRAT_DYNAMIZ n'est jamais assigné -> client_rule DOIT se déclencher ici."""
    ticket = Ticket()
    ticket = dynamiz_pharma_agent.enrich_ticket(
        ticket, _texte_synthetique(), rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert "contrat" in ticket.intervention.commentaire_interne.lower()
    assert "OD.X" in ticket.intervention.commentaire_interne


def test_aucun_champ_metier_modifie_par_le_rule_engine():
    ticket = Ticket()
    ticket = dynamiz_pharma_agent.enrich_ticket(
        ticket, _texte_synthetique(), rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat == ""  # jamais écrasé par la recommandation


def test_desactive_par_defaut_meme_avec_rag_decision_fournie():
    ticket = Ticket()
    ticket = dynamiz_pharma_agent.enrich_ticket(
        ticket, _texte_synthetique(), rag_decision=_rag_decision_usable()
    )

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_non_regression_procedure_toujours_non():
    """Non-régression : la règle unique 'Procédure = Non par défaut' continue de fonctionner, Rule Engine actif ou non."""
    ticket = Ticket()
    ticket = dynamiz_pharma_agent.enrich_ticket(
        ticket, _texte_synthetique(), rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.procedure.procedure is False