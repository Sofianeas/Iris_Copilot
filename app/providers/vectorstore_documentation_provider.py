"""
app/providers/vectorstore_documentation_provider.py

Provider concret adaptant vectorstore_service.lookup_rule() (ChromaDB,
déjà existant, NON MODIFIÉ) au contrat DocumentationProvider.fetch()
(WF-DOC-011). Aucune nouvelle infrastructure -- réutilise exclusivement
le vectorstore RAG déjà construit et testé (WF-DOC-010).

N'implémente AUCUNE logique de retrieval elle-même -- délègue
entièrement à lookup_rule(), qui gère déjà l'isolation stricte par client
(une collection ChromaDB par client, jamais de recherche cross-client).

⚠️ LIMITATION CONNUE, IMPORTANTE : `lookup_rule` ne filtre JAMAIS par
pertinence -- elle retourne toujours les N chunks les plus proches par
distance vectorielle, même si aucun n'est réellement pertinent pour la
question posée. Ce Provider hérite donc de cette limitation : `fetch()`
retourne un `None` UNIQUEMENT si le client n'a aucune collection ChromaDB
(jamais ingéré), PAS si la question est simplement sans rapport avec le
contenu indexé -- dans ce dernier cas, il retournera quand même le chunk
le "moins éloigné", même peu pertinent, SAUF si `distance_max` est fourni
(WF-DOC-013, cf. constructeur).
"""

from pathlib import Path

from app.providers.documentation_provider import DocumentationProvider, DocumentationQuery
from app.services.vectorstore_service import EmbedFn, embed_texts_gemini, lookup_rule


class VectorStoreDocumentationProvider(DocumentationProvider):
    """
    Adapte vectorstore_service.lookup_rule() au contrat DocumentationProvider.

    `fetch()` retourne le chunk le plus proche (1er résultat, déjà trié
    par ChromaDB), ou None si le client n'a aucune collection, ou si
    `distance_max` est dépassé (WF-DOC-013).
    """

    def __init__(
        self,
        dossier_persistance: Path,
        embed_fn: EmbedFn = embed_texts_gemini,
        n_results: int = 3,
        distance_max: float | None = None,
    ):
        """
        `dossier_persistance` : chemin du vectorstore ChromaDB déjà
        construit (via `vectorstore_service.construire_vectorstore`).
        `embed_fn` : DOIT être la même fonction (ou le même embedder
        TF-IDF ajusté) que celle utilisée lors de la construction du
        vectorstore -- cf. avertissement déjà documenté dans
        vectorstore_service.make_tfidf_embedder.
        `distance_max` (WF-DOC-013, optionnel, défaut None) : si fourni,
        `fetch()` retourne None quand la distance du meilleur chunk
        dépasse ce seuil (chunk jugé non pertinent) -- s'appuie
        exclusivement sur `ReponseRetrievee.distances`, déjà retourné par
        `lookup_rule()` (contrat existant, non modifié). Aucune
        dépendance à `rag_settings` (décision WF-DOC-013 : `distance_max`
        conservé tel quel, non remplacé par `score_min`/`MIN_SCORE`).
        Défaut `None` = comportement strictement inchangé par rapport à
        WF-DOC-011/012.
        """
        self._dossier_persistance = dossier_persistance
        self._embed_fn = embed_fn
        self._n_results = n_results
        self._distance_max = distance_max

    def fetch(self, request: DocumentationQuery) -> str | None:
        client, question = request
        reponse = lookup_rule(
            client=client,
            question=question,
            dossier_persistance=self._dossier_persistance,
            embed_fn=self._embed_fn,
            n_results=self._n_results,
        )
        if not reponse.chunks:
            return None
        if self._distance_max is not None and reponse.distances and reponse.distances[0] > self._distance_max:
            return None
        return reponse.chunks[0]