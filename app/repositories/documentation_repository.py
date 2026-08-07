"""
app/repositories/documentation_repository.py

Contrat spécifique au domaine Documentation, spécialisant BaseRepository
(WF-DOC-002). Reste ABSTRAIT -- aucune implémentation concrète (pas de
ChromaDB, pas de persistance réelle, pas d'appel réseau). Sera implémenté
plus tard par un Repository concret (ex. ChromaDocumentationRepository),
mission future non anticipée ici.
"""

from abc import ABC, abstractmethod

from app.repositories.base_repository import BaseRepository


class DocumentationRepository(BaseRepository[str], ABC):
    """
    Spécialisation de BaseRepository pour le domaine Documentation.

    `save`/`get_by_id` restent hérités tels quels de BaseRepository
    (persistance par identifiant). Une seule méthode abstraite
    supplémentaire est ajoutée :

    `find_by_question` -- seule opération réellement nécessaire au
    Workflow Documentation aujourd'hui. `DocumentationWorkflowRequest`
    (WF-DOC-001) ne porte jamais d'identifiant connu à l'avance,
    uniquement une question en langage naturel -- `get_by_id` seul ne
    peut donc pas servir ce cas d'usage concret. Aucune autre méthode
    de recherche (par mot-clé, par métadonnée, etc.) n'est ajoutée faute
    de besoin démontré -- cf. gouvernance du Framework (P3-440.1) :
    "aucune abstraction anticipée".

    Le type stocké (T=str) reste volontairement le plus simple possible :
    le contenu textuel d'une réponse documentaire. Aucun modèle de
    données plus riche (métadonnées, titre, score...) n'est introduit ici
    faute de besoin concret démontré.
    """

    @abstractmethod
    def find_by_question(self, client: str, question: str) -> str | None:
        """
        Retourne le contenu documentaire le plus pertinent pour
        `question` chez `client`, ou None si rien de pertinent n'est
        trouvé. Isolation stricte par client -- jamais de recherche
        cross-client, cf. conventions déjà établies pour le RAG
        (rag_decision_service.py, vectorstore_service.py).
        """
        raise NotImplementedError