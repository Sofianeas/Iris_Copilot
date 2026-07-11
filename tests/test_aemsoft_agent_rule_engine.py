# tests/test_aemsoft_agent_rule_engine.py
#
# Tests de l'intégration Rule Engine dans aemsoft_agent.py (paramètres
# optionnels rag_decision / activer_rule_engine, ajoutés dans cette étape).
# Ne duplique pas les tests métier existants de l'agent (BDC, sous-type,
# etc.) -- se concentre exclusivement sur le nouveau point d'intégration.

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult
from app.agents import aemsoft_agent

MAIL_REEL = """Bonjour,

-- Bon de commande d'intervention sur site

Objet de l'intervention : C2 - PROBLEME DE COM

Site concerné par l'intervention :
BIOMONDE BOLLWILLER / 7360
10 RUE DE SOULTZ
68540 BOLLWILLER

Pers. à contacter : MARION WIESSER (GÉRANT)
Tel magasin 09 . 87 . 15 . 83 . 47
Lien de suivi du colis UPS :
https://www.ups.com/track?loc=fr_fr&tracknum=1Z17R03E0492900378

Matériel envoyé par UPS :
- 1 X 070001 INTERVENTION SUR SITE FRANCE
- 1 X 010268 BALANCE C2 TM

---- INFORMATIONS UTILES ----
Type :-Intervention J+1
Sous-Type : -Intervention Avec pièce Expédié par AEM
INSTRUCTION TECH:
Échange Balance + cable + afficheur ( durée inter 1H)
N° TPV : 2
RETOUR COLIS PAR UPS : OUI ( ETIQUETTE RETOUR DANS LE COLIS )
"""


def _rag_decision_usable(valeur: str = "OD.AEMSOFT.001") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


def test_retrocompatibilite_stricte_signature_historique():
    """Appel exactement comme avant cette étape -- comportement métier inchangé, Rule Engine jamais invoqué."""
    ticket = Ticket()
    ticket = aemsoft_agent.enrich_ticket(ticket, MAIL_REEL)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne
    assert ticket.intervention.type == "Intervention J+1"
    assert ticket.intervention.reference_materiel_client == "2"
    assert ticket.logistics.retour_piece == "Oui"


def test_rule_engine_actif_sans_declenchement():
    """activer_rule_engine=True mais aucune règle ne se déclenche (pas d'urgence, pas de rag_decision) -> rien ajouté."""
    ticket = Ticket()
    ticket = aemsoft_agent.enrich_ticket(ticket, MAIL_REEL, activer_rule_engine=True)

    assert "Rule Engine" not in ticket.intervention.commentaire_interne


def test_rule_engine_detecte_urgence():
    """Mot-clé d'urgence dans le mail -> recommandation priority_rule ajoutée à commentaire_interne."""
    mail_urgent = MAIL_REEL.replace("Échange Balance", "Échange Balance URGENT")
    ticket = Ticket()
    ticket = aemsoft_agent.enrich_ticket(ticket, mail_urgent, activer_rule_engine=True)

    assert "Rule Engine" in ticket.intervention.commentaire_interne
    assert "niveau_priorite" in ticket.intervention.commentaire_interne
    assert "Urgent" in ticket.intervention.commentaire_interne


def test_rule_engine_avec_rag_decision_recommande_contrat():
    """RagDecision usable transmise + activer_rule_engine=True -> recommandation client_rule ajoutée."""
    ticket = Ticket()
    ticket = aemsoft_agent.enrich_ticket(
        ticket, MAIL_REEL, rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert "contrat" in ticket.intervention.commentaire_interne.lower()
    assert "OD.AEMSOFT.001" in ticket.intervention.commentaire_interne


def test_aucun_champ_metier_modifie_par_le_rule_engine():
    """Même avec une recommandation de contrat produite, le champ contrat lui-même n'est JAMAIS écrasé."""
    ticket = Ticket()
    ticket = aemsoft_agent.enrich_ticket(
        ticket, MAIL_REEL, rag_decision=_rag_decision_usable(), activer_rule_engine=True
    )

    assert ticket.intervention.contrat == ""  # jamais écrasé, uniquement suggéré en commentaire


def test_desactive_par_defaut_meme_avec_rag_decision_fournie():
    """rag_decision fourni mais activer_rule_engine omis (défaut False) -> aucune tentative, comportement inerte."""
    ticket = Ticket()
    ticket = aemsoft_agent.enrich_ticket(ticket, MAIL_REEL, rag_decision=_rag_decision_usable())

    assert "Rule Engine" not in ticket.intervention.commentaire_interne