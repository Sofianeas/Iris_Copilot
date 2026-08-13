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
le "moins éloigné", même peu pertinent. Un filtrage par score/distance
(ex. réutilisation de `app.config.rag_settings.MIN_SCORE`) est un
raffinement volontairement différé, non traité dans cette mission.
"""

from pathlib import Path

from app.providers.documentation_provider import DocumentationProvider, DocumentationQuery
from app.services.vectorstore_service import EmbedFn, embed_texts_gemini, lookup_rule


class VectorStoreDocumentationProvider(DocumentationProvider):
    """
    Adapte vectorstore_service.lookup_rule() au contrat DocumentationProvider.

    `fetch()` retourne le chunk le plus proche (1er résultat, déjà trié
    par ChromaDB), ou None uniquement si le client n'a aucune collection
    (cf. avertissement du docstring du module pour la limitation sur les
    questions sans rapport).
    """

    def __init__(
        self,
        dossier_persistance: Path,
        embed_fn: EmbedFn = embed_texts_gemini,
        n_results: int = 3,
    ):
        """
        `dossier_persistance` : chemin du vectorstore ChromaDB déjà
        construit (via `vectorstore_service.construire_vectorstore`).
        `embed_fn` : DOIT être la même fonction (ou le même embedder
        TF-IDF ajusté) que celle utilisée lors de la construction du
        vectorstore -- cf. avertissement déjà documenté dans
        vectorstore_service.make_tfidf_embedder.
        """
        self._dossier_persistance = dossier_persistance
        self._embed_fn = embed_fn
        self._n_results = n_results

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
        return reponse.chunks[0]