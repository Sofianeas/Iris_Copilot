"""
Couche d'intégration SAFE MODE entre les agents et rag_fallback_service.

Politique stricte (architecture validée avec Sofiane) :
- SEULE cette couche a le droit de connaître les modèles métier (`Ticket`).
  `rag_fallback_service.py` reste purement consultatif -- il ne reçoit
  qu'une requête textuelle, ne connaît ni Ticket ni agent.
- Cette couche ne modifie JAMAIS un champ métier du Ticket, quelle que
  soit la pertinence du résultat RAG.
- Elle enrichit UNIQUEMENT `ticket.intervention.commentaire_interne`,
  toujours sous forme de suggestion explicitement marquée non vérifiée --
  jamais présentée comme une donnée validée.

Logging : ce module logge le niveau DÉCISION MÉTIER (utilisé/ignoré +
raison). Le niveau RETRIEVAL (requête, score, chunk considéré) est déjà
loggé par `rag_fallback_service.py` -- pas de duplication, chaque couche
logge ce qui relève de sa propre responsabilité.
"""

import logging
from pathlib import Path

from app.models.ticket import Ticket
from app.services.rag_fallback_service import RagResult, tenter_fallback_rag
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


def _resultat_est_utilisable(resultat: RagResult) -> tuple[bool, str]:
    """
    Décision d'usage, au-delà du seuil déjà appliqué par rag_fallback_service.

    Vérifie DÉFENSIVEMENT l'invariant du contrat RagResult -- ne fait
    jamais confiance aveuglément, même à notre propre service : un
    résultat found=True mais avec value/source manquants est rejeté ici
    plutôt que propagé vers le ticket. Retourne (utilisable, raison).
    """
    if not resultat.found:
        return False, "aucun résultat suffisamment pertinent (found=False)"
    if not resultat.value:
        return False, "found=True mais value vide -- rejeté par sécurité (contrat RagResult violé)"
    if not resultat.source:
        return False, "found=True mais source manquante -- aucune suggestion sans source acceptée"
    return True, "résultat valide et sourcé"


def enrichir_commentaire_si_pertinent(
    ticket: Ticket,
    champ_manquant: str,
    valeur_actuelle: str,
    client: str,
    question: str,
    dossier_persistance: Path | None,
    embed_fn: EmbedFn = embed_texts_gemini,
    score_min: float = 0.0,
) -> None:
    """
    Point d'entrée unique que les agents doivent utiliser (jamais
    `rag_fallback_service.tenter_fallback_rag` directement depuis un agent).

    Ne modifie JAMAIS un champ métier -- enrichit uniquement
    `commentaire_interne`, et seulement si (a) `valeur_actuelle` est vide
    ET (b) un résultat RAG utilisable existe. Ne lève jamais d'exception.

    `dossier_persistance=None` -> aucune tentative RAG (vectorstore pas
    fourni pour ce run) ; permet aux agents d'accepter ce paramètre en
    option sans casser la rétrocompatibilité (défaut None partout où il
    est ajouté à la signature d'un agent).
    """
    if valeur_actuelle:
        logger.info("decision=ignore client=%s champ=%s raison=champ_deja_resolu", client, champ_manquant)
        return

    if dossier_persistance is None:
        logger.info("decision=ignore client=%s champ=%s raison=vectorstore_non_fourni", client, champ_manquant)
        return

    resultat = tenter_fallback_rag(client, question, dossier_persistance, embed_fn=embed_fn, score_min=score_min)
    utilisable, raison = _resultat_est_utilisable(resultat)

    if not utilisable:
        logger.info(
            "decision=ignore client=%s champ=%s query=%r raison=%s",
            client, champ_manquant, question, raison,
        )
        return

    logger.info(
        "decision=utilise client=%s champ=%s query=%r source=%s score=%.4f chunk_id=%s",
        client, champ_manquant, question, resultat.source, resultat.score, resultat.chunk_id,
    )

    apercu = resultat.value[:200] + ("…" if len(resultat.value) > 200 else "")
    note = (
        f"🔎 Suggestion RAG pour '{champ_manquant}' (NON APPLIQUÉE AU CHAMP, à vérifier "
        f"et reporter manuellement si pertinent) — source : {resultat.source} "
        f"(score={resultat.score:.2f}) : {apercu}"
    )
    ticket.intervention.commentaire_interne = _ajouter_si_absent(ticket.intervention.commentaire_interne, note)