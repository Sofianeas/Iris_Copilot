# tests/test_rule_engine.py
#
# Tests de l'AGRÉGATEUR app/services/rule_engine.py -- les règles
# individuelles sont testées isolément dans tests/rules/.

import dataclasses
import logging

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket
from app.services import rule_engine
from app.services.rag_fallback_service import RagResult
from app.services.rule_engine import executer


class CapteurDeLogs(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _decision_usable() -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value="OD.TEST.001", source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


# --------------------------------------------------------------------------
# Fonctionnement nominal
# --------------------------------------------------------------------------

def test_fonctionnement_nominal_une_regle_declenchee():
    ticket = Ticket()
    ticket.intervention.problematique = "Panne urgente en magasin."
    recos = executer(ticket)

    assert len(recos) == 1
    assert recos[0].field == "niveau_priorite"


# --------------------------------------------------------------------------
# Recommandations multiples
# --------------------------------------------------------------------------

def test_recommandations_multiples_deux_regles_declenchees():
    ticket = Ticket()
    ticket.intervention.problematique = "Panne urgente en magasin."
    # contrat vide par défaut -> client_rule se déclenche aussi si RagDecision usable
    recos = executer(ticket, _decision_usable())

    champs = {r.field for r in recos}
    assert champs == {"niveau_priorite", "contrat"}


# --------------------------------------------------------------------------
# Absence de recommandations
# --------------------------------------------------------------------------

def test_absence_de_recommandations_ticket_neutre():
    ticket = Ticket()
    ticket.intervention.problematique = "RAS, ticket de routine."
    ticket.intervention.contrat = "Contrat déjà résolu"
    recos = executer(ticket, None)

    assert recos == []


# --------------------------------------------------------------------------
# Déduplication
# --------------------------------------------------------------------------

def test_deduplication(monkeypatch):
    """2 règles produisant la MÊME recommandation exacte (field+value+source) -> une seule conservée."""
    def regle_doublon_a(ticket, rag_decision):
        return [RuleRecommendation(field="x", value="y", confidence=0.5, source="src", reason="r1")]

    def regle_doublon_b(ticket, rag_decision):
        return [RuleRecommendation(field="x", value="y", confidence=0.5, source="src", reason="r2")]

    monkeypatch.setattr(rule_engine, "REGLES", [regle_doublon_a, regle_doublon_b])

    recos = executer(Ticket())

    assert len(recos) == 1


# --------------------------------------------------------------------------
# Isolation des exceptions
# --------------------------------------------------------------------------

def test_isolation_des_exceptions(monkeypatch):
    """Une règle qui lève une exception n'empêche jamais les autres règles de produire leurs recommandations."""
    def regle_cassee(ticket, rag_decision):
        raise ValueError("panne simulée")

    def regle_fiable(ticket, rag_decision):
        return [RuleRecommendation(field="champ_ok", value="v", confidence=0.5, source="src", reason="r")]

    monkeypatch.setattr(rule_engine, "REGLES", [regle_cassee, regle_fiable])

    recos = executer(Ticket())  # ne doit PAS lever

    assert len(recos) == 1
    assert recos[0].field == "champ_ok"


def test_regle_retournant_un_type_invalide_est_ignoree(monkeypatch):
    """Défense en profondeur : une règle qui viole son contrat (ne retourne pas une liste) est ignorée, jamais propagée."""
    def regle_invalide(ticket, rag_decision):
        return "ceci n'est pas une liste"  # violation du contrat RegleFn

    monkeypatch.setattr(rule_engine, "REGLES", [regle_invalide])

    recos = executer(Ticket())  # ne doit pas lever

    assert recos == []


# --------------------------------------------------------------------------
# Aucune modification du Ticket
# --------------------------------------------------------------------------

def test_aucune_modification_du_ticket():
    ticket = Ticket()
    ticket.intervention.problematique = "urgent, panne totale"
    ticket.customer.ville = "Lyon"
    avant = dataclasses.asdict(ticket)

    executer(ticket, _decision_usable())

    apres = dataclasses.asdict(ticket)
    assert avant == apres


# --------------------------------------------------------------------------
# Traçabilité
# --------------------------------------------------------------------------

def test_tracabilite_des_recommandations():
    ticket = Ticket()
    ticket.intervention.problematique = "urgent"
    recos = executer(ticket, _decision_usable())

    for reco in recos:
        assert reco.source
        assert reco.reason
        assert 0.0 <= reco.confidence <= 1.0


# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

def test_logging_emis_pour_chaque_regle_et_le_total():
    capteur = CapteurDeLogs()
    capteur.setLevel(logging.INFO)
    logger = logging.getLogger("iris_copilot.rule_engine")
    logger.addHandler(capteur)
    logger.setLevel(logging.INFO)
    try:
        executer(Ticket())
    finally:
        logger.removeHandler(capteur)

    messages = [r.getMessage() for r in capteur.records]
    assert any("regle=" in m for m in messages)
    assert any("total_deduplique=" in m for m in messages)


# --------------------------------------------------------------------------
# Déterminisme
# --------------------------------------------------------------------------

def test_determinisme_meme_entree_meme_sortie():
    ticket = Ticket()
    ticket.intervention.problematique = "urgent"
    decision = _decision_usable()

    recos_1 = executer(ticket, decision)
    recos_2 = executer(ticket, decision)

    assert recos_1 == recos_2