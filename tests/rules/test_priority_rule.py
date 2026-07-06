# tests/rules/test_priority_rule.py
#
# Tests unitaires ISOLÉS de app/rules/priority_rule.py -- n'impliquent
# jamais rule_engine.py (couvert séparément par tests/test_rule_engine.py).

import pytest

from app.models.rag_decision import RagDecision
from app.models.ticket import Ticket
from app.rules.priority_rule import evaluer
from app.services.rag_fallback_service import RagResult


def _ticket_avec_problematique(texte: str) -> Ticket:
    ticket = Ticket()
    ticket.intervention.problematique = texte
    return ticket


# --------------------------------------------------------------------------
# Fonctionnement nominal
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "mot_cle", ["urgent", "URGENT", "Urgent", "critique", "bloquant", "arret complet", "arrêt complet"]
)
def test_fonctionnement_nominal_detection_urgence(mot_cle):
    """Chaque mot-clé d'urgence connu (insensible à la casse) déclenche exactement 1 recommandation."""
    ticket = _ticket_avec_problematique(f"Le site signale un problème {mot_cle} sur la caisse.")
    recos = evaluer(ticket, None)

    assert len(recos) == 1
    assert recos[0].field == "niveau_priorite"
    assert recos[0].value == "Urgent"


# --------------------------------------------------------------------------
# Absence de recommandations
# --------------------------------------------------------------------------

def test_absence_de_recommandation_sans_mot_cle():
    """Aucun mot-clé d'urgence dans la Problématique -> liste vide."""
    ticket = _ticket_avec_problematique("Le clavier de la caisse ne répond plus depuis ce matin.")
    recos = evaluer(ticket, None)

    assert recos == []


# --------------------------------------------------------------------------
# Cas limites
# --------------------------------------------------------------------------

def test_cas_limite_problematique_vide():
    """Problématique vide (défaut du Ticket) -> liste vide, jamais d'exception."""
    ticket = Ticket()
    recos = evaluer(ticket, None)

    assert recos == []


def test_cas_limite_mot_cle_en_sous_chaine_dun_autre_mot():
    """
    Vérifie qu'un mot-clé détecté en sous-chaîne d'un mot plus long ne
    casse rien (comportement actuel : détection par sous-chaîne simple,
    donc "urgentissime" déclenche aussi -- documenté ici comme
    comportement CONNU, pas un bug : la règle est volontairement permissive
    plutôt que de risquer de rater une vraie urgence par un matching trop strict).
    """
    ticket = _ticket_avec_problematique("Demande urgentissime de la direction.")
    recos = evaluer(ticket, None)

    assert len(recos) == 1  # comportement documenté, pas un test de rejet


# --------------------------------------------------------------------------
# Indépendance vis-à-vis de RagDecision
# --------------------------------------------------------------------------

def test_independance_vis_a_vis_de_rag_decision():
    """
    Cette règle ne dépend QUE du Ticket -- une RagDecision (usable ou non,
    voire absente) ne doit avoir strictement aucun effet sur son résultat.
    """
    ticket = _ticket_avec_problematique("Panne urgente sur site.")

    decision_usable = RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value="x", source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )
    decision_non_usable = RagDecision(usable=False, reason="resultat_non_trouve", result=None)

    recos_sans = evaluer(ticket, None)
    recos_avec_usable = evaluer(ticket, decision_usable)
    recos_avec_non_usable = evaluer(ticket, decision_non_usable)

    assert recos_sans == recos_avec_usable == recos_avec_non_usable


# --------------------------------------------------------------------------
# Traçabilité
# --------------------------------------------------------------------------

def test_tracabilite_de_la_recommandation():
    """La recommandation produite possède systématiquement source/reason non vides et une confiance ∈ [0, 1]."""
    ticket = _ticket_avec_problematique("Incident critique en boutique.")
    recos = evaluer(ticket, None)

    assert recos[0].source
    assert recos[0].reason
    assert 0.0 <= recos[0].confidence <= 1.0