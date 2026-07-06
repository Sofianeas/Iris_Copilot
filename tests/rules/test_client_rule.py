# tests/rules/test_client_rule.py
#
# Tests unitaires ISOLÉS de app/rules/client_rule.py -- n'impliquent jamais
# rule_engine.py (couvert séparément par tests/test_rule_engine.py).

from app.models.rag_decision import RagDecision
from app.models.ticket import Ticket
from app.rules.client_rule import CONFIANCE_MAX_RAG, evaluer
from app.services.rag_fallback_service import RagResult


def _decision_usable(score: float | None = 0.9, valeur: str = "OD.TEST.001", source: str = "docx:x.docx") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source=source, score=score, chunk_id="id-1"),
    )


# --------------------------------------------------------------------------
# Fonctionnement nominal
# --------------------------------------------------------------------------

def test_fonctionnement_nominal_contrat_manquant_rag_usable():
    ticket = Ticket()  # contrat="" par défaut
    recos = evaluer(ticket, _decision_usable())

    assert len(recos) == 1
    assert recos[0].field == "contrat"
    assert recos[0].value == "OD.TEST.001"
    assert recos[0].source == "docx:x.docx"


# --------------------------------------------------------------------------
# Absence de recommandations
# --------------------------------------------------------------------------

def test_absence_de_recommandation_si_contrat_deja_rempli():
    """Le déterministe prime : contrat déjà résolu -> aucune recommandation, même avec une RagDecision par ailleurs parfaite."""
    ticket = Ticket()
    ticket.intervention.contrat = "Contrat déjà décidé par l'agent"
    recos = evaluer(ticket, _decision_usable())

    assert recos == []


def test_absence_de_recommandation_si_rag_decision_none():
    ticket = Ticket()
    recos = evaluer(ticket, None)

    assert recos == []


def test_absence_de_recommandation_si_rag_decision_non_usable():
    ticket = Ticket()
    decision = RagDecision(usable=False, reason="resultat_non_trouve", result=None)
    recos = evaluer(ticket, decision)

    assert recos == []


# --------------------------------------------------------------------------
# Cas limites
# --------------------------------------------------------------------------

def test_cas_limite_confiance_plafonnee_meme_avec_score_parfait():
    """Même avec un score de retrieval de 1.0, la confiance ne dépasse jamais CONFIANCE_MAX_RAG (0.6)."""
    ticket = Ticket()
    recos = evaluer(ticket, _decision_usable(score=1.0))

    assert recos[0].confidence == CONFIANCE_MAX_RAG


def test_cas_limite_score_none_utilise_confiance_max_par_defaut():
    """
    Cas défensif (ne devrait pas arriver vu le contrat RagDecision quand
    usable=True, mais on ne fait jamais une confiance aveugle même à notre
    propre contrat interne) : score=None -> confiance = CONFIANCE_MAX_RAG,
    jamais un crash.
    """
    ticket = Ticket()
    decision = _decision_usable(score=None)
    recos = evaluer(ticket, decision)

    assert recos[0].confidence == CONFIANCE_MAX_RAG


# --------------------------------------------------------------------------
# Traçabilité
# --------------------------------------------------------------------------

def test_tracabilite_de_la_recommandation():
    ticket = Ticket()
    recos = evaluer(ticket, _decision_usable())

    assert recos[0].source
    assert recos[0].reason
    assert 0.0 <= recos[0].confidence <= 1.0