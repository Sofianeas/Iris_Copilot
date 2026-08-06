# tests/compatibility/test_rule_adapters_compatibility.py
#
# Suite officielle de certification de compatibilité ascendante entre
# l'ancien Framework des Rules (fonctions nues `evaluer()`) et le nouveau
# contrat BaseRule (P3-430). Aucune Rule métier, aucun Agent, aucun
# Service n'est modifié par cette suite.

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket
from app.rules.client_rule import ClientRule, evaluer as evaluer_client
from app.rules.priority_rule import PriorityRule, evaluer as evaluer_priority
from app.services import rule_engine
from app.services.rag_fallback_service import RagResult


def _ticket_urgent() -> Ticket:
    ticket = Ticket()
    ticket.intervention.problematique = "Panne urgente sur le TPE"
    return ticket


def _rag_decision_usable(valeur: str = "OD.X") -> RagDecision:
    return RagDecision(
        usable=True, reason="tous_criteres_satisfaits",
        result=RagResult(found=True, value=valeur, source="docx:x.docx", score=0.9, chunk_id="id-1"),
    )


# --------------------------------------------------------------------------
# PriorityRule : evaluate() vs evaluer() -- résultats strictement identiques
# --------------------------------------------------------------------------

def test_priority_rule_evaluate_fonctionne():
    resultat = PriorityRule().evaluate(_ticket_urgent(), None)

    assert len(resultat) == 1
    assert resultat[0].field == "niveau_priorite"
    assert resultat[0].value == "Urgent"


def test_priority_rule_evaluer_delegue_correctement():
    resultat = evaluer_priority(_ticket_urgent())

    assert len(resultat) == 1
    assert resultat[0].field == "niveau_priorite"
    assert resultat[0].value == "Urgent"


def test_priority_rule_evaluate_et_evaluer_produisent_le_meme_resultat():
    ticket_a = _ticket_urgent()
    ticket_b = _ticket_urgent()

    resultat_classe = PriorityRule().evaluate(ticket_a, None)
    resultat_adaptateur = evaluer_priority(ticket_b)

    assert resultat_classe == resultat_adaptateur


def test_priority_rule_evaluate_et_evaluer_identiques_cas_negatif():
    """Sans mot-clé d'urgence, les deux chemins retournent une liste vide identique."""
    ticket_a = Ticket()
    ticket_b = Ticket()

    assert PriorityRule().evaluate(ticket_a, None) == evaluer_priority(ticket_b) == []


# --------------------------------------------------------------------------
# ClientRule : evaluate() vs evaluer() -- résultats strictement identiques
# --------------------------------------------------------------------------

def test_client_rule_evaluate_fonctionne():
    rag_decision = _rag_decision_usable()
    resultat = ClientRule().evaluate(Ticket(), rag_decision)

    assert len(resultat) == 1
    assert resultat[0].field == "contrat"
    assert resultat[0].value == "OD.X"


def test_client_rule_evaluer_delegue_correctement():
    rag_decision = _rag_decision_usable()
    resultat = evaluer_client(Ticket(), rag_decision)

    assert len(resultat) == 1
    assert resultat[0].field == "contrat"
    assert resultat[0].value == "OD.X"


def test_client_rule_evaluate_et_evaluer_produisent_le_meme_resultat():
    rag_decision = _rag_decision_usable()

    resultat_classe = ClientRule().evaluate(Ticket(), rag_decision)
    resultat_adaptateur = evaluer_client(Ticket(), rag_decision)

    assert resultat_classe == resultat_adaptateur


def test_client_rule_evaluate_et_evaluer_identiques_contrat_deja_rempli():
    """Contrat déjà renseigné sur le ticket -- les deux chemins retournent une liste vide identique."""
    ticket_a = Ticket()
    ticket_a.intervention.contrat = "Deja rempli"
    ticket_b = Ticket()
    ticket_b.intervention.contrat = "Deja rempli"
    rag_decision = _rag_decision_usable()

    assert ClientRule().evaluate(ticket_a, rag_decision) == evaluer_client(ticket_b, rag_decision) == []


# --------------------------------------------------------------------------
# Rule Engine : accepte BaseRule, fonctions historiques, et un mélange
# --------------------------------------------------------------------------

def test_rule_engine_accepte_des_instances_base_rule():
    original = rule_engine.REGLES
    rule_engine.REGLES = [PriorityRule(), ClientRule()]
    try:
        resultat = rule_engine.executer(_ticket_urgent(), None)
        assert any(r.field == "niveau_priorite" for r in resultat)
    finally:
        rule_engine.REGLES = original


def test_rule_engine_accepte_des_fonctions_historiques():
    original = rule_engine.REGLES
    rule_engine.REGLES = [evaluer_priority, evaluer_client]
    try:
        resultat = rule_engine.executer(_ticket_urgent(), None)
        assert any(r.field == "niveau_priorite" for r in resultat)
    finally:
        rule_engine.REGLES = original


def test_rule_engine_accepte_un_registre_mixte():
    """BaseRule ET fonction historique dans le même registre -- aucune erreur, résultats des deux collectés."""
    original = rule_engine.REGLES
    rule_engine.REGLES = [PriorityRule(), evaluer_client]
    try:
        ticket = _ticket_urgent()
        resultat = rule_engine.executer(ticket, _rag_decision_usable())
        champs = {r.field for r in resultat}
        assert "niveau_priorite" in champs
        assert "contrat" in champs
    finally:
        rule_engine.REGLES = original


def test_rule_engine_produit_les_memes_recommandations_avant_apres_harmonisation():
    """Le registre officiel actuel (post-harmonisation) produit les mêmes recommandations qu'un registre 100% fonctions (pré-harmonisation), sur le même ticket."""
    original = rule_engine.REGLES

    ticket_post = _ticket_urgent()
    rule_engine.REGLES = [PriorityRule(), ClientRule()]
    resultat_post = rule_engine.executer(ticket_post, _rag_decision_usable())

    ticket_pre = _ticket_urgent()
    rule_engine.REGLES = [evaluer_priority, evaluer_client]
    resultat_pre = rule_engine.executer(ticket_pre, _rag_decision_usable())

    rule_engine.REGLES = original

    assert resultat_post == resultat_pre


# --------------------------------------------------------------------------
# Non-régression : exception, doublons, registre mixte, ordre d'exécution
# --------------------------------------------------------------------------

def test_non_regression_regle_qui_leve_exception_est_ignoree():
    def regle_cassee(ticket, rag_decision):
        raise ValueError("erreur simulee")

    original = rule_engine.REGLES
    rule_engine.REGLES = [PriorityRule(), regle_cassee]
    try:
        resultat = rule_engine.executer(_ticket_urgent(), None)
        # la regle cassee n'interrompt pas l'execution des autres
        assert any(r.field == "niveau_priorite" for r in resultat)
    finally:
        rule_engine.REGLES = original


def test_non_regression_doublons_sont_deduplique():
    original = rule_engine.REGLES
    rule_engine.REGLES = [PriorityRule(), PriorityRule()]  # meme regle enregistree 2 fois
    try:
        resultat = rule_engine.executer(_ticket_urgent(), None)
        # meme si la regle est enregistree 2 fois, la recommandation identique n'apparait qu'une fois
        assert len(resultat) == 1
    finally:
        rule_engine.REGLES = original


def test_non_regression_registre_mixte_sans_erreur():
    def regle_fonction_simple(ticket, rag_decision):
        return [RuleRecommendation(field="test", value="1", confidence=0.5, source="test", reason="test")]

    original = rule_engine.REGLES
    rule_engine.REGLES = [PriorityRule(), regle_fonction_simple, ClientRule()]
    try:
        resultat = rule_engine.executer(_ticket_urgent(), _rag_decision_usable())
        champs = {r.field for r in resultat}
        assert {"niveau_priorite", "test", "contrat"}.issubset(champs)
    finally:
        rule_engine.REGLES = original


def test_non_regression_ordre_execution_conserve():
    """Les recommandations apparaissent dans l'ordre des règles du registre (pas réordonnées)."""
    ordre_appel: list[str] = []

    def regle_a(ticket, rag_decision):
        ordre_appel.append("a")
        return [RuleRecommendation(field="a", value="1", confidence=0.5, source="test", reason="test")]

    def regle_b(ticket, rag_decision):
        ordre_appel.append("b")
        return [RuleRecommendation(field="b", value="1", confidence=0.5, source="test", reason="test")]

    original = rule_engine.REGLES
    rule_engine.REGLES = [regle_a, regle_b]
    try:
        resultat = rule_engine.executer(Ticket(), None)
        assert ordre_appel == ["a", "b"]
        assert [r.field for r in resultat] == ["a", "b"]
    finally:
        rule_engine.REGLES = original