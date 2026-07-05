"""
Couche d'intégration SAFE MODE entre les agents et la couche RAG.

Politique stricte (architecture validée avec Sofiane) :
- SEULE cette couche a le droit de connaître les modèles métier (`Ticket`).
  `rag_fallback_service.py` et `rag_decision_service.py` restent purement
  consultatifs -- aucun des deux ne connaît Ticket ni Agent.
- Cette couche ne modifie JAMAIS un champ métier du Ticket, quelle que
  soit la pertinence du résultat RAG.
- Elle enrichit UNIQUEMENT `ticket.intervention.commentaire_interne`,
  toujours sous forme de suggestion explicitement marquée non vérifiée --
  jamais présentée comme une donnée validée.
- Elle ne fait confiance qu'à `RagDecision` (jamais à `RagResult`
  directement) : la décision d'utilisabilité vit exclusivement dans
  `rag_decision_service.evaluer_resultat`, pas ici. Cette couche se
  contente d'appliquer la décision (écrire ou non dans commentaire_interne),
  jamais de la recalculer.

Logging : ce module logge le niveau APPLICATION (utilisé/ignoré côté
ticket + raison). Le niveau RETRIEVAL est loggé par rag_fallback_service.py,
le niveau DÉCISION par rag_decision_service.py -- pas de duplication,
chaque couche logge ce qui relève de sa propre responsabilité.
"""

import logging
from pathlib import Path

import app.config.rag_settings as rag_settings
from app.models.ticket import Ticket
from app.services.rag_decision_service import evaluer_resultat
from app.services.rag_fallback_service import tenter_fallback_rag
from app.services.vectorstore_service import EmbedFn, embed_texts_gemini

logger = logging.getLogger("iris_copilot.rag_integration")


def _ajouter_si_absent(texte_existant: str, bloc: str) -> str:
    """Même convention que tous les agents -- idempotence, jamais de doublon."""
    if not bloc:
        return texte_existant
    if texte_existant and bloc in texte_existant:
        return texte_existant
    if texte_existant:
        return f"{texte_existant.strip()}\n\n{bloc}"
    return bloc


def enrichir_commentaire_si_pertinent(
    ticket: Ticket,
    champ_manquant: str,
    valeur_actuelle: str,
    client: str,
    question: str,
    dossier_persistance: Path | None,
    embed_fn: EmbedFn = embed_texts_gemini,
) -> None:
    """
    Point d'entrée unique que les agents doivent utiliser (jamais
    `rag_fallback_service.tenter_fallback_rag` ni
    `rag_decision_service.evaluer_resultat` directement depuis un agent).

    Ne modifie JAMAIS un champ métier -- enrichit uniquement
    `commentaire_interne`, et seulement si (a) `valeur_actuelle` est vide
    ET (b) `rag_decision_service.evaluer_resultat` juge le résultat
    utilisable. Ne lève jamais d'exception.

    `dossier_persistance=None` -> aucune tentative RAG (vectorstore pas
    fourni pour ce run) ; permet aux agents d'accepter ce paramètre en
    option sans casser la rétrocompatibilité (défaut None partout où il
    est ajouté à la signature d'un agent).

    Note : `score_min`/`n_candidats` ne sont plus des paramètres de cette
    fonction -- ils sont lus depuis `app.config.rag_settings`
    (MIN_SCORE/MAX_RESULTS), plus aucune valeur de seuil codée en dur ici.
    """
    if valeur_actuelle:
        logger.info("decision=ignore client=%s champ=%s raison=champ_deja_resolu", client, champ_manquant)
        return

    if not rag_settings.ENABLE_RAG:
        # Court-circuit AVANT le retrieval : inutile d'interroger le
        # vectorstore si la fonctionnalité est globalement désactivée.
        # rag_decision_service revérifie ENABLE_RAG en défense en
        # profondeur (cf. son propre docstring), mais autant éviter le
        # coût d'un appel retrieval qu'on sait déjà voué à être ignoré.
        logger.info("decision=ignore client=%s champ=%s raison=rag_desactive_par_configuration", client, champ_manquant)
        return

    if dossier_persistance is None:
        logger.info("decision=ignore client=%s champ=%s raison=vectorstore_non_fourni", client, champ_manquant)
        return

    resultat = tenter_fallback_rag(
        client, question, dossier_persistance,
        embed_fn=embed_fn, n_candidats=rag_settings.MAX_RESULTS, score_min=rag_settings.MIN_SCORE,
    )
    decision = evaluer_resultat(resultat)

    if not decision.usable:
        logger.info(
            "decision=ignore client=%s champ=%s query=%r raison=%s",
            client, champ_manquant, question, decision.reason,
        )
        return

    # decision.result est garanti non-None et entièrement renseigné ici
    # (contrat de RagDecision.usable=True, cf. rag_decision_service).
    resultat_valide = decision.result
    logger.info(
        "decision=utilise client=%s champ=%s query=%r source=%s score=%.4f chunk_id=%s",
        client, champ_manquant, question, resultat_valide.source, resultat_valide.score, resultat_valide.chunk_id,
    )

    apercu = resultat_valide.value[:200] + ("…" if len(resultat_valide.value) > 200 else "")
    note = (
        f"🔎 Suggestion RAG pour '{champ_manquant}' (NON APPLIQUÉE AU CHAMP, à vérifier "
        f"et reporter manuellement si pertinent) — source : {resultat_valide.source} "
        f"(score={resultat_valide.score:.2f}) : {apercu}"
    )
    ticket.intervention.commentaire_interne = _ajouter_si_absent(ticket.intervention.commentaire_interne, note)