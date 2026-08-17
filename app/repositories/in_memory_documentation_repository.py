"""
app/repositories/in_memory_documentation_repository.py

Première implémentation concrète de DocumentationRepository (WF-DOC-014).
Stockage strictement en mémoire (dict Python) -- aucune base de données,
aucun fichier, aucune dépendance externe. Les données sont injectées au
constructeur, jamais codées en dur dans la classe.
"""

from app.repositories.documentation_repository import DocumentationRepository


class InMemoryDocumentationRepository(DocumentationRepository):
    """
    Implémentation en mémoire de DocumentationRepository.

    Structure interne : `{client: {question_normalisee: reponse}}` --
    même convention de normalisation (minuscule, trim) que
    StaticDocumentationProvider, pour une correspondance robuste aux
    variations mineures de casse/espaces. Isolation stricte par client :
    aucune donnée n'est jamais partagée entre clients.
    """

    def __init__(self, donnees: dict[str, dict[str, str]] | None = None):
        """`donnees` (optionnel) : jeu de données initial injecté, `{client: {question: reponse}}`. Vide par défaut."""
        self._donnees: dict[str, dict[str, str]] = {
            client: dict(questions) for client, questions in (donnees or {}).items()
        }

    def save(self, entity):
        """
        Non exploité par cette implémentation (aucun besoin concret
        démontré pour l'écriture dynamique à ce stade, cf. gouvernance
        "aucune abstraction anticipée") -- présent uniquement pour
        respecter le contrat BaseRepository.
        """
        pass

    def get_by_id(self, entity_id):
        """Non exploité (DocumentationWorkflow ne travaille jamais par identifiant, cf. DocumentationRepository)."""
        return None

    def find_by_question(self, client: str, question: str) -> str | None:
        """Correspondance exacte (client, question normalisée) -> réponse, ou None si absente."""
        questions_du_client = self._donnees.get(client, {})
        return questions_du_client.get(_normaliser(question))


def _normaliser(question: str) -> str:
    """Normalise une question pour la correspondance (minuscule, trim) -- même convention que StaticDocumentationProvider."""
    return (question or "").strip().lower()