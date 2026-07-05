"""
app/services/rag_decision_service.py

Applique TOUS les critères de validation configurés (cf.
app.config.rag_settings) à un RagResult déjà obtenu par
rag_fallback_service.tenter_fallback_rag, et retourne la décision finale
d'utilisabilité sous forme de RagDecision.

Ne modifie jamais rien. Ne connaît ni Ticket ni Agent. Fonction pure :
même entrée (RagResult + config) -> même sortie (RagDecision), aucun effet
de bord autre que le logging.

Critères appliqués, dans cet ordre (court-circuit au premier échec, chaque
échec produit une `reason` explicite et unique pour rester traçable) :
  1. ENABLE_RAG (interrupteur global)
  2. result.found (résultat non vide)
  3. valeur obligatoire (result.value)
  4. source obligatoire (result.source)
  5. chunk obligatoire (result.chunk_id)
  6. score minimal (result.score >= MIN_SCORE)
  7. document autorisé (type de source ∈ AUTHORIZED_SOURCES)
  -> si tout passe : usable=True.
"""

import logging

import app.config.rag_settings as rag_settings
from app.models.rag_decision import RagDecision
from app.services.rag_fallback_service import RagResult

logger = logging.getLogger("iris_copilot.rag_decision")


def evaluer_resultat(result: RagResult) -> RagDecision:
    """
    Évalue un RagResult déjà obtenu contre tous les critères de
    configuration actuels et retourne la RagDecision correspondante.

    Ne lève jamais d'exception : toute entrée, même malformée (ce qui ne
    devrait pas arriver vu le contrat de RagResult, mais on ne fait jamais
    une confiance aveugle), produit une RagDecision -- jamais un crash.
    """
    if not rag_settings.ENABLE_RAG:
        decision = RagDecision(usable=False, reason="rag_desactive_par_configuration", result=result)
        logger.info("decision usable=%s reason=%s", decision.usable, decision.reason)
        return decision

    if not result.found:
        decision = RagDecision(usable=False, reason="resultat_non_trouve", result=result)
        logger.info("decision usable=%s reason=%s", decision.usable, decision.reason)
        return decision

    if not result.value:
        decision = RagDecision(usable=False, reason="valeur_absente", result=result)
        logger.info("decision usable=%s reason=%s", decision.usable, decision.reason)
        return decision

    if not result.source:
        decision = RagDecision(usable=False, reason="source_absente", result=result)
        logger.info("decision usable=%s reason=%s", decision.usable, decision.reason)
        return decision

    if not result.chunk_id:
        decision = RagDecision(usable=False, reason="chunk_absent", result=result)
        logger.info("decision usable=%s reason=%s", decision.usable, decision.reason)
        return decision

    if result.score is None or result.score < rag_settings.MIN_SCORE:
        decision = RagDecision(
            usable=False,
            reason=f"score_insuffisant ({result.score!r} < {rag_settings.MIN_SCORE!r})",
            result=result,
        )
        logger.info("decision usable=%s reason=%s", decision.usable, decision.reason)
        return decision

    type_source = result.source.split(":", 1)[0] if ":" in result.source else ""
    if type_source not in rag_settings.AUTHORIZED_SOURCES:
        decision = RagDecision(
            usable=False,
            reason=f"document_non_autorise (type={type_source!r})",
            result=result,
        )
        logger.info("decision usable=%s reason=%s", decision.usable, decision.reason)
        return decision

    decision = RagDecision(usable=True, reason="tous_criteres_satisfaits", result=result)
    logger.info("decision usable=%s reason=%s", decision.usable, decision.reason)
    return decision