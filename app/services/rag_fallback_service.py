"""
Service RAG -- couche PUREMENT CONSULTATIVE (architecture validée avec Sofiane).

Ce module ne connaît NI la classe Ticket, NI aucun agent, NI aucune règle
métier. Il reçoit une requête textuelle et retourne un unique objet typé
`RagResult` -- jamais autre chose, jamais d'effet de bord, jamais
d'exception.

Contrat strict de `RagResult` :
- found=True  => value, source, score, chunk_id sont TOUS renseignés
                 (aucun champ manquant sur un résultat positif).
- found=False => value=None, source=None, score=None, chunk_id=None
                 (aucune valeur partielle qui pourrait laisser croire à
                 une information fiable là où il n'y en a pas).

Sélection : interroge le vectorstore du client pour plusieurs candidats
(`n_candidats`), puis ne retient QUE le meilleur score parmi eux.
found=False si même ce meilleur candidat n'atteint pas `score_min` --
jamais de repli sur un candidat "moins pire" hors seuil.

Score : transformation monotone décroissante de la distance ChromaDB,
score = 1 / (1 + distance) ∈ (0, 1]. Plus la distance est faible (chunk
proche), plus le score est élevé.

⚠️ La valeur ABSOLUE du score dépend de l'espace d'embedding utilisé
   (TF-IDF de test vs. Gemini de production ne sont PAS comparables terme
   à terme -- vocabulaires/dimensions différents) -- seul l'ORDRE relatif
   au sein d'un même espace est garanti significatif. `score_min` par
   défaut (0.0, aucun filtrage) est donc volontairement permissif : à
   recalibrer empiriquement une fois des requêtes réelles Gemini
   disponibles (constituer un jeu de questions/réponses connu, cf. skill
   iris-copilot-rag-and-agent-architecture : "gold Q&A set derived from
   SKILL.md's own content"). En attendant, les tests pilotent `score_min`
   explicitement plutôt que de dépendre d'un défaut non calibré.

Logging : ce module logge le niveau RETRIEVAL (requête, candidats
considérés, meilleur score, décision seuil). Le niveau DÉCISION MÉTIER
(utilisé/ignoré + raison métier) est loggé séparément par
`rag_integration_layer.py`, seule couche autorisée à connaître les
modèles métier.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from app.services.vectorstore_service import EmbedFn, embed_texts_gemini, lookup_rule

logger = logging.getLogger("iris_copilot.rag_fallback")


@dataclass
class RagResult:
    """Résultat typé unique retourné par ce module -- jamais autre chose."""
    found: bool
    value: str | None
    source: str | None
    score: float | None
    chunk_id: str | None


_AUCUN_RESULTAT = RagResult(found=False, value=None, source=None, score=None, chunk_id=None)


def _distance_vers_score(distance: float) -> float:
    """Transformation monotone décroissante distance ChromaDB -> score ∈ (0, 1]."""
    return 1.0 / (1.0 + distance)


def tenter_fallback_rag(
    client: str,
    question: str,
    dossier_persistance: Path,
    embed_fn: EmbedFn = embed_texts_gemini,
    n_candidats: int = 3,
    score_min: float = 0.0,
) -> RagResult:
    """
    Interroge le vectorstore du client pour `question`, examine jusqu'à
    `n_candidats` résultats, et retient le MEILLEUR score parmi eux.

    Ne lève jamais d'exception : client sans collection, vectorstore non
    construit, ou meilleur candidat sous `score_min` -> RagResult
    found=False (tous les autres champs à None) dans tous les cas.
    """
    reponse = lookup_rule(client, question, dossier_persistance, embed_fn=embed_fn, n_results=n_candidats)

    if not reponse.chunks:
        logger.info("retrieval client=%s query=%r resultat=aucun_candidat", client, question)
        return _AUCUN_RESULTAT

    candidats = list(zip(reponse.chunks, reponse.sources, reponse.distances, reponse.ids))
    # Le meilleur candidat = la plus petite distance (donc le plus grand score).
    meilleur_texte, meilleure_source, meilleure_distance, meilleur_id = min(candidats, key=lambda c: c[2])

    if not meilleure_source or "type_source" not in meilleure_source or "source" not in meilleure_source:
        # Métadonnée absente/malformée -> impossible de garantir la traçabilité
        # exigée par le contrat (found=True => source renseignée). On dégrade
        # proprement plutôt que de risquer un résultat non sourcé ou un crash.
        logger.warning(
            "retrieval client=%s query=%r resultat=metadata_manquante chunk_id=%s",
            client, question, meilleur_id,
        )
        return _AUCUN_RESULTAT

    meilleur_score = _distance_vers_score(meilleure_distance)

    if meilleur_score < score_min:
        logger.info(
            "retrieval client=%s query=%r meilleur_score=%.4f score_min=%.4f resultat=sous_seuil",
            client, question, meilleur_score, score_min,
        )
        return _AUCUN_RESULTAT

    source_formatee = f"{meilleure_source['type_source']}:{meilleure_source['source']}"
    logger.info(
        "retrieval client=%s query=%r source=%s score=%.4f chunk_id=%s resultat=trouve",
        client, question, source_formatee, meilleur_score, meilleur_id,
    )
    return RagResult(
        found=True,
        value=meilleur_texte,
        source=source_formatee,
        score=meilleur_score,
        chunk_id=meilleur_id,
    )